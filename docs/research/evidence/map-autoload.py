import asyncio
from datetime import datetime
from pathlib import Path
import re
import struct
import subprocess
from time import monotonic


HOST = "127.0.0.1"
DELIVERY_PORT = 29100
RELAY_PORT = 29110
PROVIDER_PORT = 29301
GAME_DIRECTORY = Path("/root/pwserver/gamed-map-autoload")
DELIVERY_TRACE = Path("/root/pwserver/logs/world2.trace")
LAB_DIRECTORY = Path(__file__).resolve().parent

ROLE_DESTINATIONS = {1026: 161}
MAPS = {161: ("is61", 101)}
PLAYER_LOGIN = 65
STATUS_ANNOUNCE = 6
WAIT_QUEUE_STATE = 164
CANCEL_WAIT_QUEUE = 165
CANCEL_WAIT_QUEUE_REPLY = 166
STATUS_OFFLINE = 0
MAX_FRAME_SIZE = 4 * 1024 * 1024
STARTUP_TIMEOUT = 90
ESTIMATED_STARTUP_SECONDS = 20
WAIT_UPDATE_SECONDS = 60
WORLD_ALLOCATED = re.compile("分配了世界".encode() + rb"\d+ 0x[0-9a-fA-F]+\r?\n")


def log(message):
    print(f"{datetime.now().astimezone().isoformat(timespec='milliseconds')} {message}",
          flush=True)


async def read_compact_uint(reader):
    first = (await reader.readexactly(1))[0]
    if first < 0x80:
        return first, bytes([first])
    if first < 0xC0:
        tail, mask, skip_first = 1, 0x7FFF, False
    elif first < 0xE0:
        tail, mask, skip_first = 3, 0x3FFFFFFF, False
    else:
        tail, mask, skip_first = 4, 0xFFFFFFFF, True
    encoded = bytes([first]) + await reader.readexactly(tail)
    return int.from_bytes(encoded[skip_first:], "big") & mask, encoded


async def read_frame(reader):
    protocol, protocol_bytes = await read_compact_uint(reader)
    size, size_bytes = await read_compact_uint(reader)
    if size > MAX_FRAME_SIZE:
        raise ValueError(f"oversized frame of type {protocol}, {size} bytes")
    payload = await reader.readexactly(size)
    return protocol, payload, protocol_bytes + size_bytes + payload


def write_queue_message(writer, protocol, payload):
    writer.write(struct.pack(">HB", 0x8000 | protocol, len(payload)) + payload)


def gateway_connected(pid):
    output = subprocess.run(
        ["ss", "-Htnp", "state", "established", f"( dport = :{PROVIDER_PORT} )"],
        capture_output=True, text=True, check=True, timeout=3,
    ).stdout
    return f"pid={pid}," in output


class MapStartup:
    def __init__(self):
        self.tasks = {}
        self.processes = {}
        self.estimated_ready_at = {}

    def request(self, world_tag):
        task = self.tasks.get(world_tag)
        process = self.processes.get(world_tag)
        if task is None or (task.done() and (process is None or process.poll() is not None)):
            task = self.tasks[world_tag] = asyncio.create_task(self.start_map(world_tag))
        return task

    def seconds_remaining(self, world_tag):
        return max(1, round(self.estimated_ready_at[world_tag] - monotonic()))

    async def start_map(self, world_tag):
        alias, server_id = MAPS[world_tag]
        started_at = monotonic()
        log(f"map request worldtag={world_tag} alias={alias}")
        try:
            delay = int((LAB_DIRECTORY / "delay-seconds").read_text().strip())
            if not 0 <= delay < STARTUP_TIMEOUT:
                raise ValueError(f"delay must be between 0 and {STARTUP_TIMEOUT - 1} seconds")
            estimate = min(STARTUP_TIMEOUT, delay + ESTIMATED_STARTUP_SECONDS)
            self.estimated_ready_at[world_tag] = started_at + estimate
            if delay:
                await asyncio.sleep(delay)
            log_path = LAB_DIRECTORY / f"{alias}.log"
            with (
                DELIVERY_TRACE.open("rb") as trace,
                log_path.open("ab") as output,
                log_path.open("rb") as map_log,
            ):
                trace.seek(0, 2)
                map_log.seek(0, 2)
                process = self.processes[world_tag] = subprocess.Popen(
                    ["stdbuf", "-oL", "./gs", alias, "gs.conf", "gmserver.conf", "gsalias.conf"],
                    cwd=GAME_DIRECTORY, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
                )
                log(f"map started alias={alias} pid={process.pid} delay={delay}s")
                registration = re.compile(
                    rb"gameserver %d's region .*worldtag is %d\b" % (server_id, world_tag)
                )
                trace_buffer = b""
                map_buffer = b""
                registered_at = None
                instance_allocated = False
                while monotonic() - started_at < STARTUP_TIMEOUT:
                    if process.poll() is not None:
                        raise OSError(f"{alias} exited with status {process.returncode}")
                    if registered_at is None:
                        trace_buffer += trace.read()
                        if registration.search(trace_buffer):
                            registered_at = monotonic()
                            log(f"map registered alias={alias} worldtag={world_tag} "
                                f"elapsed={registered_at - started_at:.2f}s")
                        trace_buffer = trace_buffer[-512:]
                    if not instance_allocated:
                        map_buffer += map_log.read()
                        instance_allocated = WORLD_ALLOCATED.search(map_buffer) is not None
                        if instance_allocated:
                            log(f"map instance allocated alias={alias} worldtag={world_tag} "
                                f"elapsed={monotonic() - started_at:.2f}s")
                        map_buffer = map_buffer[-512:]
                    if (registered_at is not None
                            and instance_allocated
                            and await asyncio.to_thread(gateway_connected, process.pid)):
                        log(f"map ready alias={alias} worldtag={world_tag} pid={process.pid} "
                            f"elapsed={monotonic() - started_at:.2f}s")
                        return True
                    await asyncio.sleep(0.2)
            log(f"map readiness timed out worldtag={world_tag}")
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            log(f"map start failed worldtag={world_tag}: {error}")
        return False


