import argparse
import os
import signal
import subprocess
import sys
import time
from typing import Dict, List, Optional
import requests

DEFAULT_AGENTS = [
    {"id": "V001", "port": 8001, "emergency": False},
    {"id": "V002", "port": 8002, "emergency": False},
    {"id": "V003", "port": 8003, "emergency": False},
    {"id": "V004", "port": 8004, "emergency": False},
    {"id": "EV01", "port": 8005, "emergency": True},
]


class AgentClusterLauncher:
    """
    Manages spawning, monitoring, and stopping independent vehicle agent processes
    on separate local ports to demonstrate true multi-process decentralization.
    """

    def __init__(self, agent_configs: Optional[List[Dict]] = None):
        self.configs = agent_configs or DEFAULT_AGENTS
        self.processes: Dict[str, subprocess.Popen] = {}

    def start_all(self):
        """
        Spawns each agent as an independent process on its assigned port.
        """
        python_exe = sys.executable
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        print(f"Launching {len(self.configs)} independent vehicle agents...")
        for cfg in self.configs:
            vid = cfg["id"]
            port = cfg["port"]
            cmd = [
                python_exe,
                "-m", "app.vehicle_agents.agent_worker",
                "--id", vid,
                "--port", str(port)
            ]
            if cfg.get("emergency"):
                cmd.append("--emergency")

            env = os.environ.copy()
            env["PYTHONPATH"] = backend_dir

            proc = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.processes[vid] = proc
            print(f"  [+] Spawned Agent {vid} on http://localhost:{port} (PID: {proc.pid})")

        print("Waiting 2 seconds for microservices to bind...")
        time.sleep(2)
        self.check_status()

    def check_status(self) -> Dict[str, Any]:
        """
        Pings health endpoints of all configured agents.
        """
        status_report = {}
        for cfg in self.configs:
            vid = cfg["id"]
            port = cfg["port"]
            url = f"http://127.0.0.1:{port}/health"
            try:
                resp = requests.get(url, timeout=1.0)
                if resp.status_code == 200:
                    status_report[vid] = {"status": "ONLINE", "port": port, "data": resp.json()}
                else:
                    status_report[vid] = {"status": f"HTTP_{resp.status_code}", "port": port}
            except Exception as e:
                status_report[vid] = {"status": "OFFLINE", "port": port, "error": str(e)}

        return status_report

    def stop_all(self):
        """
        Terminates all running agent worker subprocesses.
        """
        print("Terminating agent processes...")
        for vid, proc in list(self.processes.items()):
            try:
                proc.terminate()
                proc.wait(timeout=2.0)
                print(f"  [-] Stopped agent {vid} (PID: {proc.pid})")
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self.processes.clear()


def main():
    parser = argparse.ArgumentParser(description="Multi-process Vehicle Agent Launcher")
    parser.add_argument("--start", action="store_true", help="Start all agent processes")
    parser.add_argument("--stop", action="store_true", help="Stop all agent processes")
    parser.add_argument("--status", action="store_true", help="Check status of agent processes")
    args = parser.parse_args()

    launcher = AgentClusterLauncher()

    if args.start:
        launcher.start_all()
        try:
            print("\nAgents running. Press Ctrl+C to terminate all agents...")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop_all()
    elif args.status:
        report = launcher.check_status()
        print("\nAgent Cluster Status:")
        for vid, info in report.items():
            print(f"  {vid} (Port {info.get('port')}): {info.get('status')}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

