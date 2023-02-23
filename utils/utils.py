import json
import os

import yaml

from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent


CONFIG_PATH = os.path.join(get_project_root(), 'config', '')


def fetch_constants(section: str):
    with open(CONFIG_PATH + "constants.yaml", "r") as file:
        constants = yaml.safe_load(file)
    return constants[section]


def store_config(value: str, key: str, filename: str):
    with open(CONFIG_PATH + filename + '.json', 'r+') as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = {}
        finally:
            data.update({key: value})
            file.seek(0)
            json.dump(data, file)
            file.close()


def load_config(filename: str, key: str = None):
    with open(CONFIG_PATH + filename + '.json', 'r+') as file:
        data = json.load(file)
        file.close()
    if key:
        return data[key]
    return data


def update_config(data, filename: str):
    with open(CONFIG_PATH + filename + '.json', 'w+') as file:
        json.dump(data, file)
        file.close()
