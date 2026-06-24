import os

def is_running_in_docker() -> bool:
    try:
        with open("/proc/1/cgroup", "r") as f:
            return "docker" in f.read() or "kubepods" in f.read()
    except Exception:
        return False


def get_orion_url():
    env = os.getenv("ORION_URL")
    if env:
        return env

    return "http://orion:1026" if is_running_in_docker() else "http://localhost:1026"


def get_quantumleap_url():
    env = os.getenv("QUANTUMLEAP_URL")
    if env:
        return env

    return "http://quantumleap:8668" if is_running_in_docker() else "http://localhost:8668"