import os
import yaml
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load YAML configuration once
config_path = BASE_DIR / "core" / "config" / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

class Settings:
    def __init__(self, conf: dict):
        self.db_config = conf.get("database", {})
        
        # Best Practice: Read secrets from Environment Variables here, centrally!
        self.db_password = os.getenv("DB_PASSWORD", self.db_config.get("password", ""))

# Create a global singleton instance
settings = Settings(config)
