import asyncio
from pathlib import Path
import struct
from time import time

import map_autoload as loader

RUN = Path(__file__).resolve().parent
loader.MAPS[1] = ("gs02__", 2)
loader.GAME_DIRECTORY = RUN / "target"
MAPS = loader.MapStartup(RUN / "source.log")
ARM = RUN / "arm"
SCREEN = RUN / "screen.pending"
RESUME = RUN / "service.resume"


def selected_command(protocol, payload):
    if protocol != 75 or len(payload) != 23:
        return None
    if int.from_bytes(payload[:4], "big") != 1027 or payload[8] != 14:
        return None
    command, service, length, route = struct.unpack_from("<HIII", payload, 9)
    return command if (service, length, route) == (5, 4, 3) else None


def publish(path, text):
    pending = path.with_suffix(".tmp")
    pending.write_text(text + "\n", encoding="ascii")
    pending.replace(path)


async def serve(source_reader, source_writer):
    tasks = []
    pending = None
    gateway_writer = None

    async def resume(frame, session):
        publish(SCREEN, f"{session} {int(time()) + loader.STARTUP_TIMEOUT + 5}")
        try:
            if not await MAPS.request(1) or loader.read_session(RUN) != session:
                loader.log("Teleport network request expired before native dispatch")
                return
            publish(RESUME, session)
            source_writer.write(frame)
            await source_writer.drain()
            loader.log("Released original teleport network request for role 1027")
        finally:
            SCREEN.unlink(missing_ok=True)

    async def forward(gateway_reader):
        nonlocal pending
        while True:
            protocol, payload, frame = await loader.read_frame(gateway_reader)
            command = selected_command(protocol, payload)
            if command is not None:
                loader.log(f"Teleport network route 2103 command {command} observed")
                if pending is not None and not pending.done():
                    continue
                if ARM.is_file() and ARM.read_text(encoding="ascii").strip() == str(command):
                    session = loader.read_session(RUN)
                    if session and not loader.map_running("gs02__"):
                        ARM.unlink()
                        loader.log("Holding one teleport network request for role 1027")
                        pending = asyncio.create_task(resume(frame, session))
                        continue
            source_writer.write(frame)
            await source_writer.drain()

    try:
        gateway_reader, gateway_writer = await asyncio.open_connection("127.0.0.1", 29301)
        tasks = [
            asyncio.create_task(loader.copy_frames(source_reader, gateway_writer)),
            asyncio.create_task(forward(gateway_reader)),
        ]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except (OSError, ConnectionError) as error:
        loader.log(f"Provider relay ended: {error}")
    finally:
        for task in tasks:
            task.cancel()
        if pending is not None:
            pending.cancel()
            tasks.append(pending)
        await asyncio.gather(*tasks, return_exceptions=True)
        source_writer.close()
        if gateway_writer is not None:
            gateway_writer.close()


async def main():
    server = await asyncio.start_server(serve, "127.0.0.1", 29311)
    loader.log("Teleport network provider relay ready on loopback")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
