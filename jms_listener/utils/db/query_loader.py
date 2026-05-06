import yaml
from pathlib import Path
from utils.debug import debug_print

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_QUERY_CONFIG_PATH = BASE_DIR / "core" / "config" / "queries.yaml"

class QueryLoader:
    def __init__(self, config_path=DEFAULT_QUERY_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.queries = self._load_queries()
    
    def _load_queries(self):
        """Load queries from YAML file"""
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)
            debug_print(f"Data: {data}")
            return data.get('queries', {})
    
    def get(self, query_name: str) -> str:
        """Get query by name"""
        return self.queries.get(query_name)
    
    def __getitem__(self, key):
        return self.queries[key]

# Singleton instance
sql = QueryLoader()
