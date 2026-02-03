import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

st.title("👵 노인일자리 출퇴근 시스템")

try:
    # 1. Secrets에서 JSON 덩어리 가져오기
    json_info = json.loads(st.secrets["connections"]["gsheets"]["service_account_json"])
    
    # 2. 인증 객체 생성
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(json_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 3. 시트 열기
    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    doc = client.open_by_url(sheet_url)
    st.success(f"✅ [{doc.title}] 시트에 성공적으로 연결되었습니다!")
    
    # 명단 가져오기
    sheet = doc.get_worksheet(0)
    data = sheet.get_all_records()
    st.write("📋 명단을 불러왔습니다. 아래에서 성함을 선택하세요.")
    # (이후 명단 표시 로직 추가...)

except Exception as e:
    st.error(f"❌ 최종 연결 실패: {e}")
