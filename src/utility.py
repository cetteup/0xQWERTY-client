import json
import os
import signal
import sys
import time

import yaml
from jsonschema import validate, ValidationError

import config
from classes import ClientConfig, YamlDumper
from logger import logger


def sleep_exit(exit_code: int, seconds: float = 15.0):
    logger.info(f'Window will close in {seconds} seconds...')
    time.sleep(seconds)
    sys.exit(exit_code)


def sleep_sigterm(seconds: float = 15.0):
    """
    Sleeps for `seconds` and then sends SIGTERM to itself
    (which is the easiest way of somewhat cleanly exiting once uvicorn is running)
    """
    logger.info(f'Window will close in {seconds} seconds...')
    time.sleep(seconds)
    os.kill(os.getpid(), signal.SIGTERM)


def load_logging_config() -> dict:
    logging_config_path = os.path.join(config.ROOT_DIR, 'logging.yaml')
    try:
        with open(logging_config_path, 'r') as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        logger.critical(f'Failed to load logging config from {logging_config_path}: {e}')
        sleep_exit(1)


def load_client_config() -> ClientConfig:
    schema_path = os.path.join(config.ROOT_DIR, 'config.schema.json')
    try:
        with open(schema_path, 'r') as s:
            schema = json.load(s)
    except (OSError, json.JSONDecodeError) as e:
        logger.critical(f'Failed to load config JSON schema from {schema_path}: {e}')
        sleep_exit(1)

    client_config_path = os.path.join(config.PWD, 'config.yaml')
    try:
        with open(client_config_path, 'r') as c:
            client_config = yaml.safe_load(c)
    except (OSError, yaml.YAMLError) as e:
        logger.critical(f'Failed to load client config from {client_config_path}: {e}')
        sleep_exit(1)

    # Ensure actual client config matches schema
    try:
        validate(client_config, schema)
    except ValidationError as e:
        logger.critical(f'Client config does not match schema: {e.json_path}: {e.message}')
        sleep_exit(1)

    return ClientConfig.from_dict(client_config)


def dump_client_config(client_config: ClientConfig) -> None:
    client_config_path = os.path.join(config.PWD, 'config.yaml')
    try:
        with open(client_config_path, 'w') as c:
            yaml.dump(client_config.to_dict(), c, sort_keys=False, Dumper=YamlDumper, default_flow_style=False)
    except (OSError, yaml.YAMLError) as e:
        logger.error(f'Failed to write client config: {e}')


