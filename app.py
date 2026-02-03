import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def get_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        
        # [자동 교정 로직]
        raw_key = s["private_key"]
        
        # 1. 실제 줄바꿈 문자로 변환
        clean_key = raw_key.replace("\\n", "\n")
        
        # 2. 앞뒤 불필요한 공백 제거
        clean_key = clean_key.strip()
        
        # 3. 마지막 줄바꿈이 없다면 강제로 추가 (PEM 파일의 표준 규격)
        if not clean_key.endswith("\n"):
            clean_key += "\n"

        creds_info = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": clean_key, # 교정된 키 사용
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 연결 설정 오류: {e}")
        return None
