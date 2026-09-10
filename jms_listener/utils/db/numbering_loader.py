import yaml
from pathlib import Path
from utils.debug import debug_print

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_NUMBERING_CONFIG_PATH = BASE_DIR / "core" / "config" / "numbering.yaml"

class NumberingLoader:
    def __init__(self, config_path=DEFAULT_NUMBERING_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.numbering = self._load_numbering()

    def _load_numbering(self):
        """Load numbering config from YAML file"""
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
            debug_print(f"Data: {data}")
            return data.get('numbering', {})

    def get(self, workflow_name: str) -> dict:
        """Get numbering config ({strTranType, strTranNo}) by workflow name"""
        return self.numbering.get(workflow_name, {})

    def __getitem__(self, key):
        return self.numbering[key]

# Singleton instance
numbering = NumberingLoader()
