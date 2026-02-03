import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="근태/휴가 관리", layout="wide")

# --- 2. 구글 시트 연결 ---
@st.cache_resource
def get_gspread_client():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds_info = {
            "type": "service_account", "project_id": s["project_id"],
            "private_key": s["private_key"].replace("\\n", "\n"),
            "client_email": s["service_account_email"],
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

client = get_gspread_client()
if client:
    s = st.secrets["connections"]["gsheets"]
    sheet_id = s["spreadsheet"].split("/d/")[1].split("/")[0]
    doc = client.open_by_key(sheet_id)
    sheet_attendance = doc.worksheet("근태기록")
    sheet_vacation = doc.worksheet("연차관리")
    df_vacation = pd.DataFrame(sheet_vacation.get_all_records())
else: st.stop()

# --- 3. 세션 상태 관리 (화면 표시용) ---
if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"
if 'arrived' not in st.session_state: st.session_state.arrived = False

# --- 4. 메인 화면 ---
st.title("🏢 스마트 근태관리")

# 성함 선택 (기존 로직 동일)
all_names = df_vacation['성함'].tolist() if not df_vacation.empty else []
selected_user = st.selectbox("본인 성함을 선택하세요", all_names)

st.divider()

# --- 5. 근태 관리 탭 ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    
    # 시간 표시 카드
    st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #EEE;">
            <div style="display:flex; justify-content:center; align-items:center; gap:20px;">
                <div><div style="color:#888;">출근 시간</div><div style="font-size:28px; font-weight:bold;">{st.session_state.disp_start}</div></div>
                <div style="font-size:24px; color:#DDD;">➔</div>
                <div><div style="color:#888;">퇴근 시간</div><div style="font-size:28px; font-weight:bold;">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    loc = get_geolocation()
    col1, col2 = st.columns(2)

    with col1:
        # [출근하기] 클릭 시
        if st.button("🚀 출근하기", use_container_width=True, type="primary", 
                     disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            # 시트에 새로운 줄 추가 (출근 기록)
            # 순서: 성함, 날짜, 출근시간, 퇴근시간, 상태, 비고, 위도, 경도
            sheet_attendance.append_row([selected_user, today_date, st.session_state.disp_start, "", "출근", "정상출근", lat, lon])
            st.rerun()

    with col2:
        # [퇴근하기] 클릭 시
        if st.button("🏠 퇴근하기", use_container_width=True, 
                     disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            
            # 시트에 새로운 줄 추가 (퇴근 기록) - 출근 시간과 겹치지 않게 '퇴근시간' 열에 기록
            # 시트의 세 번째 열은 비우고 네 번째 열(퇴근시간)에 저장
            sheet_attendance.append_row([selected_user, today_date, "", st.session_state.disp_end, "퇴근", "정상퇴근", "", ""])
            st.success("퇴근 기록이 완료되었습니다!")
            st.rerun()

    st.divider()
    # 위치/지도 로직 생략 (기존과 동일)
