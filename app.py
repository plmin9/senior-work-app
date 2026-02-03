import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="노인일자리 출퇴근 시스템", layout="centered")
st.title("👵 노인일자리 출퇴근 시스템")

try:
    # 1. Secrets에서 값 불러오기
    s = st.secrets["connections"]
    
    # 2. Private Key 정제 (줄바꿈 및 공백 문제 해결)
    # 여러 줄로 들어온 키를 합치고 공백을 제거합니다.
    raw_key = s["private_key"].strip()
    
    # 만약 \n이 텍스트로 들어있을 경우 실제 줄바꿈으로 변경
    clean_key = raw_key.replace("\\n", "\n")

    # 3. 구글 서비스 계정 인증 정보 설정
    creds_info = {
        "type": "service_account",
        "project_id": s["project_id"],
        "private_key": clean_key,
        "client_email": s["email"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    # 4. Google Sheets 인증
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 5. 스프레드시트 열기
    doc = client.open_by_url(s["spreadsheet"])
    st.success(f"✅ [{doc.title}] 시트와 연결되었습니다!")
    
    # 첫 번째 워크시트 데이터 가져오기 테스트
    sheet = doc.get_worksheet(0)
    data = sheet.get_all_records()
    
    if data:
        st.write("📋 현재 등록된 명단입니다:")
        st.dataframe(data)
    else:
        st.info("시트에 데이터가 비어 있습니다.")

except Exception as e:
    st.error(f"❌ 접속 오류가 발생했습니다.")
    st.info(f"상세 에러: {e}")
    st.warning("Secrets 설정에서 키가 정확히 입력되었는지, 혹은 시트가 서비스 계정에 공유되었는지 확인해 주세요.")
