import json5
import os.path


def check_settings(template: dict, config: dict, path: str = ""):
    for key in template:
        if key not in config:
            print(f"No {path}.{key} was found in config file. Copy from the template.")
            config[key] = template[key]
        elif isinstance(template[key], dict):
            if not isinstance(config[key], dict):
                print(f"Expect json object at {path}.{key}, {type(config[key])} found in config file. Copy from the template.")
                config[key] = template[key]
            check_settings(template[key], config[key], f"{path}.{key}")


if os.path.exists("settings.json"):
    with open("settings.json", "r", encoding="utf8") as f:
        settings = json5.load(f)
else:
    settings = dict()

with open("settings.template.json", "r", encoding="utf8") as f:
    settings_template = json5.load(f)

check_settings(settings_template, settings)
with open("settings.json", "w", encoding="utf8") as f:
    json5.dump(settings, f, ensure_ascii=False)

print("Config file was loaded successfully.")
