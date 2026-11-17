import argparse
from contextlib import ExitStack
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
import rpc_bench
import time

spec = importlib.util.spec_from_file_location("probe_gnet", Path(__file__).with_name("probe-gnet.py"))
gnet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gnet)

SQL_IP = "198.18.108.2"
GAME_IP = "198.18.108.1"
LINKS = {
    **gnet.ENDPOINTS,
    "gdeliveryd": (
        ("GDeliveryServer", "delivery.sock", 29100),
        ("GProviderServer", "provider.sock", 29300),
        ("GameDBClient", "wdb.sock", 29400),
        ("UniqueNameClient", "names.sock", 29401),
        ("LogclientTcpClient", "log.sock", 11101),
    ),
    "glinkd": (
        ("GDeliveryClient", "delivery.sock", 29100),
        ("GProviderServer1", "link.sock", 29301),
        ("LogclientTcpClient", "log.sock", 11101),
    ),
    "gs": (
        ("GProviderClient0", "provider.sock", 29300),
        ("GProviderClient2", "link.sock", 29301),
        ("GamedbClient", "wdb.sock", 29400),
        ("LogclientTcpClient", "log.sock", 11101),
    ),
}


def run(arguments, *, input_data=None, timeout=12, check=True):
    return subprocess.run(
        [str(arg) for arg in arguments], input=input_data, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=check, timeout=timeout,
    )


def start_process(stack, arguments, cwd, log_path):
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            [str(arg) for arg in arguments], cwd=cwd, stdout=log, stderr=log,
            start_new_session=True,
        )
    stack.callback(gnet.stop, process)
    return process


def observe(predicate, seconds, interval=0.05):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def verify_private_network():
    addresses = json.loads(run(["ip", "-j", "address"]).stdout)
    if {entry["ifname"] for entry in addresses} != {"lo"}:
        raise RuntimeError("start the probe in a private network namespace with only loopback")
    if subprocess.run(["mountpoint", "-q", "/home"], check=False).returncode != 0:
        raise RuntimeError("mount a private /home with the original license file before probing")


def prepare_sql_namespace(stack, directory):
    holder = start_process(stack, ["unshare", "--net", "--ipc", "sleep", "600"],
                           directory, directory / "namespace.log")
    initial = os.readlink("/proc/self/ns/net")
    target = Path(f"/proc/{holder.pid}/ns/net")
    if not observe(lambda: holder.poll() is None and os.readlink(target) != initial, 2):
        raise RuntimeError("separate SQL network namespace did not initialize")
    prefix = ["nsenter", "--target", str(holder.pid), "--net", "--ipc", "--"]
    run(["ip", "link", "add", "pwgame", "type", "veth", "peer", "name", "pwsql"])
    run(["ip", "link", "set", "pwsql", "netns", holder.pid])
    run(["ip", "addr", "add", f"{GAME_IP}/30", "dev", "pwgame"])
    run(["ip", "link", "set", "pwgame", "up"])
    run([*prefix, "ip", "link", "set", "lo", "up"])
    run([*prefix, "ip", "addr", "add", f"{SQL_IP}/30", "dev", "pwsql"])
    run([*prefix, "ip", "link", "set", "pwsql", "up"])
    return prefix


def start_sql(stack, directory, fixture, tools):
    prefix = prepare_sql_namespace(stack, directory)
    basedir = tools / "usr"
    datadir = directory / "sql-data"
    socket = directory / "sql.sock"
    initialize = [basedir / "bin/mariadb-install-db", "--no-defaults",
                  f"--basedir={basedir}", f"--datadir={datadir}", "--user=root",
                  "--auth-root-authentication-method=normal", "--skip-test-db",
                  "--skip-name-resolve"]
    setup = run(initialize, check=False, timeout=35)
    if setup.returncode != 0:
        (directory / "sql-install.log").write_bytes(setup.stdout + setup.stderr)
        raise RuntimeError("temporary MariaDB initialization failed: "
                           + (setup.stderr or setup.stdout).decode(errors="replace")[-1300:])
    server = [*prefix, basedir / "sbin/mariadbd", "--no-defaults", "--user=root",
              f"--basedir={basedir}", f"--datadir={datadir}", f"--socket={socket}",
              f"--pid-file={directory / 'sql.pid'}", f"--bind-address={SQL_IP}",
              "--port=3306", "--skip-name-resolve", "--innodb-buffer-pool-size=64M"]
    sql = start_process(stack, server, directory, directory / "sql.log")
    client = [*prefix, str(basedir / "bin/mariadb"), "--no-defaults",
              f"--socket={socket}", "-uroot", "-NB"]
    database_ready = lambda: socket.exists() and run(
        [*client, "-e", "SELECT 1"], check=False, timeout=3
    ).returncode == 0
    if not observe(database_ready, 10):
        raise RuntimeError("temporary MariaDB did not accept SQL: "
                           + (directory / "sql.log").read_text(errors="replace")[-1000:])
    password = secrets.token_hex(12)
    run(client, input_data=b"CREATE DATABASE IF NOT EXISTS licenseservice;\n")
    run([*client, "licenseservice"], input_data=(fixture / "root/sql/licenseservice.sql").read_bytes())
    run(client, input_data=(
        f"CREATE USER 'pw_ipc'@'{GAME_IP}' IDENTIFIED BY '{password}';"
        f"GRANT ALL ON licenseservice.* TO 'pw_ipc'@'{GAME_IP}';"
    ).encode())
    return sql, client, password


