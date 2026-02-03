import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="근태/휴가 관리", layout="wide")

# --- 2. 디자인 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab"] { font-size: 20px; font-weight: bold; color: #888; }
    .stTabs [aria-selected="true"] { color: #333 !important; border-bottom-color: #333 !important; }

    /* 휴가 박스 스타일 */
    .vacation-container { display: flex; gap: 10px; margin-bottom: 20px; }
    .vacation-box {
        flex: 1; background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #F0F0F0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .vacation-box.active { background-color: #EBF5FF; border: 1px solid #C2E0FF; }
    .v-label { font-size: 14px; color: #666; margin-bottom: 8px; }
    .v-value { font-size: 20px; font-weight: bold; color: #333; }
    .v-value.blue { color: #1A73E8; }

    /* 캐릭터 프로그레스 바 */
    .char-progress-container {
        background: white; padding: 20px; border-radius: 15px; 
        margin-bottom: 30px; border: 1px solid #F0F0F0;
    }
    .char-msg-box {
        background: #EBF5FF; padding: 10px 15px; border-radius: 10px;
        font-size: 14px; color: #1A73E8; display: inline-block; margin-left: 10px;
    }

    /* 근태 시간 카드 */
    .time-card {
        background: white; padding: 30px; border-radius: 20px;
        text-align: center; border: 1px solid #EEE; margin-bottom: 20px;
    }
    .time-val { font-size: 38px; font-weight: bold; color: #222; }

    /* GPS 정보창 */
    .gps-info {
        background: #F1F3F4; padding: 15px; border-radius: 12px;
        font-size: 13px; color: #555; font-family: monospace;
        border: 1px solid #DDD; margin-top: 10px;
    }
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
st.title("근태 현황")

cho = st.radio("성씨 초성", ["전체", "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"], horizontal=True)
names = df_vacation['성함'].tolist() if not df_vacation.empty else []
filtered = names if cho == "전체" else [n for n in names if get_chosung(n) == cho]
selected_user = st.selectbox("본인 성함을 선택하세요", filtered if filtered else ["데이터 없음"])

st.divider()

# --- 5. 탭 구성 ---
tab_attendance, tab_vacation = st.tabs(["근태", "휴가"])

# --- [근태 탭] ---
with tab_attendance:
    now = datetime.now()
    st.write(f"📅 {now.strftime('%Y-%m-%d (%a) %H:%M:%S')}")
    
    if 'arrived' not in st.session_state: st.session_state.arrived = False
    if 'start_time' not in st.session_state: st.session_state.start_time = "-"

    st.markdown(f"""
        <div class="time-card">
            <div style="display:flex; justify-content:center; align-items:center; gap:30px;">
                <div><div style="color:#888; font-size:14px;">출근 시간</div><div class="time-val">{st.session_state.start_time}</div></div>
                <div style="font-size:30px; color:#EEE;">➔</div>
                <div><div style="color:#888; font-size:14px;">퇴근 시간</div><div class="time-val">-</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # --- GPS 및 지도 섹션 ---
    st.subheader("📍 현재 위치 확인")
    loc = get_geolocation()
    
    if loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        
        # 지도 표시
        df_loc = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(df_loc, zoom=15)
        
        # 위도 경도 텍스트 표시
        st.markdown(f"""
            <div class="gps-info">
                🛰️ <b>위도(Latitude):</b> {lat}<br>
                🛰️ <b>경도(Longitude):</b> {lon}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("GPS 위치 정보를 불러오는 중입니다. 브라우저의 위치 권한을 허용해 주세요.")

    st.write("") # 간격
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 출근하기", use_container_width=True, disabled=st.session_state.arrived or not loc):
            st.session_state.arrived = True
            st.session_state.start_time = datetime.now().strftime("%H:%M:%S")
            sheet_attendance.append_row([selected_user, now.strftime("%Y-%m-%d"), st.session_state.start_time, "", "출근", "", lat, lon])
            st.rerun()
    with col2:
        if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.arrived):
            st.session_state.arrived = False
            st.session_state.start_time = "-"
            st.success("고생하셨습니다!")

# --- [휴가 탭] ---
with tab_vacation:
    st.header("휴가 관리")
    if not df_vacation.empty and selected_user in df_vacation['성함'].values:
        u = df_vacation[df_vacation['성함'] == selected_user].iloc[0]
        v_total = to_num(u.get('총연차', 0))
        v_used = to_num(u.get('사용연차', 0))
        v_rem = to_num(u.get('잔여연차', 0))
        
        st.markdown(f"""
            <div class="vacation-container">
                <div class="vacation-box active">
                    <div style="font-size:30px;">🏖️</div>
                    <div class="v-label">잔여 연차</div>
                    <div class="v-value blue">{int(v_rem)}d</div>
                </div>
                <div class="vacation-box">
                    <div style="font-size:30px;">📅</div>
                    <div class="v-label">사용 연차</div>
                    <div class="v-value">{int(v_used)}d</div>
                </div>
                <div class="vacation-box">
                    <div style="font-size:30px;">✈️</div>
                    <div class="v-label">총 연차</div>
                    <div class="v-value">{int(v_total)}d</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        prog_ratio = min(v_used / v_total, 1.0) if v_total > 0 else 0.0
        st.markdown(f"""
            <div class="char-progress-container">
                <div style="display:flex; align-items:center; margin-bottom:10px;">
                    <span style="font-size:40px;">🐰</span>
                    <div class="char-msg-box">연차 현황을 확인하세요!</div>
                </div>
        """, unsafe_allow_html=True)
        st.progress(prog_ratio)
        st.markdown(f"<div style='text-align:right; color:#888; font-size:12px;'>{int(prog_ratio*100)}% ({int(v_used)} / {int(v_total)})</div></div>", unsafe_allow_html=True)

    if st.button("➕ 휴가 신청하기", use_container_width=True):
        @st.dialog("새 휴가 신청")
        def apply_form():
            st.date_input("휴가 일자")
            st.selectbox("휴가 종류", ["연차", "반차", "병가"])
            if st.button("신청서 제출"):
                st.success("신청되었습니다.")
                st.rerun()
        apply_form()
