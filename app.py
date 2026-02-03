import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("👵 노인일자리 시스템")

try:
    s = st.secrets["connections"]["gsheets"]
    
    # [핵심 수리] 비밀키 앞뒤의 불필요한 공백과 줄바꿈을 완전히 제거합니다.
    p_key = s["private_key"].strip()
    
    # 만약 \n이 글자로 들어있다면 실제 줄바꿈으로 바꿔줍니다.
    if "\\n" in p_key:
        p_key = p_key.replace("\\n", "\n")

    creds_info = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": p_key,
        "client_email": s["client_email"],
        "client_id": s["client_id"],
        "auth_uri": s["auth_uri"],
        "token_uri": s["token_uri"],
        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
        "client_x509_cert_url": s["client_x509_cert_url"]
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 시트 열기
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 연결 성공!")
    
    # 명단 가져오기 테스트
    sheet = doc.get_worksheet(0)
    st.write("📋 첫 번째 시트의 내용을 불러왔습니다.")

except Exception as e:
    st.error(f"❌ 오류 발생: {e}")
