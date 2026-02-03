import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="노인일자리 관리", layout="wide")
st.title("👵 노인일자리 출퇴근 시스템")

try:
    # Streamlit의 공식 구글 시트 커넥션을 사용합니다.
    # 이 방식은 내부적으로 키 로딩 에러를 방지하도록 설계되어 있습니다.
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 데이터를 읽어옵니다. (시트 URL은 Secrets에 설정한 값을 사용)
    df = conn.read()
    
    st.success("✅ 구글 시트 연결에 성공했습니다!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("❌ 연결 오류가 발생했습니다.")
    st.code(str(e))
    st.info("Secrets 설정의 형식이 새로운 표준에 맞는지 확인해주세요.")
