import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

LAB=Path("/root/pw-ipc-client-lab")
spec=importlib.util.spec_from_file_location("controller","/root/pw-ipc-client-controller.py")
controller=importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


def client_socket():
    return subprocess.run(["ss","-Hntpe","state","established","( sport = :29000 )"],
                          capture_output=True,text=True,check=True).stdout.strip()


def sockets():
    return subprocess.run(["ss","-Hxnpa"],capture_output=True,text=True,check=True).stdout.splitlines()


def log_peers(rows,records,pid):
    server_inodes={line.split()[5] for line in rows
                   if "ESTAB" in line and "u_str" in line
                   and "pid="+str(pid)+"," in line and "/run/pw-ipc-test/log.sock" in line}
    return sorted({record["name"] for record in records if record["name"]!="logservice"
                   and any("pid="+str(record["pid"])+"," in line and "ESTAB" in line
                           and len(line.split())>7 and line.split()[7] in server_inodes
                           for line in rows)})


def main():
    records=json.loads((LAB/"launched.json").read_text())
    logger=next(row for row in records if row["name"]=="logservice")
    before_client=client_socket()
    if not before_client:
        raise RuntimeError("client must be connected for the reconnect probe")
    before_rows=sockets()
    before_peers=log_peers(before_rows,records,logger["pid"])
    if not before_peers:
        raise RuntimeError("no connected log clients were identified")
    before_inode=re.search(r"\bino:(\d+)",before_client).group(1)
    started=time.monotonic()
    controller.terminate([logger],signal.SIGUSR1)
    replacement=controller.launch("logservice",logger["args"],Path(logger["cwd"]))
    records=[replacement if row["name"]=="logservice" else row for row in records]
    (LAB/"launched.json").write_text(json.dumps(records,indent=2)+"\n")
    events=[]
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        current_client=client_socket()
        current_peers=log_peers(sockets(),records,replacement["pid"])
        inode=re.search(r"\bino:(\d+)",current_client)
        event={"elapsed_s":round(time.monotonic()-started,3),"peers":current_peers,
               "same_client":bool(inode and inode.group(1)==before_inode)}
        events.append(event)
        if not event["same_client"]:
            raise RuntimeError("game client session changed during log restart")
        if current_peers==before_peers:
            break
        time.sleep(0.25)
    result={"before_logger_pid":logger["pid"],"after_logger_pid":replacement["pid"],
            "before_peers":before_peers,"after_peers":events[-1]["peers"],
            "elapsed_s":events[-1]["elapsed_s"],"same_client":events[-1]["same_client"],
            "before_client":before_client,"after_client":client_socket(),
            "all_processes_alive":all(controller.alive(row) for row in records),
            "events":events}
    (LAB/"log-reconnect.json").write_text(json.dumps(result,indent=2)+"\n")
    if result["before_peers"]!=result["after_peers"] or not result["all_processes_alive"]:
        raise RuntimeError("log clients failed to recover")
    print(json.dumps(result),flush=True)


if __name__=="__main__":
    main()
