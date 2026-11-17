import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

ROOT = Path("/root/pwserver")
LAB = Path("/root/pw-ipc-client-lab")
SOCKETS = Path("/run/pw-ipc-test")
SERVICES = ("logservice", "uniquenamed", "gamedbd", "gauthd", "gacd",
            "gfactiond", "gdeliveryd", "glinkd")
PORTS = {11101: "log", 29100: "delivery", 29200: "auth",
         29300: "provider", 29400: "gamedbd", 29401: "names",
         29500: "faction", 29600: "faction-provider", 29702: "anticheat"}
PORTS.update({29300 + index: f"link{index}" for index in range(1, 9)})


def command(*args):
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout


def snapshot():
    records = []
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():
            continue
        try:
            name = (directory / "comm").read_text().strip()
            if name not in {*SERVICES, "gs", "licenseservice", "python3"}:
                continue
            args = [arg.decode() for arg in (directory / "cmdline").read_bytes().split(b"\0") if arg]
            if name == "python3" and not any("network-relay.py" in arg for arg in args):
                continue
            pid = int(directory.name)
            records.append({"pid": pid, "pgid": os.getpgid(pid), "name": name, "args": args,
                            "cwd": os.readlink(directory / "cwd")})
        except (OSError, ProcessLookupError):
            continue
    return records


def state(phase, **details):
    data = {"phase": phase, "time": time.time(), **details}
    (LAB / "status.json").write_text(json.dumps(data, indent=2) + "\n")
    print(phase, flush=True)


def config_filename(service):
    return "logservice.conf" if service == "logservice" else "gamesys.conf"


def convert_config(path, destination):
    data = path.read_bytes()
    changes = []

    def convert(section):
        header, body = section[1], section[2]
        current_type = re.search(rb"(?im)^[ \t]*type[ \t]*=[ \t]*(\w+)", body)
        port = re.search(rb"(?im)^[ \t]*port[ \t]*=[ \t]*(\d+)", body)
        if current_type is None or current_type[1].lower() != b"tcp" or port is None:
            return section[0]
        name = PORTS.get(int(port[1]))
        if name is None:
            return section[0]
        address = str(SOCKETS / (name + ".sock")).encode()
        body, count = re.subn(rb"(?im)^([ \t]*type[ \t]*=[ \t]*)[^\r\n]*",
                             lambda row: row[1] + b"unix", body)
        if count != 1:
            raise ValueError(f"ambiguous type in {path}")
        body, count = re.subn(rb"(?im)^([ \t]*address[ \t]*=[ \t]*)[^\r\n]*",
                             lambda row: row[1] + address, body)
        if count != 1:
            raise ValueError(f"ambiguous address in {path}")
        changes.append({"section": header.decode().strip(), "port": int(port[1]),
                        "socket": address.decode()})
        return header + body

    result = re.sub(rb"(?m)(^\[[^\r\n]+\][^\r\n]*\r?\n)([\s\S]*?)(?=^\[|\Z)", convert, data)
    destination.write_bytes(result)
    destination.chmod(0o600)
    return changes


def prepare():
    if LAB.exists():
        raise RuntimeError("lab path already exists")
    if command("ss", "-Hnt", "state", "established", "( sport = :29000 )").strip():
        raise RuntimeError("an active game client is connected")
    records = snapshot()
    for record in records:
        if record["name"] in SERVICES or record["name"] == "gs":
            group = [row for row in records if row["pgid"] == record["pgid"]]
            if record["pgid"] != record["pid"] or len(group) != 1:
                raise RuntimeError(f"unexpected process group for {record['name']}")
    os.umask(0o077)
    LAB.mkdir()
    (LAB / "configs").mkdir()
    (LAB / "logs").mkdir()
    (LAB / "backups").mkdir()
    SOCKETS.mkdir(mode=0o700, exist_ok=True)
    (LAB / "baseline.json").write_text(json.dumps(records, indent=2) + "\n")
    manifests = {}
    for service in SERVICES:
        source = ROOT / service / config_filename(service)
        target = LAB / "configs" / (service + ".conf")
        manifests[service] = convert_config(source, target)
    manifests["gs"] = convert_config(ROOT / "gamed/gmserver.conf", LAB / "configs/gmserver.conf")
    (LAB / "manifest.json").write_text(json.dumps(manifests, indent=2) + "\n")
    state("prepared", changed_sections=sum(len(value) for value in manifests.values()))
    return manifests


