import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation  # GPS 기능을 위한 도구

st.set_page_config(page_title="근태관리 시스템", layout="wide")

# --- CSS 디자인 (이전과 동일) ---
st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: bold; color: #1E3A8A; }
    .status-box { background-color: #F3F4F6; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #E5E7EB; }
    .time-text { font-size: 24px; font-weight: bold; color: #2563EB; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 근태현황</div>', unsafe_allow_html=True)
st.markdown('<div class="business-unit">🏢 실버 복지 사업단</div>', unsafe_allow_html=True)

# --- GPS 위치 가져오기 섹션 ---
st.subheader("📍 현재 위치 인증")
col_gps, col_map = st.columns([1, 2])

with col_gps:
    st.write("출근 전 위치 인증이 필요합니다.")
    loc = get_geolocation() # 브라우저 GPS 요청
    
    if loc:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        st.success(f"✅ 위치 확인 완료")
        st.write(f"위도: {lat:.4f} / 경도: {lon:.4f}")
    else:
        st.warning("위치 정보 권한을 허용해 주세요.")

with col_map:
    if loc:
        # 구글맵/지도 표시용 데이터프레임
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_data) # 스트림릿 내장 지도 (구글맵 기반)

st.divider()

# --- 출퇴근 섹션 (GPS가 확인되어야 출근 버튼 활성화) ---
col1, col2 = st.columns(2)

if 'is_arrived' not in st.session_state:
    st.session_state.is_arrived = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = "--:--"

# GPS 인증 여부에 따른 버튼 활성화 로직
gps_ready = True if loc else False

with col1:
    st.markdown(f'<div class="status-box"><b>출근 시간</b><br><span class="time-text">{st.session_state.start_time}</span></div>', unsafe_allow_html=True)
    
    btn_label = "🚀 출근하기" if gps_ready else "📍 위치 인증 필요"
    if st.button(btn_label, use_container_width=True, disabled=st.session_state.is_arrived or not gps_ready):
        st.session_state.is_arrived = True
        st.session_state.start_time = datetime.now().strftime("%H:%M")
        # 여기서 구글 시트에 [성함, 날짜, 시간, 위도, 경도]를 저장하게 됩니다.
        st.rerun()

with col2:
    st.markdown('<div class="status-box"><b>퇴근 시간</b><br><span class="time-text">--:--</span></div>', unsafe_allow_html=True)
    if st.button("🏠 퇴근하기", use_container_width=True, disabled=not st.session_state.is_arrived):
        st.session_state.is_arrived = False
        st.rerun()

# --- 이후 연차/알림 섹션은 이전과 동일하게 유지 ---
