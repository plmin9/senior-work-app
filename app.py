import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="노인일자리 출퇴근 시스템", layout="centered")
st.title("👵 노인일자리 출퇴근 시스템")

# 1. 시트 연결 (가장 에러 없는 방식)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 명단 가져오기 (첫 번째 시트)
    # worksheet 이름을 정확히 기입하세요 (예: "명단" 또는 "Sheet1")
    main_df = conn.read(worksheet="명단", ttl=0) 
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
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = pd.DataFrame([{
                    "성함": selected_name, "시간": now, "구분": "출근",
                    "위도": loc['coords']['latitude'], "경도": loc['coords']['longitude'],
                    "메모": work_memo, "상태": "대기"
                }])
                # 데이터 추가
                existing_logs = conn.read(worksheet="근태로그", ttl=0)
                updated_logs = pd.concat([existing_logs, new_row], ignore_index=True)
                conn.update(worksheet="근태로그", data=updated_logs)
                st.balloons()
                st.info(f"{selected_name}님, 출근 등록되었습니다!")

        with col2:
            if st.button("🏠 퇴근하기", use_container_width=True):
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_row = pd.DataFrame([{
                    "성함": selected_name, "시간": now, "구분": "퇴근",
                    "위도": loc['coords']['latitude'], "경도": loc['coords']['longitude'],
                    "메모": work_memo, "상태": "대기"
                }])
                existing_logs = conn.read(worksheet="근태로그", ttl=0)
                updated_logs = pd.concat([existing_logs, new_row], ignore_index=True)
                conn.update(worksheet="근태로그", data=updated_logs)
                st.warning(f"{selected_name}님, 퇴근 등록되었습니다!")
    else:
        st.info("좌측 상단의 위치 권한 허용을 눌러주세요.")

except Exception as e:
    st.error(f"데이터 연결 오류: {e}")
    st.info("💡 Secrets 설정 형식이 'connections.gsheets'로 되어있는지 확인해주세요.")
