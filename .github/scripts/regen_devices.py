import json
import os

# Configurações de caminhos
DEVICES_DIR = "API/devices"
UPDATER_DIR = "API/updater"
DEVICES_JSON_PATH = "API/devices.json"
DEVICE_LIST_MD_PATH = "docs/DeviceList.md"

device_list = []

# Garante que as pastas de saída existam
os.makedirs("API", exist_ok=True)
os.makedirs("docs", exist_ok=True)

if not os.path.exists(DEVICES_DIR):
    print(f"❌ Erro: Pasta {DEVICES_DIR} não encontrada.")
    exit(1)

for device_file in os.listdir(DEVICES_DIR):
    if not device_file.endswith(".json"):
        continue
        
    file_path = os.path.join(DEVICES_DIR, device_file)
    
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            device_data = json.load(f)

        codename = device_data.get("codename")
        if not codename:
            print(f"⚠️ Pulando {device_file}: chave 'codename' ausente.")
            continue

        updater_path = os.path.join(UPDATER_DIR, f"{codename}.json")
        last_updated = None
        version = None

        # Tenta buscar informações no Updater (API de atualizações)
        if os.path.exists(updater_path):
            try:
                with open(updater_path, "r", encoding='utf-8') as f:
                    updater_data = json.load(f)
                    response = updater_data.get("response", [])
                    if response and len(response) > 0:
                        # Tenta pegar datetime ou last_updated (suporta int ou string)
                        last_updated = response[0].get("datetime") or response[0].get("last_updated")
                        version = response[0].get("version")
            except Exception as e:
                print(f"⚠️ Erro ao ler updater para {codename}: {e}")

        # TRATAMENTO DOS MAINTAINERS (Aceita Objeto único ou Lista)
        maintainers_data = device_data.get("maintainer", [])
        
        if isinstance(maintainers_data, dict):
            # Se for um objeto só, transforma em lista para o loop funcionar
            maintainers_data = [maintainers_data]
            
        if isinstance(maintainers_data, list) and len(maintainers_data) > 0:
            maintainer_names = " && ".join(
                [m.get("display_name", "Unknown") for m in maintainers_data if isinstance(m, dict)]
            )
        else:
            # Caso o campo maintainer_name (string) já exista no seu JSON original
            maintainer_names = device_data.get("maintainer_name") or "No Maintainer"

        # Monta a entrada para o devices.json
        device_entry = {
            "codename": codename,
            "codename_alt": device_data.get("codename_alt", codename),
            "vendor": device_data.get("vendor", "Unknown"),
            "model": device_data.get("model", "Unknown Device"),
            "maintainer_name": maintainer_names,
            "frame": device_data.get("frame"),
            "active": device_data.get("active", False),
            "last_updated": last_updated,
            "version": version,
            "release": device_data.get("release"),
            "download_link": device_data.get("download_link", "#"),
            "archive": device_data.get("archive", "#"),
        }

        device_list.append(device_entry)

    except json.JSONDecodeError as e:
        print(f"❌ ERRO DE SINTAXE JSON em: {file_path}")
        print(f"   Linha {e.lineno}, Coluna {e.colno}: {e.msg}")
        continue # Pula o arquivo bugado mas continua processando o resto
    except Exception as e:
        print(f"❌ Erro inesperado ao processar {device_file}: {e}")

# Ordena por codename
device_list.sort(key=lambda x: x["codename"])

# 1. Salva o API/devices.json
with open(DEVICES_JSON_PATH, "w", encoding='utf-8') as f:
    json.dump({"devices": device_list}, f, indent=4, ensure_ascii=False)

# 2. Gera o docs/DeviceList.md (Markdown)
active_devices = [d for d in device_list if d["active"]]
brand_devices = {}
for device in active_devices:
    vendor = device["vendor"]
    brand_devices.setdefault(vendor, []).append(device)

sorted_brands = sorted(brand_devices.keys())

md_lines = [
    "# AyakaUI Device List",
    "List of all officially supported devices.\n",
    f"**Total Devices:** {len(active_devices)} | **Total Brands:** {len(sorted_brands)}\n",
    "---",
]

for brand in sorted_brands:
    md_lines.append(f"\n### {brand}")
    brand_devices[brand].sort(key=lambda x: x["model"])
    for idx, device in enumerate(brand_devices[brand], 1):
        md_lines.append(f"{idx}. {device['model']} (`{device['codename']}`)")

with open(DEVICE_LIST_MD_PATH, "w", encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print(f"✅ Sucesso! Processados {len(device_list)} dispositivos.")
