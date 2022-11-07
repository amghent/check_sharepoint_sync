import logging.config
import os
import yaml

from pathlib import Path


APP_NAME: str = ""
APP_VERSION: str = ""

CURRENT_DIR = Path(__file__).parent
HOME_DIR = Path.home()
AM_PYTHON_DIR_NL = os.path.join(HOME_DIR, "ArcelorMittal", "AM Python - Documenten")
AM_PYTHON_DIR_EN = os.path.join(HOME_DIR, "ArcelorMittal", "AM Python - Documents")
AM_PYTHON_DIR = AM_PYTHON_DIR_NL

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


def verify_am_python_dir():
    global AM_PYTHON_DIR

    LOGGER.info(f"User's home directory: {HOME_DIR} ")

    if os.path.exists(AM_PYTHON_DIR_NL):
        pass
    elif os.path.exists(AM_PYTHON_DIR_EN):
        AM_PYTHON_DIR = AM_PYTHON_DIR_EN
    else:
        raise Exception("Cannot find the AM Python - Document(en/s) directory")

    LOGGER.info(f"AM Python - Document(en/s) directory: {AM_PYTHON_DIR}")


if __name__ == "__main__":
    configure_logger()
    read_config()
    verify_am_python_dir()
