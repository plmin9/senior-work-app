import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="근태/휴가 관리", layout="wide")

# --- 2. 디자인 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .time-card {
        background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #EEE; margin-bottom: 15px;
    }
    .time-val { font-size: 32px; font-weight: bold; color: #222; }
    .location-box { background: white; padding: 15px; border-radius: 12px; border: 1px solid #E0E0E0; height: 100%; }
    .gps-value { font-size: 15px; color: #1A73E8; font-family: monospace; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 구글 시트 연결 ---
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

# --- 4. 세션 상태 유지 (매우 중요) ---
if 'arrived' not in st.session_state: st.session_state.arrived = False
if 'disp_start' not in st.session_state: st.session_state.disp_start = "-"
if 'disp_end' not in st.session_state: st.session_state.disp_end = "-"

def to_num(val):
    try: return float(str(val).replace(',', ''))
    except: return 0.0

def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

# --- 5. 메인 화면 ---
st.markdown("## 🏢 스마트 근태관리")
cho = st.radio("성씨 초성 선택", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True)
names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered = names if cho == "전체" else [n for n in names if get_chosung(n) == cho]
selected_user = st.selectbox("본인 성함을 선택하세요", filtered if filtered else ["데이터 없음"])

st.divider()

tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

with tab_attendance:
    now = datetime.now()
    st.write(f"📅 {now.strftime('%Y년 %m월 %d일 %H:%M')}")
    
    # [수정] 카드 디자인에서 세션 상태의 시간을 실시간으로 보여줌
    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:center; align-items:center; gap:20px;">
                <div><div style="color:#888; font-size:12px;">출근 시간</div><div class="time-val">{st.session_state.disp_start}</div></div>
                <div style="font-size:24px; color:#DDD;">➔</div>
                <div><div style="color:#888; font-size:12px;">퇴근 시간</div><div class="time-val">{st.session_state.disp_end}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    loc = get_geolocation()
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # 출근 시: 시간을 세션에 고정
        if st.button("🚀 출근하기", use_container_width=True, type="primary", disabled=st.session_state.arrived or not loc):
            st.session_state.disp_start = datetime.now().strftime("%H:%M:%S")
            st.session_state.arrived = True
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.disp_start, "", "출근", "", lat, lon])
            st.rerun()

    with col_btn2:
        # 퇴근 시: 출근 시간을 유지하면서 퇴근 시간만 추가
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived or st.session_state.disp_end != "-"):
            st.session_state.disp_end = datetime.now().strftime("%H:%M:%S")
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", st.session_state.disp_end, "퇴근", "", "", ""])
            st.success("퇴근 기록 완료! 고생하셨습니다.")
            # 퇴근 후에는 시간을 리셋하지 않고 화면에 보여줌 (필요 시 st.rerun 제거)
            st.rerun()

    st.divider()

    st.markdown("##### 📍 현재 위치 확인")
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        col_map, col_gps = st.columns([1.5, 1])
        with col_map: st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14)
        with col_gps:
            st.markdown(f"""
                <div class="location-box">
                    <div style="font-size:14px; color:#666; font-weight:bold;">🛰️ 위도</div><div class="gps-value">{lat:.6f}</div>
                    <div style="margin-top:10px; font-size:14px; color:#666; font-weight:bold;">🛰️ 경도</div><div class="gps-value">{lon:.6f}</div>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("위치 정보를 수신 중입니다...")

# --- 휴가 탭 생략 (기존 기능 유지) ---
with tab_vacation:
    st.subheader("🏖️ 나의 휴가 현황")
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_total, v_used, v_rem = to_num(u.get('총연차', 0)), to_num(u.get('사용연차', 0)), to_num(u.get('잔여연차', 0))
        st.markdown(f"**잔여 연차: {int(v_rem)}일** / 사용: {int(v_used)}일")
        st.progress(min(v_used / v_total, 1.0) if v_total > 0 else 0.0)
    if st.button("➕ 휴가 신청하기", use_container_width=True):
        st.info("신청 팝업이 준비 중입니다.")
