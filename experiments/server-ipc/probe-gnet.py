import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time

SERVICES = ("logservice", "uniquenamed", "gamedbd")
ENDPOINTS = {
    "logservice": (("LogserviceTcpServer", "log.sock", 11101),),
    "uniquenamed": (("UniqueNameServer", "names.sock", 29401),
                   ("LogclientTcpClient", "log.sock", 11101)),
    "gamedbd": (("GameDBServer", "wdb.sock", 29400),
                ("LogclientTcpClient", "log.sock", 11101)),
}


def configure(path, section, values):
    data = path.read_bytes()
    pattern = rb"(?im)(^\[" + section.encode() + rb"\][^\r\n]*\r?\n)(.*?)(?=^\[|\Z)"
    match = re.search(pattern, data, re.DOTALL)
    if not match:
        raise RuntimeError(f"missing {path.name} [{section}]")
    settings = match[2]
    for key, value in values.items():
        key_pattern = rb"(?im)^([ \t]*" + key.encode() + rb"[ \t]*=[ \t]*)[^\r\n]*"
        settings, count = re.subn(key_pattern, lambda entry: entry[1] + value.encode(), settings)
        if count != 1:
            raise RuntimeError(f"expected one {path.name} [{section}] {key}")
    path.write_bytes(data[:match.start(2)] + settings + data[match.end(2):])


def start(service, directory, assets, wdb, transport):
    fixture = assets if service == "logservice" else wdb
    cwd = directory / service
    shutil.copytree(fixture / service, cwd)
    config = cwd / ("logservice.conf" if service == "logservice" else "gamesys.conf")
    binary = cwd / service
    binary.chmod(0o700)
    for section, sockname, port in ENDPOINTS[service]:
        address = str(directory / sockname) if transport != "tcp" else "127.0.0.1"
        configure(config, section, {"type": transport, "address": address, "port": str(port)})
    with (cwd / "probe-stdout.log").open("wb") as log:
        process = subprocess.Popen(
            [str(binary), config.name], cwd=cwd, stdout=log, stderr=log,
            start_new_session=True,
        )
    return process, cwd


def connections(processes):
    rows = {}
    for label, flags in (("tcp_listeners", "-Hltnp"), ("unix_listeners", "-Hlxnp"),
                         ("tcp_established", "-Htnp"), ("unix_established", "-Hxnpa")):
        output = subprocess.run(["ss", flags], check=True, text=True, capture_output=True)
        rows[label] = [
            line.strip()
            for line in output.stdout.splitlines()
            if any(f"pid={process.pid}," in line for process in processes.values())
            and (label != "unix_established" or "ESTAB" in line)
        ]
    return rows


def connect_to(transport, directory, sockname, port):
    if transport == "shm":
        return None
    endpoint = ("127.0.0.1", port) if transport == "tcp" else str(directory / sockname)
    family = socket.AF_INET if transport == "tcp" else socket.AF_UNIX
    with socket.socket(family, socket.SOCK_STREAM) as client:
        client.settimeout(0.2)
        try:
            client.connect(endpoint)
        except OSError:
            return False
    return True


def stop(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def probe(directory, assets, wdb, transport):
    (directory / "logs").mkdir(parents=True)
    processes = {}
    paths = {}
    try:
        for service in SERVICES:
            processes[service], paths[service] = start(service, directory, assets, wdb, transport)
            if service == "logservice":
                deadline = time.monotonic() + 3
                while processes[service].poll() is None and time.monotonic() < deadline:
                    if connect_to(transport, directory, "log.sock", 11101):
                        break
                    if transport == "shm":
                        break
                    time.sleep(0.05)

        time.sleep(2.0)
        state = connections(processes)
        native_files = {}
        for path in (directory / "logs").iterdir():
            if path.is_file():
                native_files[path.name] = path.stat().st_size
        return {
            "pid": {service: proc.pid for service, proc in processes.items()},
            "exit": {service: proc.poll() for service, proc in processes.items()},
            "connect": {
                service: connect_to(transport, directory, ENDPOINTS[service][0][1],
                                    ENDPOINTS[service][0][2])
                for service in SERVICES
            },
            "sockets": state,
            "native_log_bytes": native_files,
            "stdout": {
                service: [
                    line[:140] for line in (path / "probe-stdout.log").read_text(
                        encoding="utf-8", errors="replace",
                    ).splitlines()
                    if re.search(r"storage|error|fatal|signal|bind|listen|init|failed|^usage|exec", line, re.I)
                    and not re.search(r"passwd|password|token|secret|userkey|license|login", line, re.I)
                ][:12]
                for service, path in paths.items()
            },
            "shm_maps": {
                service: [
                    line.rsplit(maxsplit=1)[-1] for line in (Path("/proc") / str(proc.pid) / "maps")
                    .read_text().splitlines()
                    if "/dev/shm/" in line or "SYSV" in line or "memfd:" in line
                ]
                for service, proc in processes.items() if proc.poll() is None
            },
        }
    finally:
        for process in reversed(processes.values()):
            stop(process)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--wdb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    addr = subprocess.run(["ip", "-j", "address"], check=True, text=True, capture_output=True)
    interfaces = {entry["ifname"] for entry in json.loads(addr.stdout)}
    if interfaces != {"lo"} or "127.0.0.1" not in addr.stdout:
        parser.error("requires an isolated network namespace with active loopback only")
    results = {
        "sha256": {
            service: hashlib.file_digest(
                ((args.assets if service == "logservice" else args.wdb) / service / service).open("rb"),
                "sha256",
            ).hexdigest()
            for service in SERVICES
        }
    }
    with tempfile.TemporaryDirectory(prefix="pw-gnet-ipc-") as tmp:
        for mode in ("tcp", "unix", "shm"):
            results[mode] = probe(Path(tmp) / mode, args.assets, args.wdb, mode)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for mode in ("tcp", "unix", "shm"):
        data = results[mode]
        print(mode, "exit", data["exit"], "connect", data["connect"])
        for label, rows in data["sockets"].items():
            for row in rows:
                print(label, row)
        print("native logs", data["native_log_bytes"])
