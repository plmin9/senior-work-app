import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("👵 노인일자리 출퇴근 관리")

try:
    s = st.secrets["connections"]
    
    # 여러 줄로 입력된 키를 하나로 합치고 앞뒤 공백만 정리합니다.
    p_key = s["private_key"].strip()

    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": p_key,
        "client_email": s["email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ 구글 시트[{doc.title}] 연결에 성공했습니다!")
    
    # 데이터 불러오기 확인
    sheet = doc.get_worksheet(0)
    st.dataframe(sheet.get_all_records())

except Exception as e:
    st.error("❌ 연결 오류가 발생했습니다.")
    st.code(str(e)) # 에러 내용을 코드로 표시해 가독성을 높였습니다.
