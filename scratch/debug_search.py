"""Debug script to check why search is not finding names"""
import os
import json
import sys

BASE_DIR = r"H:\Users\Asus\Desktop\oat\J.A.R.V.I.S\Automation\433resume_docx\output_docs\ชั้นปีที่ ๕\นนร.ชั้นปีที่ ๕"
PASSWORDS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'passwords.json')

print("=" * 60)
print("DEBUG: Search Name Matching")
print("=" * 60)

# 1. Check if BASE_DIR exists
print(f"\n1. BASE_DIR exists: {os.path.exists(BASE_DIR)}")

# 2. List first 5 folders
folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
print(f"\n2. Total folders: {len(folders)}")
print("   First 5 folders:")
for f in folders[:5]:
    print(f"   - '{f}' (repr: {repr(f)})")

# 3. Check passwords.json
with open(PASSWORDS_PATH, 'r', encoding='utf-8') as pf:
    passwords = json.load(pf)
print(f"\n3. Total passwords entries: {len(passwords)}")
print("   First 5 password keys:")
for k in list(passwords.keys())[:5]:
    print(f"   - '{k}' (repr: {repr(k)})")

# 4. Test normalization matching
def normalize_name(name):
    if not name: return ""
    return name.replace("นนร.", "").replace("น.น.ร.", "").replace("น.น.ร", "").replace(" ", "").replace(".", "").strip()

print(f"\n4. Normalization test:")
matched = 0
unmatched_examples = []
for folder in folders:
    normalized = normalize_name(folder)
    if normalized in passwords:
        matched += 1
    else:
        if len(unmatched_examples) < 5:
            unmatched_examples.append((folder, normalized))

print(f"   Matched: {matched}/{len(folders)}")
if unmatched_examples:
    print(f"   Unmatched examples:")
    for orig, norm in unmatched_examples:
        print(f"   - Folder: '{orig}' -> Normalized: '{norm}'")
        # Try to find closest match in passwords
        for pk in passwords:
            if norm[:5] == pk[:5]:
                print(f"     Close match in passwords: '{pk}'")
                break

# 5. Check API response format
print(f"\n5. Simulated API response (first 3):")
people = [{"name": f, "fullName": f} for f in folders[:3]]
api_json = json.dumps(people, ensure_ascii=False, indent=2)
print(api_json)

# 6. Check if there are hidden chars
print(f"\n6. Hidden character check in first folder name:")
first = folders[0]
for i, ch in enumerate(first):
    print(f"   [{i}] U+{ord(ch):04X} = '{ch}'")
    if i > 20:
        print("   ... (truncated)")
        break
