import json
from pathlib import Path

from graphify.extract import extract


def main() -> None:
    detection = json.loads(
        Path("graphify-out/.graphify_detect.json").read_text(encoding="utf-8")
    )
    files = [Path(path) for path in detection["files"].get("code", [])]
    result = extract(files, cache_root=Path("."), parallel=False)
    Path("graphify-out/.graphify_ast.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"AST: {len(result['nodes'])} nodes, {len(result['edges'])} edges")


if __name__ == "__main__":
    main()
