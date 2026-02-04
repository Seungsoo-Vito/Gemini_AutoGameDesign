import streamlit as st
from google import genai

# 1. 페이지 설정
st.set_page_config(page_title="Game PM AI Assistant", page_icon="🎮")

# API 키 설정
API_KEY = "AIzaSyDsZOnRpEaT6DYRmBtPn2GF_Zg6HmD8FBM"

# 최신 SDK 클라이언트 생성
try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"클라이언트 생성 실패: {e}")

# 2. 모델 자동 탐색 기능
@st.cache_resource
def find_working_model():
    try:
        models = client.models.list()
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                if "gemini-1.5-flash" in m.name:
                    return m.name
        return "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

target_model = find_working_model()

# 3. 웹 화면 UI
st.title("🎮 Game Idea to GDD")
st.write("베테랑 게임 PM의 시각으로 기획서 초안을 작성합니다.")
st.divider()

col1, col2 = st.columns(2)
with col1:
    genre = st.selectbox("게임 장르", ["방치형 RPG", "서브컬처 수집형", "오픈월드", "로그라이크", "매치3 퍼즐"])
    target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])
with col2:
    art_style = st.selectbox("아트 스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼"])
    keywords = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 덱빌딩")

# 4. 생성 로직
if st.button("기획서 초안 생성 ✨", type="primary"):
    if not keywords:
        st.warning("핵심 키워드를 입력해 주세요.")
    else:
        with st.spinner("AI PM이 기획서를 작성 중입니다..."):
            # 💡 여기서 'prompt' 변수를 먼저 정의합니다!
            input_prompt = f"""
            당신은 10년 경력의 게임 개발 PM입니다. 
            다음 조건을 바탕으로 전문적인 게임 기획서 초안(GDD)을 한국어로 작성하세요.
            
            - 장르: {genre}
            - 타겟: {target}
            - 키워드: {keywords}
            - 아트 스타일: {art_style}
            
            [문서 구조]
            1. Concept Summary: 한 줄 핵심 요약
            2. World Building: 세계관 및 주요 설정
            3. Core Loop: [실행 - 보상 - 성장] 순환 구조
            4. Key Features: 핵심 재미 요소 3가지
            5. Monetization: 글로벌 시장에 적합한 BM 제안
            """
            
            try:
                # 💡 정의된 input_prompt를 사용합니다.
                response = client.models.generate_content(
                    model=target_model,
                    contents=input_prompt
                )
                
                st.markdown("---")
                st.markdown("### 📝 생성된 기획서 초안")
                st.markdown(response.text)
                
            except Exception as e:
                # 💡 만약 404가 나면 gemini-pro로 마지막 시도
                try:
                    response = client.models.generate_content(
                        model="gemini-flash-latest",
                        contents=input_prompt
                    )
                    st.markdown(response.text)
                except Exception as final_error:
                    st.error(f"생성 중 오류가 발생했습니다: {final_error}")

st.caption("© 2026 Game PM AI Assistant")