from flask import Flask, render_template, jsonify, send_from_directory, request
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Path to the resume directory (รองรับทั้ง local และ Vercel)
BASE_DIR = os.path.join(os.path.dirname(__file__), 'resumes')

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1Q-KqweZ__-EEDrsBy3jhdNS91otSda6-0M-Wd6vW2q4'

# โหลด credentials — ถ้ามี env var ใช้ env var, ถ้าไม่มีใช้ไฟล์ (local)
creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
if creds_json:
    creds_info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

gc = gspread.authorize(creds)

# ---- Helpers ----

def normalize_name(name):
    return name.replace("นนร.", "").replace("น.น.ร.", "").replace(" ", "").strip()

def load_passwords():
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet('ชั้น5')
    rows = ws.get_all_records()
    passwords = {}
    for row in rows:
        name = str(row.get('ยศ/ชื่อ – สกุล', '')).strip()
        raw  = row.get('หมายเลขประจำตัวประชาชน', '')
        try:
            pid = str(int(float(str(raw)))).strip()
        except:
            pid = str(raw).strip()
        if name and pid:
            passwords[normalize_name(name)] = pid
    return passwords

# ---- Routes ----

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/people')
def get_people():
    try:
        if not os.path.exists(BASE_DIR):
            return jsonify({"error": "Directory not found"}), 404
        folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
        people = [{"name": f.replace("นนร.", "").strip(), "fullName": f} for f in folders]
        return jsonify(people)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify', methods=['POST'])
def verify_id():
    data          = request.json
    full_name     = data.get('fullName', '')
    provided_pass = data.get('password', '')

    try:
        PASSWORDS_MAP = load_passwords()
    except Exception as e:
        return jsonify({"success": False, "message": f"ไม่สามารถเชื่อมต่อ Google Sheets: {str(e)}"}), 500

    name_key     = normalize_name(full_name)
    correct_pass = PASSWORDS_MAP.get(name_key)

    if correct_pass and provided_pass == correct_pass:
        folder_path = os.path.join(BASE_DIR, full_name)
        files = os.listdir(folder_path)
        return jsonify({"success": True, "files": files})
    return jsonify({"success": False, "message": "รหัสบัตรประชาชนไม่ถูกต้อง"}), 401

from urllib.parse import unquote

@app.route('/preview/<path:folder>/<path:filename>')
def preview_file(folder, filename):
    folder = unquote(folder)
    filename = unquote(filename)
    provided_pass = request.args.get('pass')
    try:
        PASSWORDS_MAP = load_passwords()
    except:
        return "ไม่สามารถเชื่อมต่อ Google Sheets", 500

    if PASSWORDS_MAP.get(normalize_name(folder)) == provided_pass:
        return send_from_directory(os.path.join(BASE_DIR, folder), filename)
    return "Unauthorized", 401

@app.route('/download/<path:folder>/<path:filename>')
def download_file(folder, filename):
    folder = unquote(folder)
    filename = unquote(filename)
    provided_pass = request.args.get('pass')
    try:
        PASSWORDS_MAP = load_passwords()
    except:
        return "ไม่สามารถเชื่อมต่อ Google Sheets", 500

    if PASSWORDS_MAP.get(normalize_name(folder)) == provided_pass:
        return send_from_directory(os.path.join(BASE_DIR, folder), filename, as_attachment=True)
    return "Unauthorized", 401

@app.route('/api/comment', methods=['POST'])
def add_comment():
    data      = request.json
    full_name = data.get('fullName', '').replace('นนร.', '').strip()
    comment   = data.get('comment', '').strip()

    if not full_name or not comment:
        return jsonify({"success": False, "message": "ข้อมูลไม่ครบ"}), 400

    try:
        sh = gc.open_by_key(SHEET_ID)
        ws = sh.worksheet('comment')
        ws.append_row([full_name, comment])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)