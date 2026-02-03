import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="근태/휴가 관리", layout="wide")

# --- 2. 디자인 CSS (UI 최적화) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab-list"] { background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab"] { font-size: 18px; font-weight: bold; }

    /* 출퇴근 카드 */
    .time-card {
        background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #EEE; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .time-val { font-size: 32px; font-weight: bold; color: #222; }

    /* 위치 정보 박스 */
    .location-box {
        background: white; padding: 15px; border-radius: 12px;
        border: 1px solid #E0E0E0; height: 100%;
    }
    .gps-label { font-size: 14px; color: #666; font-weight: bold; margin-bottom: 5px; }
    .gps-value { font-size: 15px; color: #1A73E8; font-family: monospace; }

    /* 휴가 박스 */
    .vacation-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .vacation-box {
        flex: 1; background: white; padding: 15px; border-radius: 12px;
        text-align: center; border: 1px solid #F0F0F0;
    }
    .vacation-box.active { background-color: #EBF5FF; border: 1px solid #C2E0FF; }
    .v-label { font-size: 13px; color: #666; }
    .v-value { font-size: 18px; font-weight: bold; color: #333; }
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

def to_num(val):
    try: return float(str(val).replace(',', ''))
    except: return 0.0

def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text: return ""
    char_code = ord(str(text)[0]) - 0xAC00
    return CHOSUNG_LIST[char_code // 588] if 0 <= char_code <= 11171 else str(text)[0].upper()

# --- 4. 메인 화면 ---
st.markdown("## 🏢 스마트 근태관리")

# 본인 선택
cho = st.radio("성씨 초성 선택", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True)
names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered = names if cho == "전체" else [n for n in names if get_chosung(n) == cho]
selected_user = st.selectbox("본인 성함을 선택하세요", filtered if filtered else ["데이터 없음"])

st.divider()

# --- 5. 탭 구성 ---
tab_attendance, tab_vacation = st.tabs(["🕒 근태관리", "🏖️ 휴가관리"])

# --- [근태 탭] ---
with tab_attendance:
    now = datetime.now()
    st.write(f"📅 {now.strftime('%Y년 %m월 %d일 %H:%M')}")
    
    if 'arrived' not in st.session_state: st.session_state.arrived = False
    if 'start_time' not in st.session_state: st.session_state.start_time = "-"

    # 1. 출퇴근 시간 표시 카드
    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:center; align-items:center; gap:20px;">
                <div><div style="color:#888; font-size:12px;">출근</div><div class="time-val">{st.session_state.start_time}</div></div>
                <div style="font-size:24px; color:#DDD;">➔</div>
                <div><div style="color:#888; font-size:12px;">퇴근</div><div class="time-val">-</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. 버튼 배치
    loc = get_geolocation()
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🚀 출근하기", use_container_width=True, type="primary", disabled=st.session_state.arrived or not loc):
            st.session_state.arrived = True
            st.session_state.start_time = datetime.now().strftime("%H:%M:%S")
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            # 구글 시트에 기록 (출근 행 추가)
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.start_time, "", "출근", "", lat, lon])
            st.rerun()

    with col_btn2:
        # 퇴근 버튼 클릭 시 동작 수정
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived):
            end_time = datetime.now().strftime("%H:%M:%S")
            # 구글 시트에 기록 (퇴근 행 추가)
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), "", end_time, "퇴근", "", "", ""])
            
            st.session_state.arrived = False
            st.session_state.start_time = "-"
            st.success("퇴근 기록이 완료되었습니다. 고생하셨습니다!")
            st.rerun()

    st.divider()

    # 3. 위치 정보
    st.markdown("##### 📍 현재 위치 확인")
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        col_map, col_gps = st.columns([1.5, 1])
        
        with col_map:
            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=14, use_container_width=True)
        
        with col_gps:
            st.markdown(f"""
                <div class="location-box">
                    <div class="gps-label">🛰️ 위도 (Latitude)</div>
                    <div class="gps-value">{lat:.6f}</div>
                    <div style="margin-top:10px;" class="gps-label">🛰️ 경도 (Longitude)</div>
                    <div class="gps-value">{lon:.6f}</div>
                    <hr style="margin:10px 0;">
                    <div style="font-size:12px; color:#28a745;">✔️ 위치 확인 완료</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("위치 정보를 수신 중입니다... 잠시만 기다려 주세요.")

# --- [휴가 탭] ---
with tab_vacation:
    st.subheader("🏖️ 나의 휴가 현황")
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_total, v_used, v_rem = to_num(u.get('총연차', 0)), to_num(u.get('사용연차', 0)), to_num(u.get('잔여연차', 0))
        
        st.markdown(f"""
            <div class="vacation-container">
                <div class="vacation-box active"><div class="v-label">잔여</div><div class="v-value" style="color:#1A73E8;">{int(v_rem)}d</div></div>
                <div class="vacation-box"><div class="v-label">사용</div><div class="v-value">{int(v_used)}d</div></div>
                <div class="vacation-box"><div class="v-label">총</div><div class="v-value">{int(v_total)}d</div></div>
            </div>
        """, unsafe_allow_html=True)
        
        prog = min(v_used / v_total, 1.0) if v_total > 0 else 0.0
        st.progress(prog)
        st.caption(f"연차 사용률: {int(prog*100)}%")

    if st.button("➕ 휴가 신청하기", use_container_width=True):
        @st.dialog("새 휴가 신청")
        def apply_form():
            v_date = st.date_input("날짜 선택")
            v_type = st.selectbox("종류", ["연차", "오전반차", "오후반차", "병가"])
            if st.button("제출"):
                # 휴가 신청 시에도 구글 시트에 기록
                sheet_attendance.append_row([selected_user, v_date.strftime("%Y-%m-%d"), "", "", v_type, "휴가신청", "", ""])
                st.success("신청이 완료되었습니다.")
                st.rerun()
        apply_form()

st.write("<br><br>", unsafe_allow_html=True)
st.caption("실버 복지 사업단 v2.9")
