import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MAPPING_PATH = BASE_DIR / "core" / "config" / "mtl_variable_mapping.csv"


class VariableMappingLoader:
    def __init__(self, mapping_path=DEFAULT_MAPPING_PATH):
        self.mapping_path = Path(mapping_path)
        self.return_variables = self._load_return_variables()

    @staticmethod
    def _lookup_key(core_service: str, process_type: str, key: str) -> tuple[str, str, str]:
        return (
            (core_service or "").strip().lower(),
            (process_type or "").strip().lower(),
            (key or "").strip().upper(),
        )

    def _load_return_variables(self) -> dict[tuple[str, str, str], str]:
        return_variables = {}

        with open(self.mapping_path, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                lookup_key = self._lookup_key(
                    row.get("core_service"),
                    row.get("process_type"),
                    row.get("key"),
                )
                return_variables[lookup_key] = row.get("return_variable", "").strip()

        return return_variables

    def get_return_variable(self, core_service: str, process_type: str, key: str) -> str | None:
        return self.return_variables.get(
            self._lookup_key(core_service, process_type, key)        
        )


variable_mapping = VariableMappingLoader()
