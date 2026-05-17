import csv
import json
from collections import Counter


INPUT_FILE = "result_task_2.json"
OUTPUT_JSON = "result_task_3.json"
OUTPUT_CSV = "result_task_3.csv"


SEVERITIES = ["CRITICAL", "HIGH", "MODERATE", "LOW"]


def strategy(dep):
    vulns = dep.get("vulnerabilities", [])
    if not vulns:
        return "Уязвимостей не найдено"

    secure_version = dep.get("secure_version")
    if secure_version and secure_version != dep["version"]:
        return f"Обновить зависимость до версии {secure_version} или выше"

    return "Проверить advisory вручную; patched version не указан"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        deps = json.load(f)

    rows = []

    for dep in deps:
        vulns = dep.get("vulnerabilities", [])
        if not vulns:
            continue

        counts = Counter(v["severity"] for v in vulns)

        row = {
            "name": dep["name"],
            "version": dep["version"],
            "ecosystem": dep["ecosystem"],
            "critical": counts.get("CRITICAL", 0),
            "high": counts.get("HIGH", 0),
            "moderate": counts.get("MODERATE", 0),
            "low": counts.get("LOW", 0),
            "total_vulnerabilities": len(vulns),
            "secure_version": dep.get("secure_version", dep["version"]),
            "recommended_strategy": strategy(dep)
        }
        rows.append(row)

    rows.sort(key=lambda x: x["total_vulnerabilities"], reverse=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "name",
            "version",
            "ecosystem",
            "critical",
            "high",
            "moderate",
            "low",
            "total_vulnerabilities",
            "secure_version",
            "recommended_strategy"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Vulnerable dependencies: {len(rows)}")
    print(f"Output: {OUTPUT_JSON}")
    print(f"Output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
