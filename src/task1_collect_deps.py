import json
import re
from pathlib import Path


PROJECT_DIR = Path("kubernetes")
OUTPUT_FILE = "result_task_1.json"


def package_url_go(name: str, version: str) -> str:
    clean_version = version.lstrip("v")
    return f"pkg:golang/{name}@{clean_version}"


def package_homepage_go(name: str) -> str:
    if name.startswith("github.com/"):
        return "https://" + name
    return "https://pkg.go.dev/" + name


def parse_go_mod(path: Path):
    deps = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    block = False
    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("//"):
            continue

        if line.startswith("require ("):
            block = True
            continue

        if block and line == ")":
            block = False
            continue

        if line.startswith("require "):
            line = line.replace("require ", "", 1).strip()

        if block or raw_line.strip().startswith("require "):
            line = line.split("//")[0].strip()
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                version = parts[1]
                if re.match(r"^[A-Za-z0-9_.\-/]+(\.[A-Za-z]{2,}|/)", name):
                    deps.append({
                        "name": name,
                        "version": version,
                        "ecosystem": "go",
                        "url": package_homepage_go(name),
                        "purl": package_url_go(name, version)
                    })

    return deps


def main():
    result = []
    seen = set()

    go_mod_files = sorted(PROJECT_DIR.rglob("go.mod"))

    for go_mod in go_mod_files:
        deps = parse_go_mod(go_mod)
        for dep in deps:
            key = (dep["name"], dep["version"], dep["ecosystem"])
            if key not in seen:
                seen.add(key)
                result.append(dep)

    result.sort(key=lambda x: (x["ecosystem"], x["name"], x["version"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    ecosystem_stats = {}
    for item in result:
        ecosystem_stats[item["ecosystem"]] = ecosystem_stats.get(item["ecosystem"], 0) + 1

    print(f"Saved dependencies: {len(result)}")
    print("Ecosystem stats:", ecosystem_stats)
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