def start_license(stack, directory, assets, password):
    cwd = directory / "licenseservice"
    shutil.copytree(assets / cwd.name, cwd)
    binary = cwd / cwd.name
    binary.chmod(0o700)
    config = cwd / "gamesys.conf"
    gnet.configure(config, "GMysqlClient", {"address": SQL_IP, "port": "3306",
                                          "user": "pw_ipc", "passwd": password,
                                          "name": "licenseservice"})
    process = start_process(stack, [binary, config.name], cwd, cwd / "probe.log")
    if not observe(lambda: gnet.connect_to("tcp", directory, "", 33000), 8):
        raise RuntimeError(f"stock licenseservice did not listen on 33000, exit={process.poll()}")
    return process


def configure_links(service, config, socket_dir, mode):
    for section, name, port in LINKS[service]:
        address = "127.0.0.1" if mode == "tcp" else str(socket_dir / name)
        gnet.configure(config, section, {"type": mode, "address": address, "port": str(port)})


def start_service(stack, service, directory, assets, wdb, mode, cpu=None):
    source = wdb if service in {"uniquenamed", "gamedbd", "gdeliveryd"} else assets
    cwd = directory / service
    shutil.copytree(source / service, cwd)
    binary = cwd / service
    binary.chmod(0o700)
    config = cwd / ("logservice.conf" if service == "logservice" else "gamesys.conf")
    configure_links(service, config, directory, mode)
    arguments = [binary, config.name]
    if cpu is not None:
        arguments = ["taskset", "--cpu-list", str(cpu), *arguments]
    if service == "glinkd":
        arguments.append("1")
    return start_process(stack, arguments, cwd, cwd / "probe.log")


def measure_map(stack, directory, mode, gs_sample, map_assets, seconds):
    cwd = directory / "gamed"
    shutil.copytree(gs_sample, cwd)
    shutil.copytree(map_assets, cwd, dirs_exist_ok=True)
    binary = cwd / "gs"
    binary.chmod(0o700)
    configure_links("gs", cwd / "gmserver.conf", directory, mode)
    config = cwd / "gs.conf"
    data = config.read_bytes()
    config.write_bytes(data.replace(b"/tmp/gssock_", str(directory / "gs-").encode()))
    stdout = cwd / "probe.log"
    start = time.monotonic()
    process = start_process(stack, [binary, "is61", "gs.conf", "gmserver.conf", "gsalias.conf"], cwd, stdout)
    trace = directory / "logs/world2.trace"
    registration = re.compile(rb"gameserver\s+101\b[^\r\n]*worldtag\D*161\b", re.I)
    state = {"pid": process.pid}

    def read_registration():
        if process.poll() is not None:
            return True
        if "first_gs_listener_s" not in state and (directory / "gs-is61").is_socket():
            state["first_gs_listener_s"] = round(time.monotonic() - start, 3)
        if trace.is_file() and registration.search(trace.read_bytes()):
            state["registration_s"] = round(time.monotonic() - start, 3)
            return True
        return False

    observe(read_registration, seconds, interval=0.1)
    state["exit"] = process.poll()
    state["elapsed_s"] = round(time.monotonic() - start, 3)
    state["socket_state"] = gnet.connections({"gs": process})
    state["stdout_bytes"] = stdout.stat().st_size
    state["stdout_tail"] = diagnostic_tail(stdout)
    if trace.is_file():
        state["registration_lines"] = [
            line[:200] for line in trace.read_text(errors="replace").splitlines()
            if re.search(r"gameserver\s+101|Add dispatcher", line, re.I)
        ][-5:]
    proc = Path(f"/proc/{process.pid}")
    for filename in ("io", "status"):
        path = proc / filename
        if process.poll() is None and path.is_file():
            state[filename] = [
                line for line in path.read_text().splitlines()
                if re.match(r"rchar|wchar|read_bytes|write_bytes|VmRSS|VmHWM", line)
            ]
    return state


