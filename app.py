import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

st.title("👵 노인일자리 출퇴근 시스템")

try:
    # Secrets에서 JSON 덩어리를 읽어와 파이썬 딕셔너리로 변환
    info = json.loads(st.secrets["connections"]["gsheets"]["service_account_json"])
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 시트 연결
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    doc = client.open_by_url(sheet_url)
    st.success(f"✅ [{doc.title}] 시트와 연결되었습니다!")

    # 명단 불러오기
    sheet = doc.get_worksheet(0)
    data = sheet.get_all_records()
    st.write("📋 명단을 성공적으로 확인했습니다.")

except Exception as e:
    st.error(f"❌ 연결 실패: {e}")
    st.info("새 키를 발급받으셨다면 Secrets 저장 후 반드시 'Reboot app'을 눌러주세요.")
