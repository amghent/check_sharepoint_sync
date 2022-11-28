import logging.config
import os
import socket
import smtplib

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

    sync_dir_found = False
    name = "unknown"

    for sync_dir in config_data["sync_dirs"]:
        name = sync_dir["name"]
        final_dir = HOME_DIR

        for sub_dir in sync_dir["sub_dirs"]:
            final_dir = os.path.join(final_dir, sub_dir)

        if os.path.exists(final_dir) and os.path.isdir(final_dir):
            SYNC_DIR = final_dir
            sync_dir_found = True
            break

    if sync_dir_found:
        LOGGER.info(f"Sync directory: {SYNC_DIR} ({name})")
        return True
    else:
        LOGGER.error(f"Could not find any of the pre-defined sync dirs")
        return False


def get_machine_name():
    global MACHINE_NAME

    MACHINE_NAME = socket.gethostname()

    LOGGER.info(f"This buddy's name: {MACHINE_NAME}")

    return True


def write_info():
    output_path = os.path.join(SYNC_DIR, f"{MACHINE_NAME}.txt")

    try:
        with open(output_path, "w") as output_file:
            output_file.write(f"Output written on {datetime.now()}\n\n(the content of this file is not important)")

        LOGGER.info(f"Writing info on sync directory for machine in {MACHINE_NAME}.txt")

        return True

    except PermissionError as err:
        LOGGER.error(f"Error writing info on sync directory: {err}")

        return False


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

    old_files = []

    for f in file_list:
        if f in skip_files:
            LOGGER.info(f"Skipping {f} (in list of files to skip)")
            continue

        if f == f"{MACHINE_NAME}.txt":
            LOGGER.info(f"Skipping {f} (machine's own file)")
            continue

        LOGGER.info(f"Verifying {f}")

        modified_epoch = os.stat(os.path.join(SYNC_DIR, f)).st_mtime
        modified_ts = datetime.fromtimestamp(modified_epoch)

        if modified_ts < min_ts:
            LOGGER.warning(f"File modified on: {modified_ts}: TOO OLD")
            old_files.append([f, modified_ts])
        else:
            LOGGER.info(f"File modified on: {modified_ts}: OK")

    LOGGER.info(f"Exiting, sync is ok on {MACHINE_NAME}")
    return len(old_files) == 0, old_files


def notify(config_data, old_files):
    try:
        with smtplib.SMTP(host=config_data["mail"]["server"], port=int(config_data["mail"]["port"])) as server:
            to = []

            for buddy in config_data["buddies"]:
                if str(buddy["name"]).lower() == MACHINE_NAME.lower():
                    for t in buddy["to"]:
                        to.append(t)

                    break

            msg = MIMEMultipart()

            msg["subject"] = Header(config_data["mail"]["subject"])
            msg["from"] = Header(config_data["mail"]["from"])
            msg["to"] = Header(",".join(map(str, to)))

            body = f"{config_data['mail']['text']}: {MACHINE_NAME}\n\n"
            body += f"File(s):\n"

            for o in old_files:
                body += f"{o[0]}: {o[1]}\n"

            msg.attach(MIMEText(body, "plain"))

            server.send_message(msg=msg)

            LOGGER.info(f"Notifying {msg['to']}")
            LOGGER.info(f"Aborting check, sync is NOT OK on {MACHINE_NAME} (abort on first fail)")
    except Exception as err:
        LOGGER.error(f"Could not notify people because of a mail server error: {err}")


def run(config_data):
    if not set_sync_dir(config_data=config_data):
        return

    get_machine_name()

    if not write_info():
        return

    check_ok, old_files = check_info(config_data=config_data)

    if not check_ok:
        notify(config_data=config_data, old_files=old_files)


def main():
    configure_logger()
    config_data = read_config()
    log_dirs()

    cron = croniter(config_data["cron"], datetime.now())
    next_run = cron.get_next(ret_type=datetime)

    LOGGER.info(f"Next run at: {next_run}")

    while True:
        LOGGER.debug("Checking ...")

        now = datetime.now()

        if now > next_run:
            run(config_data=config_data)

            next_run = cron.get_next(ret_type=datetime)
            LOGGER.info(f"Next run at: {next_run}")

        sleep(60 - now.second)


if __name__ == "__main__":
    main()
