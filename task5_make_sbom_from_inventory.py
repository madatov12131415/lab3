import json
from datetime import datetime, timezone
from urllib.parse import quote


INPUT_FILE = "result_task_4_after.json"
OUTPUT_FILE = "after_bom.cdx.json"


def build_purl(name, version, arch):
    safe_name = quote(str(name), safe="")
    safe_version = quote(str(version), safe="")
    safe_arch = quote(str(arch), safe="")

    return f"pkg:deb/debian/{safe_name}@{safe_version}?arch={safe_arch}"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    components = []

    for pkg in inventory.get("packages", []):
        name = pkg.get("name")
        version = pkg.get("version", "")
        arch = pkg.get("arch", "")

        if not name:
            continue

        component = {
            "type": "library",
            "name": name,
            "version": version,
            "purl": build_purl(name, version, arch),
            "properties": [
                {
                    "name": "arch",
                    "value": str(arch)
                },
                {
                    "name": "description",
                    "value": str(pkg.get("description", ""))
                },
                {
                    "name": "size",
                    "value": str(pkg.get("size", ""))
                }
            ]
        }

        components.append(component)

    os_info = inventory.get("OS", {})

    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {
                "type": "operating-system",
                "name": os_info.get("name", ""),
                "version": os_info.get("version", ""),
                "properties": [
                    {
                        "name": "id",
                        "value": str(os_info.get("id", ""))
                    },
                    {
                        "name": "version_id",
                        "value": str(os_info.get("version_id", ""))
                    },
                    {
                        "name": "arch",
                        "value": str(os_info.get("arch", ""))
                    },
                    {
                        "name": "description",
                        "value": str(os_info.get("description", ""))
                    },
                    {
                        "name": "codename",
                        "value": str(os_info.get("codename", ""))
                    }
                ]
            }
        },
        "components": components
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(bom, f, indent=2, ensure_ascii=False)

    print(f"Components: {len(components)}")
    print(f"Created {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