def alive(record):
    path = Path(f"/proc/{record['pid']}")
    try:
        args = [arg.decode() for arg in (path / "cmdline").read_bytes().split(b"\0") if arg]
        return args == record["args"] and os.readlink(path / "cwd") == record["cwd"]
    except OSError:
        return False


def wait_stopped(records, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if all(not alive(record) for record in records):
            return
        time.sleep(0.2)
    raise RuntimeError("processes still active: " + repr(
        [(record["name"], record["pid"]) for record in records if alive(record)]))


def terminate(records, signum):
    for record in records:
        if alive(record):
            os.kill(record["pid"], signum)
    wait_stopped(records, 12)


def launch(name, args, cwd):
    with (LAB / "logs" / (name + ".log")).open("wb") as output:
        process = subprocess.Popen(args, cwd=cwd, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=output, start_new_session=True)
    return {"name": name, "pid": process.pid, "pgid": process.pid,
            "args": [str(arg) for arg in args], "cwd": str(cwd)}


def run():
    if command("ss", "-Hnt", "state", "established", "( sport = :29000 )").strip():
        raise RuntimeError("an active game client is connected")
    baseline = json.loads((LAB / "baseline.json").read_text())
    state("stopping_maps")
    terminate([record for record in baseline if record["name"] in {"gs", "python3"}], signal.SIGTERM)
    state("stopping_network_services")
    terminate([record for record in baseline
               if record["name"] in set(SERVICES) - {"logservice", "uniquenamed", "gamedbd"}],
              signal.SIGUSR1)
    storage = [record for record in baseline if record["name"] in {"gamedbd", "uniquenamed"}]
    state("waiting_for_wdb_checkpoint")
    quitfiles = [Path("/tmp/.quitgamedbd"), Path("/tmp/.quituniquenamed")]
    for path in quitfiles:
        if path.exists():
            raise RuntimeError(f"quit file already exists: {path}")
        path.touch()
    wait_stopped(storage, 75)
    for path in quitfiles:
        path.unlink(missing_ok=True)
    state("backing_up_wdb")
    for service in ("gamedbd", "uniquenamed"):
        shutil.copytree(ROOT / service / "dbhome", LAB / "backups" / service)
    terminate([record for record in baseline if record["name"] == "logservice"], signal.SIGUSR1)
    state("starting_unix_services")
    launched = []
    try:
        for service in SERVICES:
            args = [str(ROOT / service / service), str(LAB / "configs" / (service + ".conf"))]
            if service == "glinkd":
                args.append("1")
            launched.append(launch(service, args, ROOT / service))
            (LAB / "launched.json").write_text(json.dumps(launched, indent=2) + "\n")
            time.sleep(0.4)
            if not alive(launched[-1]):
                raise RuntimeError(f"{service} exited during startup")
        state("starting_full_world")
        for alias in ("gs01", "is61"):
            args = [str(ROOT / "gamed/gs"), alias, "gs.conf",
                    str(LAB / "configs/gmserver.conf"), "gsalias.conf"]
            launched.append(launch(alias, args, ROOT / "gamed"))
            (LAB / "launched.json").write_text(json.dumps(launched, indent=2) + "\n")
        state("waiting_for_maps", pids={record["name"]: record["pid"] for record in launched})
    except Exception:
        state("startup_failed")
        raise


def status():
    data = json.loads((LAB / "status.json").read_text())
    if (LAB / "launched.json").exists():
        records = json.loads((LAB / "launched.json").read_text())
        data["processes"] = [{**record, "alive": alive(record)} for record in records]
        pids = {str(record["pid"]) for record in records}
        for label, flags in (("unix", "-Hxnpa"), ("tcp", "-Htnpa")):
            rows = command("ss", flags).splitlines()
            data[label] = [row.strip() for row in rows
                           if any("pid=" + pid + "," in row for pid in pids)]
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "run", "status"))
    options = parser.parse_args()
    if options.action == "prepare":
        print(json.dumps(prepare(), indent=2))
    elif options.action == "run":
        try:
            run()
        except Exception as error:
            state("failed", error=str(error))
            raise
    else:
        print(json.dumps(status(), indent=2))
