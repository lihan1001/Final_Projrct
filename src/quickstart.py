import datetime
import os.path
import json
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 如果修改這些範圍，請刪除 token.json 檔案
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# 從 JSON 檔案中讀取資料
with open('dict/fridge_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("dict/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        for ingredient in data:
            if validate_date(ingredient['expiry']):
                expiry_date = ingredient['expiry']

                # 使用日期格式，無需具體的時間，設定為全天事件
                event = {
                    'summary': ingredient['name'],
                    'description': f"數量: {ingredient['quantity']}, 類別: {ingredient['category']}",
                    'start': {
                        'date': expiry_date,  # 設定為全天事件
                        'timeZone': 'Asia/Taipei',
                    },
                    'end': {
                        'date': expiry_date,  # 設定為全天事件
                        'timeZone': 'Asia/Taipei',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},  # 24小時前通知
                            {'method': 'email', 'minutes': 7 * 24 * 60}  # 一週前通知
                        ],
                    },
                }

                # 嘗試創建事件
                event_result = service.events().insert(calendarId='primary', body=event).execute()
                print(f'Event created: {event_result.get("htmlLink")}')
            else:
                print(f"Invalid date format for ingredient {ingredient['name']} with expiry {ingredient['expiry']}")

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()