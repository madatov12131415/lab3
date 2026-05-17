import json
import os
import re
import requests
import semver


INPUT_FILE = "result_task_1.json"
OUTPUT_FILE = "result_task_2.json"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


QUERY = """
query($package: String!, $ecosystem: SecurityAdvisoryEcosystem!) {
  securityVulnerabilities(first: 100, package: $package, ecosystem: $ecosystem) {
    nodes {
      vulnerableVersionRange
      firstPatchedVersion {
        identifier
      }
      advisory {
        ghsaId
        summary
        severity
      }
    }
  }
}
"""


def normalize_go_version(version: str) -> str:
    version = version.strip()
    version = version.split("+")[0]
    version = version.lstrip("v")

    if "-" in version:
        version = version.split("-")[0]

    parts = version.split(".")
    normalized_parts = []

    for part in parts:
        digits = re.match(r"(\d+)", part)
        if digits:
            normalized_parts.append(str(int(digits.group(1))))
        else:
            normalized_parts.append("0")

    while len(normalized_parts) < 3:
        normalized_parts.append("0")

    return ".".join(normalized_parts[:3])


def version_satisfies_range(version: str, vulnerable_range: str) -> bool:
    try:
        v = semver.Version.parse(normalize_go_version(version))
    except Exception:
        return False

    checks = re.split(r",|\s+", vulnerable_range)
    checks = [c.strip() for c in checks if c.strip()]

    for check in checks:
        m = re.match(r"(<=|>=|<|>|=)?\s*v?([0-9]+(?:\.[0-9]+){0,2})", check)
        if not m:
            continue

        op = m.group(1) or "="

        try:
            target = semver.Version.parse(normalize_go_version(m.group(2)))
        except Exception:
            continue

        if op == "<" and not (v < target):
            return False
        if op == "<=" and not (v <= target):
            return False
        if op == ">" and not (v > target):
            return False
        if op == ">=" and not (v >= target):
            return False
        if op == "=" and not (v == target):
            return False

    return True


def github_graphql(package_name: str):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Set GITHUB_TOKEN environment variable")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    variables = {
        "package": package_name,
        "ecosystem": "GO"
    }

    response = requests.post(
        GITHUB_GRAPHQL_URL,
        headers=headers,
        json={"query": QUERY, "variables": variables},
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    return data["data"]["securityVulnerabilities"]["nodes"]


def choose_secure_version(version: str, vulnerabilities):
    patched_versions = []

    for vuln in vulnerabilities:
        patched = vuln.get("first_patched_version")
        if patched:
            patched_versions.append(patched)

    if not patched_versions:
        return version

    try:
        patched_versions.sort(
            key=lambda x: semver.Version.parse(normalize_go_version(x))
        )
        return patched_versions[-1]
    except Exception:
        return patched_versions[-1]


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        deps = json.load(f)

    result = []

    for idx, dep in enumerate(deps, start=1):
        print(f"[{idx}/{len(deps)}] {dep['name']} {dep['version']}")

        vulnerabilities = []

        try:
            nodes = github_graphql(dep["name"])
        except Exception as e:
            print("  FAIL:", e)
            nodes = []

        for node in nodes:
            vulnerable_range = node.get("vulnerableVersionRange", "")

            if version_satisfies_range(dep["version"], vulnerable_range):
                first_patched = node.get("firstPatchedVersion")

                vulnerabilities.append({
                    "name": node["advisory"]["ghsaId"],
                    "severity": node["advisory"]["severity"],
                    "vulnerable_range": vulnerable_range,
                    "first_patched_version": first_patched["identifier"] if first_patched else None
                })

        item = dict(dep)
        item["vulnerabilities"] = vulnerabilities
        item["secure_version"] = choose_secure_version(dep["version"], vulnerabilities)

        result.append(item)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    vuln_count = sum(1 for x in result if x["vulnerabilities"])

    print(f"Saved dependencies: {len(result)}")
    print(f"Vulnerable dependencies: {vuln_count}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
