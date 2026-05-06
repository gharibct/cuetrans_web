import ast
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
IGNORED_DIRS = {".git", ".claude", "__pycache__", "venv"}


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def find_print_calls(path: Path) -> list[tuple[int, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    matches = []

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            matches.append((node.lineno, node.col_offset + 1))

    return matches


def main() -> int:
    violations = []

    for path in PROJECT_ROOT.rglob("*.py"):
        if is_ignored(path):
            continue

        for line, column in find_print_calls(path):
            violations.append(f"{path.relative_to(PROJECT_ROOT)}:{line}:{column}")

    if violations:
        sys.stderr.write("Raw print() calls are not allowed. Use utils.debug.debug_print().\n")
        sys.stderr.write("\n".join(violations) + "\n")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

