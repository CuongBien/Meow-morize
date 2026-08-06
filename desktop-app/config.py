import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
SRS_FILE = os.path.join(os.path.dirname(__file__), "srs_data.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"notion_token": "", "database_id": ""}

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

def load_srs_data():
    if os.path.exists(SRS_FILE):
        try:
            with open(SRS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_srs_data(srs_data):
    with open(SRS_FILE, "w", encoding="utf-8") as f:
        json.dump(srs_data, f, ensure_ascii=False, indent=2)
