import json
import os

dirname = os.path.join(os.path.dirname(__file__), "..", "resources/json")


def load_json(name: str, num_keys: bool = False) -> dict | list:
    hook = keys_to_int if num_keys else None
    return json.load(
        open(os.path.join(dirname, f"{name}.json")), object_pairs_hook=hook
    )


def keys_to_int(x):
    """JSON only allows int keys so this is to reverse that"""
    return {int(k) if k.isdigit() else k: v for k, v in x}
