import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import base64

st.title("👵 노인일자리 출퇴근 시스템")

try:
    s = st.secrets["connections"]
    
    # 1. 쪼개진 키를 하나로 합치고, 모든 공백/줄바꿈 강제 제거
    combined_key = s["k1"] + s["k2"] + s["k3"]
    clean_b64 = "".join(combined_key.split()) # 모든 공백 제거
    
    # 2. Base64 해독
    decoded_key = base64.b64decode(clean_b64).decode("utf-8")
    
    # 3. 인증 정보 구성
    creds_info = {
        "type": "service_account",
        "project_id": "senior-work-486210",
        "private_key": decoded_key,
        "client_email": s["email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    creds = Credentials.from_service_account_info(creds_info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
    
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 연결되었습니다!")
    
    sheet = doc.get_worksheet(0)
    st.dataframe(sheet.get_all_records())

except Exception as e:
    st.error(f"❌ 접속 오류: {e}")