async def copy_frames(reader, writer):
    while True:
        _, _, frame = await read_frame(reader)
        writer.write(frame)
        await writer.drain()


async def handle_gateway(gateway_reader, gateway_writer, maps):
    delivery_writer = None
    delivery_to_gateway = None
    gateway_to_delivery = None
    pending = {}
    try:
        delivery_reader, delivery_writer = await asyncio.open_connection(HOST, DELIVERY_PORT)
        log("gateway delivery channel connected")

        async def continue_login(role_id, session_id, world_tag, frame):
            startup = maps.request(world_tag)
            interval = 0.2
            while not startup.done():
                ready, _ = await asyncio.wait((startup,), timeout=interval)
                if ready:
                    break
                seconds = maps.seconds_remaining(world_tag)
                notice = struct.pack(">IBhhi", session_id, 0, 0, 1, seconds)
                write_queue_message(gateway_writer, WAIT_QUEUE_STATE, notice)
                log(f"wait notice sid={session_id} worldtag={world_tag} eta={seconds}s")
                await gateway_writer.drain()
                interval = WAIT_UPDATE_SECONDS
            log(f"forward login role={role_id} sid={session_id} worldtag={world_tag} "
                f"ready={int(startup.result())}")
            delivery_writer.write(frame)
            pending.pop(session_id)

        async def forward_requests():
            while True:
                protocol, payload, frame = await read_frame(gateway_reader)
                if protocol == PLAYER_LOGIN and len(payload) >= 12:
                    role_id, _, session_id = struct.unpack_from(">iiI", payload)
                    world_tag = ROLE_DESTINATIONS.get(role_id)
                    if world_tag is not None:
                        if session_id not in pending or pending[session_id].done():
                            log(f"received login role={role_id} sid={session_id}")
                            pending[session_id] = asyncio.create_task(
                                continue_login(role_id, session_id, world_tag, frame)
                            )
                        continue
                cancel_wait = protocol == CANCEL_WAIT_QUEUE and len(payload) == 8
                logout = (protocol == STATUS_ANNOUNCE and len(payload) == 9
                          and payload[8] == STATUS_OFFLINE)
                if cancel_wait or logout:
                    session_id = struct.unpack_from(">I", payload, 4)[0]
                    task = pending.pop(session_id, None)
                    if task is not None and not task.done():
                        log(f"cancel login sid={session_id}")
                        task.cancel()
                        if cancel_wait:
                            reply = struct.pack(">iI", 0, session_id)
                            write_queue_message(gateway_writer, CANCEL_WAIT_QUEUE_REPLY, reply)
                            await gateway_writer.drain()
                            continue
                delivery_writer.write(frame)
                await delivery_writer.drain()

        delivery_to_gateway = asyncio.create_task(copy_frames(delivery_reader, gateway_writer))
        gateway_to_delivery = asyncio.create_task(forward_requests())
        closed, _ = await asyncio.wait(
            (delivery_to_gateway, gateway_to_delivery), return_when=asyncio.FIRST_COMPLETED,
        )
        for task in closed:
            task.result()
    except (OSError, ValueError, asyncio.IncompleteReadError) as error:
        if not isinstance(error, asyncio.IncompleteReadError) or error.partial:
            log(f"gateway delivery channel closed: {error}")
    finally:
        tasks = tuple(pending.values()) + tuple(
            task for task in (delivery_to_gateway, gateway_to_delivery) if task is not None
        )
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for writer in (gateway_writer, delivery_writer):
            if writer is not None:
                writer.close()
        log("gateway delivery channel disconnected")


async def main():
    maps = MapStartup()
    server = await asyncio.start_server(
        lambda reader, writer: handle_gateway(reader, writer, maps), HOST, RELAY_PORT
    )
    log(f"listening on {HOST}:{RELAY_PORT}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
