import streamlit as st
import gspread
import json
from google.oauth2.service_account import Credentials

def get_gspread_client():
    try:
        # Secrets에서 전체 정보를 딕셔너리로 읽어옴
        s = st.secrets["connections"]["gsheets"]
        
        # private_key 내부의 모든 \n 문자를 실제 줄바꿈으로 강제 치환
        # (앞뒤 따옴표나 불필요한 공백을 완전히 제거하는 로직 포함)
        p_key = s["private_key"].strip().replace("\\n", "\n")
        
        # 구글 인증용 정보 재구성
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
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"⚠️ 연결 실패: {e}")
        return None

client = get_gspread_client()

if client:
    try:
        # 파일 이름을 "근태로그" 대신 시트의 URL(주소)로 직접 열기 (가장 확실함)
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        doc = client.open_by_url(sheet_url)
        st.success("✅ 구글 시트 연결 성공!")
        
        # 첫 번째 시트의 성함 목록 가져오기 테스트
        sheet = doc.get_worksheet(0)
        names = sheet.col_values(1)[1:] # 첫 번째 열의 제목 빼고 가져오기
        st.write(f"불러온 명단: {names}")
        
    except Exception as e:
        st.error(f"⚠️ 시트 열기 실패: {e}")
