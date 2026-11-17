import hashlib
import socket
import statistics
import struct
import time

RPC_ID = 3013


def compact(value):
    if value < 0x80:
        return bytes([value])
    if value < 0x4000:
        return struct.pack("!H", value | 0x8000)
    if value < 0x20000000:
        return struct.pack("!I", value | 0xC0000000)
    return b"\xe0" + struct.pack("!I", value)


def receive_exact(sock, length):
    result = bytearray()
    while len(result) < length:
        chunk = sock.recv(length - len(result))
        if not chunk:
            raise EOFError("GNET peer closed the session")
        result.extend(chunk)
    return bytes(result)


def receive_compact(sock):
    first = receive_exact(sock, 1)[0]
    if first < 0x80:
        return first
    if first < 0xC0:
        return ((first & 0x3F) << 8) | receive_exact(sock, 1)[0]
    if first < 0xE0:
        return int.from_bytes(bytes([first & 0x1F]) + receive_exact(sock, 3), "big")
    return int.from_bytes(receive_exact(sock, 4), "big")


def request(sock, role, xid):
    argument = struct.pack("!II", xid | 0x80000000, role)
    sock.sendall(compact(RPC_ID) + compact(len(argument)) + argument)
    protocol = receive_compact(sock)
    length = receive_compact(sock)
    if protocol != RPC_ID or length < 8 or length > 16384:
        raise ValueError(f"unexpected reply {protocol}, {length}")
    response = receive_exact(sock, length)
    response_xid, retcode = struct.unpack("!Ii", response[:8])
    if response_xid != xid:
        raise ValueError("reply xid mismatch")
    return retcode, response[8:]


def benchmark(mode, directory, count, role):
    family = socket.AF_INET if mode == "tcp" else socket.AF_UNIX
    address = ("127.0.0.1", 29400) if mode == "tcp" else str(directory / "wdb.sock")
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        if mode == "tcp":
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.connect(address)
        retcode, value = request(sock, role, 1)
        selected = role
        if retcode != 0:
            raise ValueError(f"fixture role {role} returned retcode {retcode}")
        reference_hash = hashlib.sha256(value).hexdigest()
        reference_size = len(value)
        samples = []
        for i in range(300 + count):
            started = time.perf_counter_ns()
            rc, current = request(sock, selected, i + 2)
            elapsed = time.perf_counter_ns() - started
            if rc != 0 or len(current) != reference_size:
                raise ValueError("RPC read result changed")
            if i >= 300:
                samples.append(elapsed / 1000)
        if hashlib.sha256(current).hexdigest() != reference_hash:
            raise ValueError("RPC read data changed")
    samples.sort()
    return {
        "operation": "GetRoleBase",
        "protocol": RPC_ID,
        "roleid": selected,
        "retcode": 0,
        "response_value_bytes": reference_size,
        "response_sha256": reference_hash,
        "requests": count,
        "warmup": 300,
        "p50_us": round(statistics.median(samples), 3),
        "p95_us": round(samples[int((count - 1) * 0.95)], 3),
        "p99_us": round(samples[int((count - 1) * 0.99)], 3),
    }
