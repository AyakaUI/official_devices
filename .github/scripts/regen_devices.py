import json
import os

DEVICES_DIR = "API/devices"
UPDATER_DIR = "API/updater"
DEVICES_JSON_PATH = "API/devices.json"
DEVICE_LIST_MD_PATH = "docs/DeviceList.md"

device_list = []

os.makedirs("API", exist_ok=True)
os.makedirs("docs", exist_ok=True)

if not os.path.exists(DEVICES_DIR):
    print(f"❌ Missing {DEVICES_DIR}")
    exit(1)

for device_file in os.listdir(DEVICES_DIR):
    if not device_file.endswith(".json"):
        continue

    path = os.path.join(DEVICES_DIR, device_file)

    try:
        with open(path, encoding="utf-8") as f:
            device_data = json.load(f)

        codename = device_data.get("codename")
        if not codename:
            continue

        last_updated = None
        version = None

        updater_path = os.path.join(UPDATER_DIR, f"{codename}.json")

        if os.path.exists(updater_path):
            try:
                with open(updater_path, encoding="utf-8") as f:
                    updater = json.load(f)

                # New OTA format
                if isinstance(updater, list) and updater:
                    build = updater[0]
                    last_updated = build.get("datetime")
                    version = build.get("version")

            except Exception as e:
                print(f"⚠ updater error {codename}: {e}")

        maintainers = device_data.get("maintainer", [])
        if isinstance(maintainers, dict):
            maintainers = [maintainers]

        maintainer_names = " && ".join(
            [
                m.get("display_name", "Unknown")
                for m in maintainers
                if isinstance(m, dict)
            ]
        )

        device_entry = {
            "codename": codename,
            "codename_alt": device_data.get("codename_alt", codename),
            "vendor": device_data.get("vendor", "Unknown"),
            "model": device_data.get("model", "Unknown Device"),
            "maintainer_name": maintainer_names or "No Maintainer",
            "frame": device_data.get("frame"),
            "active": device_data.get("active", False),
            "last_updated": last_updated,
            "version": version,
            "release": device_data.get("release"),
        }

        device_list.append(device_entry)

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON {path}: {e}")

device_list.sort(key=lambda x: x["codename"])

with open(DEVICES_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump({"devices": device_list}, f, indent=4, ensure_ascii=False)

# Markdown
active_devices = [d for d in device_list if d["active"]]
brands = {}

for device in active_devices:
    brands.setdefault(device["vendor"], []).append(device)

lines = [
    "# AyakaUI Device List",
    "Officially supported devices.\n",
    f"**Devices:** {len(active_devices)}",
    f"**Brands:** {len(brands)}",
    "",
]

for brand in sorted(brands):
    lines.append(f"## {brand}")
    devices = sorted(brands[brand], key=lambda x: x["model"])

    for i, device in enumerate(devices, 1):
        lines.append(f"{i}. {device['model']} (`{device['codename']}`)")

    lines.append("")

with open(DEVICE_LIST_MD_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"✅ Generated {len(device_list)} devices")
