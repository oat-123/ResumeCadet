from flask import Flask, render_template, jsonify, send_from_directory, request
import os
import json
import time
import threading
import urllib.parse
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Path to the resume directory (relative to the project root)
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'resumes')

# Google Sheets Configuration
SHEET_ID = '1Q-KqweZ__-EEDrsBy3jhdNS91otSda6-0M-Wd6vW2q4'
SHEET_NAME = 'ชั้น5'  # ชื่อชีทที่ต้องการ
LOG_SHEET_NAME = 'log'  # ชีทสำหรับเก็บ log
CACHE_TTL = 300  # Cache 5 นาที (300 วินาที)

# Cache variables
_passwords_cache = {}
_cache_timestamp = 0

def get_gspread_client():
    """Create gspread client from credentials.json or environment variable"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Try environment variable first (for Vercel deployment)
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        # Fallback to local file
        creds_file = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    
    return gspread.authorize(creds)

def load_passwords_from_sheets():
    """Load passwords directly from Google Sheets with caching"""
    global _passwords_cache, _cache_timestamp
    
    now = time.time()
    # Return cache if still valid
    if _passwords_cache and (now - _cache_timestamp) < CACHE_TTL:
        return _passwords_cache
    
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Try to open sheet by name, fallback to first sheet
        try:
            sheet = spreadsheet.worksheet(SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            print(f"Sheet '{SHEET_NAME}' not found, using first sheet")
            sheet = spreadsheet.sheet1
        
        data = sheet.get_all_values()
        if not data:
            return _passwords_cache
        
        rows = data[1:]  # Skip header row
        mapping = {}
        for row in rows:
            if len(row) < 2:
                continue
            raw_name = row[0]
            raw_id = row[1]
            name = normalize_name(raw_name)
            password = str(raw_id).strip()
            if name and password:
                mapping[name] = password
        
        _passwords_cache = mapping
        _cache_timestamp = now
        return mapping
        
    except Exception as e:
        print(f"Error loading from Google Sheets: {e}")
        if _passwords_cache:
            return _passwords_cache
        
        # Fallback to local passwords.json
        fallback_path = os.path.join(os.path.dirname(__file__), '..', 'passwords.json')
        if os.path.exists(fallback_path):
            with open(fallback_path, 'r', encoding='utf-8') as f:
                _passwords_cache = json.load(f)
                _cache_timestamp = now
                return _passwords_cache
        
        return {}

def log_to_sheets(name, password):
    """Log verification attempt to Google Sheets 'log' sheet (runs in background thread)"""
    def _write_log():
        try:
            client = get_gspread_client()
            spreadsheet = client.open_by_key(SHEET_ID)
            log_sheet = spreadsheet.worksheet(LOG_SHEET_NAME)
            
            # Timestamp in Thai timezone (UTC+7)
            thai_time = datetime.utcnow() + timedelta(hours=7)
            timestamp = thai_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Append row: name, pass, time
            log_sheet.append_row([name, password, timestamp], value_input_option='USER_ENTERED')
            print(f"Logged: {name} | {timestamp}")
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    # Run in background thread so it doesn't slow down the response
    thread = threading.Thread(target=_write_log, daemon=True)
    thread.start()

def normalize_name(name):
    if not name: return ""
    # Remove common prefixes, spaces and dots for matching
    return name.replace("นนร.", "").replace("น.น.ร.", "").replace("น.น.ร", "").replace(" ", "").replace(".", "").strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/people')
def get_people():
    try:
        if not os.path.exists(BASE_DIR):
            return jsonify({"error": "Directory not found"}), 404
        folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
        people = [{"name": f, "fullName": f} for f in folders]
        return jsonify(people)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def normalize_password(pwd):
    if not pwd: return ""
    # Map Thai numerals to Arabic numerals
    thai_to_arabic = str.maketrans('๐๑๒๓๔๕๖๗๘๙', '0123456789')
    pwd = str(pwd).translate(thai_to_arabic)
    # Replace common OCR/typing mistakes ('o', 'O' -> '0')
    pwd = pwd.replace('o', '0').replace('O', '0')
    # Remove all non-digit characters (spaces, dashes, etc.)
    return ''.join(filter(str.isdigit, pwd))

@app.route('/api/verify', methods=['POST'])
def verify_id():
    data = request.json
    full_name = data.get('fullName', '')
    provided_pass = str(data.get('password', '')).strip()
    
    # Log every verification attempt to Google Sheets
    log_to_sheets(full_name, provided_pass)
    
    # Load passwords from Google Sheets (with cache)
    passwords_map = load_passwords_from_sheets()
    
    name_key = normalize_name(full_name)
    correct_pass = passwords_map.get(name_key)
    
    if correct_pass:
        correct_pass_norm = normalize_password(correct_pass)
        provided_pass_norm = normalize_password(provided_pass)
        
        if provided_pass_norm == correct_pass_norm:
            folder_path = os.path.join(BASE_DIR, full_name)
            if os.path.exists(folder_path):
                files = os.listdir(folder_path)
                return jsonify({"success": True, "files": files})
            else:
                return jsonify({"success": False, "message": "ไม่พบโฟลเดอร์ไฟล์"}), 404
        else:
            return jsonify({"success": False, "message": "รหัสบัตรประชาชนไม่ถูกต้อง"}), 401
    else:
        return jsonify({"success": False, "message": "รหัสบัตรประชาชนไม่ถูกต้อง"}), 401

@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    folder = urllib.parse.unquote(folder)
    filename = urllib.parse.unquote(filename)
    provided_pass = str(request.args.get('pass', ''))
    name_key = normalize_name(folder)
    passwords_map = load_passwords_from_sheets()
    
    correct_pass = passwords_map.get(name_key)
    if correct_pass and normalize_password(correct_pass) == normalize_password(provided_pass):
        directory = os.path.join(BASE_DIR, folder)
        return send_from_directory(directory, filename, as_attachment=True)
    return f"Unauthorized: f={folder}, p={provided_pass}, c={correct_pass}", 401

@app.route('/preview/<folder>/<filename>')
def preview_file(folder, filename):
    folder = urllib.parse.unquote(folder)
    filename = urllib.parse.unquote(filename)
    provided_pass = str(request.args.get('pass', ''))
    name_key = normalize_name(folder)
    passwords_map = load_passwords_from_sheets()
    
    correct_pass = passwords_map.get(name_key)
    if correct_pass and normalize_password(correct_pass) == normalize_password(provided_pass):
        directory = os.path.join(BASE_DIR, folder)
        return send_from_directory(directory, filename, as_attachment=False)
    return f"Unauthorized: f={folder}, p={provided_pass}, c={correct_pass}", 401

# For local testing
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
