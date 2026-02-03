import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="노인일자리 출퇴근 시스템", layout="centered")

# 1. 구글 시트 연결 함수
def get_gspread_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds_info = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"], 
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
        st.error(f"연결 설정 실패: {e}")
        return None

# 2. 메인 실행 부분
st.title("👵 노인일자리 출퇴근 시스템")

client = get_gspread_client()

if client:
    try:
        # 시트 주소로 열기
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        doc = client.open_by_url(sheet_url)
        
        # 첫 번째 시트(명단) 선택
        sheet = doc.get_worksheet(0) 
        
        # 모든 데이터 가져오기
        data = sheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            
            # 성함 목록 추출 (시트의 첫 번째 열 제목이 '성함'이어야 합니다)
            if "성함" in df.columns:
                names = df["성함"].tolist()
                
                st.subheader("🙋 어르신 성함을 선택해주세요")
                selected_name = st.selectbox("성함 선택", names)
                
                st.write(f"### 반갑습니다, {selected_name} 어르신!")
                st.info("아래 버튼을 눌러 출퇴근을 기록해주세요.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 출근하기", use_container_width=True):
                        st.balloons()
                        st.success(f"{selected_name}님 출근 완료!")
                with col2:
                    if st.button("🏠 퇴근하기", use_container_width=True):
                        st.warning(f"{selected_name}님 퇴근 완료!")
            else:
                st.error("시트에 '성함' 열을 찾을 수 없습니다. 첫 줄에 '성함'이라고 적혀있는지 확인해주세요.")
        else:
            st.warning("시트에 데이터가 없습니다. 성함 명단을 입력해주세요.")
            
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류 발생: {e}")
else:
    st.warning("인증 정보를 확인 중입니다...")
