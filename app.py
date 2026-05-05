from flask import Flask, render_template, jsonify, send_from_directory, request
import os
import json

app = Flask(__name__)

# Path to the resume directory (Absolute for local)
BASE_DIR = r"H:\Users\Asus\Desktop\oat\J.A.R.V.I.S\Automation\433resume_docx\output_docs\ชั้นปีที่ ๕\นนร.ชั้นปีที่ ๕"

# Load passwords mapping
PASSWORDS_PATH = os.path.join(os.path.dirname(__file__), 'passwords.json')
with open(PASSWORDS_PATH, 'r', encoding='utf-8') as f:
    PASSWORDS_MAP = json.load(f)

def normalize_name(name):
    return name.replace("นนร.", "").replace("น.น.ร.", "").replace(" ", "").strip()

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
    data = request.json
    full_name = data.get('fullName', '')
    provided_pass = data.get('password', '')
    
    name_key = normalize_name(full_name)
    correct_pass = PASSWORDS_MAP.get(name_key)
    
    if correct_pass and provided_pass == correct_pass:
        # Return file list if verified
        folder_path = os.path.join(BASE_DIR, full_name)
        files = os.listdir(folder_path)
        return jsonify({"success": True, "files": files})
    else:
        return jsonify({"success": False, "message": "รหัสบัตรประชาชนไม่ถูกต้อง"}), 401

@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    provided_pass = request.args.get('pass')
    name_key = normalize_name(folder)
    
    if PASSWORDS_MAP.get(name_key) == provided_pass:
        directory = os.path.join(BASE_DIR, folder)
        return send_from_directory(directory, filename, as_attachment=True)
    return "Unauthorized", 401

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
