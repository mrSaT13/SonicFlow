# check_integration.py
import os
import json

def check():
    errors = []
    
    # Check folder structure
    if not os.path.exists("custom_components/sonicflow"):
        errors.append("❌ Папка custom_components/sonicflow не найдена")
    
    # Check manifest
    manifest_path = "custom_components/sonicflow/manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
            if manifest.get("domain") != "sonicflow":
                errors.append(f"❌ Domain в manifest: {manifest.get('domain')}")
            if not manifest.get("config_flow"):
                errors.append("❌ 'config_flow': true отсутствует в manifest.json")
    else:
        errors.append("❌ manifest.json не найден")
    
    # Check required files
    required = [
        "custom_components/sonicflow/config_flow.py",
        "custom_components/sonicflow/strings.json",
        "custom_components/sonicflow/translations/en.json",
        "custom_components/sonicflow/__init__.py",
    ]
    for file in required:
        if not os.path.exists(file):
            errors.append(f"❌ {file} не найден")
    
    if errors:
        print("ОШИБКИ:")
        for e in errors:
            print(e)
        return False
    else:
        print("✅ Все проверки пройдены!")
        return True

if __name__ == "__main__":
    check()