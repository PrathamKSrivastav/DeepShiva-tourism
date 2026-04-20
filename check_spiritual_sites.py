import json
from pathlib import Path

json_file = Path("data/json_content/spiritualSites.json")

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== spiritualSites.json Structure ===")
print(f"Root keys: {list(data.keys())}")
print()

for key, value in data.items():
    print(f"Key: '{key}'")
    print(f"Type: {type(value).__name__}")
    
    if isinstance(value, dict):
        print(f"Nested keys: {list(value.keys())[:5]}")  # First 5 keys
        for nested_key, nested_value in list(value.items())[:2]:
            print(f"  - {nested_key}: {type(nested_value).__name__}")
    
    elif isinstance(value, list):
        print(f"Length: {len(value)}")
        if value and isinstance(value[0], dict):
            print(f"First item keys: {list(value[0].keys())[:5]}")
    
    print()
