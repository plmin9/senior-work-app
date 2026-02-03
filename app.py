import streamlit as st
import pandas as pd
import gspread
import datetime
from streamlit_js_eval import get_geolocation

# 1. 시트 ID 설정 (실제 ID로 확인됨)
SHEET_ID = "1y5XoW1L_fO7V7jW4eA7P-V7yvXo_U9C-V7yvXo_U9C" # 예시이므로 본인 시트 ID로 다시 확인

def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            # 설정값을 그대로 딕셔너리로 만듭니다.
            key_info = dict(st.secrets["gcp_service_account"])
            
            # 여기서 replace를 쓰면 오히려 에러가 날 수 있으니
            # 문자열 양 끝의 불필요한 공백만 제거하고 바로 보냅니다.
            key_info["private_key"] = key_info["private_key"].strip()
            
            return gspread.service_account_from_dict(key_info)
        return None
    except Exception as e:
        st.error(f"⚠️ 인증 처리 중 상세 오류: {e}")
        return None
        
st.title("👵 노인일자리 출퇴근 시스템")

# 시트 연결 시도
client = get_gspread_client()

if client:
    try:
        # 데이터 읽기
        sheet = client.open_by_key(SHEET_ID)
        # 1번째 탭(명단)에서 어르신 성함 가져오기
        main_df = pd.DataFrame(sheet.get_worksheet(0).get_all_records())
        names = main_df["성함"].unique()
        
        selected_name = st.selectbox("🙋 성함을 선택해주세요", names)
        
        st.divider()
        
        # 위치 정보 가져오기
        loc = get_geolocation()
        if loc:
            st.success("📍 위치 확인 완료")
            
            work_memo = st.text_input("오늘의 활동 내용 (예: 공원 청소)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 출근하기", use_container_width=True):
                    log_sheet = sheet.worksheet("근태로그")
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_sheet.append_row([selected_name, now, "출근", loc['coords']['latitude'], loc['coords']['longitude'], work_memo, "대기"])
                    st.balloons()
                    st.info(f"{selected_name}님, 출근 등록되었습니다!")
            
            with col2:
                if st.button("🏠 퇴근하기", use_container_width=True):
                    log_sheet = sheet.worksheet("근태로그")
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_sheet.append_row([selected_name, now, "퇴근", loc['coords']['latitude'], loc['coords']['longitude'], work_memo, "대기"])
                    st.warning(f"{selected_name}님, 퇴근 등록되었습니다!")
        else:
            st.info("좌측 상단의 위치 권한 허용을 눌러주세요.")
            
    except Exception as e:
        st.error(f"데이터 연결 오류: {e}")
else:
    st.error("구글 서비스 인증에 실패했습니다. Secrets 설정을 확인하세요.")