def diagnostic_tail(path):
    with path.open("rb") as log:
        log.seek(max(0, path.stat().st_size - 12000))
        stream = log.read()
    return [
        line[:140] for line in stream[-12000:].decode(errors="replace").splitlines()
        if re.search(r"missing|can't|cannot|error|failed|fatal|startup|storage|create|successful", line, re.I)
        and not re.search(r"passwd|password|token|secret|userkey|sql|sql_client|license|login", line, re.I)
    ][-8:]


def probe_mode(args, lab, mode, index):
    directory = lab / f"{mode}{index}"
    (directory / "logs").mkdir(parents=True)
    with ExitStack() as stack:
        processes = {}
        for service in ("logservice", "uniquenamed", "gamedbd", "gdeliveryd", "glinkd"):
            cpu = args.rpc_cpus[1] if args.rpc_count and service == "gamedbd" else None
            process = start_service(stack, service, directory, args.assets, args.wdb, mode, cpu)
            processes[service] = process
            _, name, port = LINKS[service][0]
            observe(lambda: process.poll() is not None or
                    gnet.connect_to(mode, directory, name, port), 5)
        time.sleep(1)
        result = {
            "exit": {service: proc.poll() for service, proc in processes.items()},
            "sockets": gnet.connections(processes),
            "diagnostics": {
                service: diagnostic_tail(directory / service / "probe.log")
                for service in processes
            },
        }
        print(mode, result["exit"], flush=True)
        if args.rpc_count:
            original_affinity = os.sched_getaffinity(0)
            try:
                os.sched_setaffinity(0, {args.rpc_cpus[0]})
                result["rpc"] = rpc_bench.benchmark(mode, directory, args.rpc_count, args.rpc_role)
            finally:
                os.sched_setaffinity(0, original_affinity)
            result["rpc"]["cpus"] = args.rpc_cpus
            print(mode, "rpc", result["rpc"], flush=True)
        if args.map_seconds > 0 and all(result["exit"][name] is None
                                        for name in ("gdeliveryd", "gamedbd", "glinkd")):
            result["map"] = measure_map(stack, directory, mode, args.gs,
                                        args.fixture / "root/pwserver/gamed", args.map_seconds)
            print(mode, "map", {key: result["map"].get(key) for key in (
                "elapsed_s", "registration_s", "exit", "stdout_bytes",
            )}, flush=True)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--wdb", type=Path, required=True)
    parser.add_argument("--gs", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--modes", nargs="+", choices=("tcp", "unix"), default=["tcp", "unix"])
    parser.add_argument("--map-seconds", type=int, default=0)
    parser.add_argument("--rpc-count", type=int, default=0)
    parser.add_argument("--rpc-role", type=int, default=16)
    parser.add_argument("--rpc-cpus", nargs=2, type=int, default=[2, 3])
    args = parser.parse_args()
    if args.rpc_count < 0 or args.map_seconds < 0:
        parser.error("request count and timeout must be nonnegative")
    if not 0 <= args.rpc_role <= 0xFFFFFFFF:
        parser.error("RPC role id must fit uint32")
    if args.rpc_count and not set(args.rpc_cpus) <= os.sched_getaffinity(0):
        parser.error("RPC CPUs must be available in the current affinity mask")
    verify_private_network()
    with tempfile.TemporaryDirectory(prefix="pw-ipc-stack-") as directory, ExitStack() as stack:
        lab = Path(directory)
        license_root = lab / "license"
        license_root.mkdir()
        sql, client, password = start_sql(stack, license_root, args.fixture, args.tools)
        license_server = start_license(stack, license_root, args.assets, password)
        result = {"sql_pid": sql.pid, "license_pid": license_server.pid, "modes": {}}
        for index, mode in enumerate(args.modes, 1):
            result["modes"][f"{mode}{index}"] = probe_mode(args, lab, mode, index)
            sql_sessions = run([*client, "-e",
                               "SELECT HOST,DB FROM INFORMATION_SCHEMA.PROCESSLIST WHERE USER='pw_ipc'"]
                               ).stdout.decode().splitlines()
            result["sql_sessions"] = sql_sessions
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print("license SQL sessions", result.get("sql_sessions"), flush=True)
