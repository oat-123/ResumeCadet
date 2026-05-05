import os
import json

BASE_DIR = r"H:\Users\Asus\Desktop\oat\J.A.R.V.I.S\Automation\433resume_docx\output_docs\ชั้นปีที่ ๕\นนร.ชั้นปีที่ ๕"

print(f"Checking directory: {BASE_DIR}")
if os.path.exists(BASE_DIR):
    print("Directory exists.")
    folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
    print(f"Found {len(folders)} folders.")
    for f in folders[:5]:
        print(f"Folder: {f}")
        # Try to encode/decode to check for issues
        try:
            print(f"Encoded: {f.encode('utf-8')}")
        except:
            print("Failed to encode to utf-8")
else:
    print("Directory does NOT exist.")
