import streamlit as st
import pandas as pd
import gspread
import json
import datetime
from streamlit_js_eval import get_geolocation

# ==========================================
# 1. 설정 정보 (본인의 SHEET_ID로 수정 필수)
# ==========================================
SHEET_ID = "1lhCgIWvcn6QrQRKbzrFrU1tPaKtQr3c8GJ-i8hbCsEQ" 
JSON_KEY = "key.json"

st.set_page_config(page_title="노인일자리 관리시스템", layout="centered")

# [보완된 인증 함수]
def get_gspread_client():
    try:
        # Streamlit Cloud 환경 (Secrets 사용)
        if "gcp_service_account" in st.secrets:
            key_info = json.loads(st.secrets["gcp_service_account"], strict=False)
            return gspread.service_account_from_dict(key_info)
        # 로컬 환경 (key.json 파일 사용)
        else:
            return gspread.service_account(filename=JSON_KEY)
    except Exception as e:
        st.error(f"⚠️ 인증 처리 중 오류가 발생했습니다: {e}")
        return None

# ==========================================
# 2. 메인 화면 구성
# ==========================================
st.title("👵 노인일자리 출퇴근 시스템")

try:
    # (1) 명단 및 기본 현황 불러오기 (Pandas)
    read_url = f"https://docs.google.com/spreadsheets/d/1lhCgIWvcn6QrQRKbzrFrU1tPaKtQr3c8GJ-i8hbCsEQ/export?format=csv&gid=0"
    data = pd.read_csv(read_url)
    
    if not data.empty:
        names = data["성함"].unique()
        selected_name = st.selectbox("🙋 성함을 선택해주세요:", names)
        
        # (2) 구글 시트 쓰기 권한 연결
        client = get_gspread_client()
        
        if client:
            log_sheet = client.open_by_key(SHEET_ID).worksheet("근태로그")
            
            # [결재 확인 로직]
            all_logs_data = log_sheet.get_all_records()
            if all_logs_data:
                all_logs = pd.DataFrame(all_logs_data)
                if '승인여부' in all_logs.columns:
                    user_logs = all_logs[all_logs['성함'] == selected_name]
                    if not user_logs.empty:
                        last_status = user_logs.iloc[-1]['승인여부']
                        if last_status == "승인":
                            st.success(f"✅ 관리자 확인: {selected_name}님의 활동이 승인되었습니다!")
                        elif last_status == "반려":
                            st.error("⚠️ 반려: 활동 기록을 확인 후 다시 작성해주세요.")
                        else:
                            st.info("⏳ 현재 관리자가 활동 내용을 검토 중입니다.")

            # (3) 개인별 누적 시간 표시
            user_info = data[data["성함"] == selected_name].iloc[0]
            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("이번 달 근무", f"{user_info['당월근무시간']} / 60시간")
                progress = min(float(user_info['당월근무시간']) / 60, 1.0)
                st.progress(progress)
            with col_b:
                st.metric("남은 연차", f"{user_info['잔여연차']}시간")

            st.divider()

            # (4) GPS 수집 및 업무 입력
            st.write("📍 위치 확인 중...")
            loc = get_geolocation()
            
            if loc:
                lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
                st.success("✅ 위치 확인 완료")

                st.subheader("📝 오늘의 활동 기록")
                work_types = st.multiselect("업무 종류:", ["상담", "홍보", "환경정비", "교육", "기타"])
                work_memo = st.text_area("상세 내용을 적어주세요:", placeholder="예: 어르신 3명 상담 완료")

                # (5) 출퇴근 버튼
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 출근하기", use_container_width=True):
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        summary = f"[{', '.join(work_types)}] {work_memo}"
                        log_sheet.append_row([selected_name, now, "출근", lat, lon, summary, "대기"])
                        st.balloons()
                        st.info(f"출근 완료: {now}")
                
                with col2:
                    if st.button("🏠 퇴근하기", use_container_width=True):
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        summary = f"[{', '.join(work_types)}] {work_memo}"
                        log_sheet.append_row([selected_name, now, "퇴근", lat, lon, summary, "대기"])
                        st.warning(f"퇴근 완료: {now}")
            else:
                st.info("💡 위치 권한 허용이 필요합니다. 잠시만 기다려주시거나 새로고침 해주세요.")
        else:
            st.warning("⚠️ 시트 인증에 실패했습니다. 관리자 설정을 확인하세요.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

st.divider()
st.caption("관리자 승인 시 화면에 결과가 반영됩니다.")
