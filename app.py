import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import base64

st.title("👵 노인일자리 시스템 (최종 보안 연결)")

try:
    s = st.secrets["connections"]["gsheets"]
    
    # [최후의 방법] Base64로 인코딩된 키를 복호화하여 줄바꿈 문제를 원천 차단합니다.
    encoded_key = s["private_key_base64"]
    decoded_key = base64.b64decode(encoded_key).decode("utf-8")

    creds_info = {
        "type": s["type"],
        "project_id": s["project_id"],
        "private_key_id": s["private_key_id"],
        "private_key": decoded_key,
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
    
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 연결에 성공했습니다!")
    
    # 명단 표시
    sheet = doc.get_worksheet(0)
    st.write("📋 시스템 정상 작동 중")

except Exception as e:
    st.error(f"❌ 오류 발생: {e}")
    st.info("비밀키 인코딩 연결을 시도했습니다. 이 에러가 지속되면 키 재발급이 필요할 수 있습니다.")
