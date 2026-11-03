#!/usr/bin/env python3
"""
GTasks CLI & Dashboard Re-login Helper
Re-authenticates Google Tasks OAuth credentials (token.pickle / token.json)
without modifying or deleting any tasks from ~/.gtasks/tasks.db.
"""

import os
import sys
import pickle
from pathlib import Path

def main():
    print("=" * 60)
    print(" GTasks Google Re-authentication Helper")
    print("=" * 60)
    
    config_dir = Path(os.environ.get('GTASKS_CONFIG_DIR', os.path.expanduser('~/.gtasks')))
    config_dir.mkdir(parents=True, exist_ok=True)
    
    creds_file = config_dir / 'credentials.json'
    token_pickle = config_dir / 'token.pickle'
    token_json = config_dir / 'token.json'
    db_file = config_dir / 'tasks.db'

    print(f"[i] Config directory: {config_dir}")
    print(f"[i] Database location: {db_file} (Will NOT be modified)")
    
    if not creds_file.exists():
        print(f"[-] Error: Credentials file not found at {creds_file}")
        sys.exit(1)
        
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("[-] Error: google-auth-oauthlib or google-api-python-client not installed.")
        print("    Run: pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    scopes = ['https://www.googleapis.com/auth/tasks']

    print("[+] Starting fresh OAuth 2.0 authorization flow...")
    print("[+] Notice: Your local tasks database will remain 100% intact.")
    
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), scopes)

    try:
        # Try local server first (works if browser redirects to localhost)
        creds = flow.run_local_server(port=0, prompt='consent')
    except Exception as e:
        print(f"[!] Local server callback notice: {e}")
        print("[i] Switching to console / manual browser URL flow...")
        creds = flow.run_local_server(port=0, open_browser=False, prompt='consent')

    if not creds or not creds.valid:
        print("[-] Authentication failed: credentials are invalid.")
        sys.exit(1)

    # Save to token.pickle
    with open(token_pickle, 'wb') as f:
        pickle.dump(creds, f)
    print(f"[+] Successfully updated {token_pickle}")

    # Save to token.json
    try:
        with open(token_json, 'w') as f:
            f.write(creds.to_json())
        print(f"[+] Successfully updated {token_json}")
    except Exception as e:
        print(f"[!] Warning writing token.json: {e}")

    # Verify connection
    print("[+] Verifying Google Tasks API connection...")
    try:
        service = build('tasks', 'v1', credentials=creds)
        results = service.tasklists().list(maxResults=10).execute()
        lists = results.get('items', [])
        print(f"[✓] Verification successful! Found {len(lists)} task list(s):")
        for lst in lists:
            print(f"    - {lst.get('title')} (ID: {lst.get('id')})")
        print("\n[✓] All done! You can now run 'gtasks advanced-sync' or use the app safely.")
    except Exception as e:
        print(f"[-] Verification failed: {e}")

if __name__ == '__main__':
    main()
