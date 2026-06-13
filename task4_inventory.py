import os
import json
import platform
import subprocess


def get_os_info():
    os_info = {}

    with open("/etc/os-release") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os_info[key] = value.strip('"')

    return {
        "name": os_info.get("NAME"),
        "version": os_info.get("VERSION", ""),
        "arch": platform.machine(),
        "id": os_info.get("ID"),
        "version_id": os_info.get("VERSION_ID"),
        "description": os_info.get("PRETTY_NAME"),
        "codename": os_info.get("VERSION_CODENAME", "")
    }


def get_packages():
    cmd = [
        "dpkg-query",
        "-W",
        "-f=${Package}|${Version}|${Architecture}|${Installed-Size}|${Description}\n"
    ]

    result = subprocess.check_output(cmd, text=True)
    packages = []

    for line in result.splitlines():
        parts = line.split("|", 4)

        if len(parts) < 5:
            continue

        name, version, arch, size, desc = parts

        packages.append({
            "name": name,
            "version": version,
            "arch": arch,
            "description": desc.split(".")[0],
            "size": int(size) if size.isdigit() else None
        })

    return packages


def main():
    data = {
        "OS": get_os_info(),
        "packages": get_packages()
    }

    with open("result_task_4.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Created result_task_4.json")


if __name__ == "__main__":
    main()

