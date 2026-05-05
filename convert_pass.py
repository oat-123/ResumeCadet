import gspread
import json
import os
from google.oauth2.service_account import Credentials

# Configuration
SHEET_ID = '1Q-KqweZ__-EEDrsBy3jhdNS91otSda6-0M-Wd6vW2q4'
CREDS_FILE = 'credentials.json'
OUTPUT_JSON = 'passwords.json'

def normalize_name(name):
    if not isinstance(name, str): return ""
    name = name.replace("นนร.", "").replace("น.น.ร.", "").replace(" ", "").strip()
    return name

def update_from_google_sheets():
    try:
        # Define scopes
        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        
        # Authenticate
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the sheet
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Get all records
        data = sheet.get_all_values()
        if not data:
            print("No data found in sheet.")
            return

        # Use headers to find columns or assume index 0 and 1
        # data[0] are headers, data[1:] are values
        headers = data[0]
        rows = data[1:]
        
        print(f"Headers found: {headers}")
        
        mapping = {}
        for row in rows:
            if len(row) < 2: continue
            
            raw_name = row[0]
            raw_id = row[1]
            
            name = normalize_name(raw_name)
            # Ensure ID is a string and clean it
            password = str(raw_id).strip()
            
            if name and password:
                mapping[name] = password
                
        # Save to local passwords.json
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully updated {len(mapping)} records from Google Sheets.")
        
    except Exception as e:
        print(f"Error updating from Google Sheets: {e}")
        print("Make sure you have SHARED the Google Sheet with the client_email in your credentials.json")

if __name__ == '__main__':
    update_from_google_sheets()
