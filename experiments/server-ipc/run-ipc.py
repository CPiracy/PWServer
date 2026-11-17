import argparse
import csv
import itertools
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile

TRANSPORTS = ("tcp", "unix", "shm")
PAYLOADS = {64: 30000, 1024: 30000, 65536: 8000}
METRICS = ("p50_us", "p95_us", "p99_us", "cpu_us", "echo_mib_s")


def run(rounds, cpus, output):
    cases = list(itertools.product(PAYLOADS, TRANSPORTS))
    rng = random.Random(4311)
    all_rows = []
    with tempfile.TemporaryDirectory(prefix="pw-ipc-build-") as directory:
        executable = Path(directory) / "ipc-bench"
        subprocess.run(
            ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-pthread",
             str(Path(__file__).with_name("ipc-bench.c")), "-o", str(executable)],
            check=True,
        )
        for trial in range(1, rounds + 1):
            rng.shuffle(cases)
            for size, transport in cases:
                completed = subprocess.run(
                    [str(executable), transport, str(size), str(PAYLOADS[size]),
                     *map(str, cpus)],
                    check=True, text=True, stdout=subprocess.PIPE, timeout=40,
                )
                values = [float(value) for value in completed.stdout.strip().split(",")]
                all_rows.append((trial, size, transport, *values))

    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("trial", "bytes", "transport", *METRICS))
        writer.writerows(all_rows)

    print(f"{os.uname().release}; CPUs {cpus[0]},{cpus[1]}; {rounds} repeats")
    print("bytes transport " + " ".join(METRICS))
    for size, transport in itertools.product(PAYLOADS, TRANSPORTS):
        samples = [row[3:] for row in all_rows if row[1:3] == (size, transport)]
        medians = [statistics.median(column) for column in zip(*samples)]
        print(size, transport, " ".join(f"{value:.2f}" for value in medians))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--cpus", nargs=2, type=int, default=sorted(os.sched_getaffinity(0))[:2])
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if options.repeats < 1 or len(options.cpus) != 2:
        parser.error("specify a positive repeat count and two CPUs")
    run(options.repeats, options.cpus, options.output)
