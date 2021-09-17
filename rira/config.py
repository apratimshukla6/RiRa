import toml
import logging
import os

def load_config(path="./config.toml"):
    if os.path.exists(path) and os.path.isfile(path):
        config = toml.load(path)
        return config
