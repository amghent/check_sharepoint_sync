import logging.config
import os
import socket
import smtplib
import sys

import yaml

from croniter import croniter
from datetime import timedelta, datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from time import sleep


APP_NAME: str = ""
APP_VERSION: str = ""

CURRENT_DIR: Path = Path(__file__).parent
HOME_DIR: Path = Path.home()
SYNC_DIR: Path = HOME_DIR
MACHINE_NAME: str = ""

LOGGER = logging.getLogger(APP_NAME)


def configure_logger():
    with open(os.path.join(CURRENT_DIR, "logging.yaml"), "r") as config_file:
        config_data = yaml.safe_load(config_file.read())

        logging.config.dictConfig(config_data)
        logging.basicConfig(level=logging.NOTSET)


def read_config():
    global APP_NAME, APP_VERSION

    with open(os.path.join(CURRENT_DIR, "config.yaml"), "r") as config_file:
        config_data = yaml.safe_load(config_file)

    APP_NAME = config_data["name"]
    APP_VERSION = config_data["version"]

    title = f"{APP_NAME.upper()} v.{APP_VERSION}"

    LOGGER.info(len(title) * "_")
    LOGGER.info(title)
    LOGGER.info(len(title) * "_")

    return config_data


def log_dirs():
    LOGGER.info(f"Current directory: {CURRENT_DIR} ")
    LOGGER.info(f"User's home directory: {HOME_DIR} ")


def set_sync_dir(config_data):
    global SYNC_DIR

    for sub_dir in config_data["sync_dir"]:
        SYNC_DIR = os.path.join(SYNC_DIR, sub_dir)

    LOGGER.info(f"Sync directory: {SYNC_DIR}")

    assert os.path.exists(SYNC_DIR)
    assert os.path.isdir(SYNC_DIR)


def get_machine_name():
    global MACHINE_NAME

    MACHINE_NAME = socket.gethostname()

    LOGGER.info(f"This buddy's name: {MACHINE_NAME}")


def write_info():
    output_path = os.path.join(SYNC_DIR, f"{MACHINE_NAME}.txt")

    try:
        with open(output_path, "w") as output_file:
            output_file.write(f"Output written on {datetime.now()}\n\n(the content of this file is not important)")

        LOGGER.info(f"Writing info on sync directory for machine in {MACHINE_NAME}.txt")
    except PermissionError as err:
        LOGGER.error(f"Error writing info on sync directory: {err}")
        sys.exit(1)


def check_info(config_data):
    skip_files = []

    for sf in config_data["skip_files"]:
        skip_files.append(sf)

    sync_delta = int(config_data["sync_delta"])
    LOGGER.info(f"Synchronisation delta in seconds: {sync_delta}")

    min_ts = datetime.now() - timedelta(seconds=sync_delta)
    LOGGER.info(f"Oldest timestamp allowed for files: {min_ts}")

    file_list = os.listdir(SYNC_DIR)
    LOGGER.info(f"Found {len(file_list)} files in sync directory")

    for f in file_list:
        if f in skip_files:
            LOGGER.info(f"Skipping {f} (in list of files to skip)")
            continue

        if f == f"{MACHINE_NAME}.txt":
            LOGGER.info(f"Skipping {f} (machine's own file)")
            continue

        LOGGER.info(f"Verifying {f}")

        creation_epoch = os.stat(os.path.join(SYNC_DIR, f)).st_ctime
        creation_ts = datetime.fromtimestamp(creation_epoch)

        if creation_ts < min_ts:
            LOGGER.warning(f"File created on: {creation_ts}: TOO OLD")
            return False
        else:
            LOGGER.info(f"File created on: {creation_ts}: OK")

    LOGGER.info(f"Exiting, sync is ok on {MACHINE_NAME}")
    return True


def notify(config_data):
    with smtplib.SMTP(host=config_data["mail"]["server"], port=int(config_data["mail"]["port"])) as server:
        to = []

        for t in config_data["mail"]["to"]:
            to.append(t)

        msg = MIMEMultipart()

        msg["subject"] = Header(config_data["mail"]["subject"])
        msg["from"] = Header(config_data["mail"]["from"])
        msg["to"] = Header(",".join(map(str, to)))

        msg.attach(MIMEText(f"{config_data['mail']['text']}: {MACHINE_NAME}", "plain"))

        server.send_message(msg=msg)

        LOGGER.info(f"Notifying {msg['to']}")
        LOGGER.info(f"Exiting, sync is NOT OK on {MACHINE_NAME} (exit on first fail)")


def run(config_data):
    log_dirs()
    set_sync_dir(config_data=config_data)
    get_machine_name()
    write_info()

    ok = check_info(config_data=config_data)

    if not ok:
        notify(config_data=config_data)


def main():
    configure_logger()
    config_data = read_config()

    to_the_second = False
    cron = croniter(config_data["cron"], datetime.now())
    next_run = cron.get_next(ret_type=datetime)
    default_sleep = int(config_data["sleep"])

    LOGGER.info(f"Next run at: {next_run}")
    LOGGER.info(f"Default sleep: {default_sleep}")

    while True:
        LOGGER.debug("Checking ...")

        if datetime.now() > next_run:
            run(config_data=config_data)

            to_the_second = True
            next_run = cron.get_next(ret_type=datetime)
            LOGGER.info(f"Next run at: {next_run}")
        else:
            if to_the_second:
                sleep(default_sleep)
            else:
                sleep(1)


if __name__ == "__main__":
    main()
