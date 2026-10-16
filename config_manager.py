"""
Config Manager for Auto Clicker
Handles loading and saving user preferences to config.json.
"""

import json
import os
from typing import Any, Dict

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "hours": 0,
    "minutes": 0,
    "seconds": 0,
    "milliseconds": 100,
    "use_jitter": False,
    "jitter_ms": 15,
    "mouse_button": "left",
    "click_type": "single",
    "location_mode": "current",
    "fixed_x": 500,
    "fixed_y": 500,
    "repeat_mode": "infinite",
    "repeat_count": 100,
    "hotkey_toggle": "F6",
    "hotkey_pick": "F7",
    "always_on_top": True,
}


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json, fallback to defaults."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Warning] Could not load config.json: {e}")
    return config


def save_config(config: Dict[str, Any]) -> None:
    """Save current configuration to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Warning] Could not save config.json: {e}")
