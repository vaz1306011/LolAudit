import logging
import re
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

# Regex
LCU_PORT_KEY = "--app-port="
LCU_TOKEN_KEY = "--remoting-auth-token="
PORT_REGEX = re.compile(r"--app-port=(\d+)")
TOKEN_REGEX = re.compile(r"--remoting-auth-token=(\S+)")
LEAGUE_PROCESSES = {"LeagueClientUx.exe", "LeagueClientUx"}


def get_lcu_port_and_token() -> Optional[tuple[str, str]]:

    stdout = ""
    for proc in psutil.process_iter(["name", "cmdline"]):
        name, cmdline = proc.info["name"], proc.info["cmdline"]

        if name in LEAGUE_PROCESSES:
            stdout = " ".join(cmdline)

    port_match = PORT_REGEX.search(stdout)
    port = port_match.group(1).replace(LCU_PORT_KEY, "") if port_match else "0"

    token_match = TOKEN_REGEX.search(stdout)
    token = (
        token_match.group(1).replace(LCU_TOKEN_KEY, "").replace('"', "")
        if token_match
        else ""
    )

    if not token:
        return None

    return port, token


def wait_for_lcu_port_and_token() -> tuple[str, str]:
    import time

    logger.info("等待授權...")
    auth = get_lcu_port_and_token()
    while auth is None:
        time.sleep(1)
        auth = get_lcu_port_and_token()
    logger.info(f"授權成功\n  port: {auth[0]}\n  token: {auth[1]}")
    return auth


if __name__ == "__main__":
    print(get_lcu_port_and_token())
