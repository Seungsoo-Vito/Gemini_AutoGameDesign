import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# 1. 페이지 설정
st.set_page_config(page_title="비토쨩 자동 기획서", page_icon="🎮")

# --- 🔒 API 설정 ---
# 승수님, 만약 이 코드로도 404가 뜨면 Google AI Studio에서 
# 'Create API key in a NEW project'로 키를 새로 발급받아 교체해 보세요.
API_KEY = "AIzaSyDsZOnRpEaT6DYRmBtPn2GF_Zg6HmD8FBM"
genai.configure(api_key=API_KEY)

# 2. 웹 화면 UI
st.title("비토쨩 자동 기획서")
st.write("제미나이로 기획서 만들어 PDF까지 추출하기")
st.divider()

# 세션 상태 초기화 (결과 유지용)
if 'gdd_result' not in st.session_state:
    st.session_state['gdd_result'] = None

col1, col2 = st.columns(2)
with col1:
    genre = st.selectbox("게임 장르", ["방치형 RPG", "서브컬처 수집형", "오픈월드", "로그라이크", "매치3 퍼즐"])
    target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])
with col2:
    art_style = st.selectbox("아트 스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼"])
    keywords = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 덱빌딩")

# --- 📄 PDF 생성 함수 ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    try:
        # 승수님이 확인하신 폰트 파일명 적용
        pdf.add_font('Nanum', '', 'NanumGothic-Regular.ttf')
        pdf.set_font('Nanum', size=11)
    except:
        pdf.set_font('Arial', size=11)
        st.warning("폰트 파일을 찾을 수 없어 한글이 깨질 수 있습니다. 폴더에 .ttf 파일이 있는지 확인하세요.")

    # 텍스트 출력 및 자동 줄바꿈
    pdf.multi_cell(0, 8, txt=text)
    return pdf.output()

# 3. 생성 로직
if st.button("기획서 초안 생성 ✨", type="primary"):
    if not keywords:
        st.warning("핵심 키워드를 입력해 주세요.")
    else:
        with st.spinner("AI PM이 기획서를 작성 중입니다..."):
            prompt = f"""
            너는 10년 경력의 게임 PM이야. 다음 조건으로 전문적인 GDD 초안을 한국어로 써줘.
            - 장르: {genre} / 타겟: {target} / 키워드: {keywords} / 아트: {art_style}
            
            [구조] 1. Concept Summary 2. World Building 3. Core Loop 4. Key Features 5. Monetization
            """
            
            try:
                # 💡 모델 선언 시점과 호출 방식을 분리하여 안정성을 높임
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                if response.text:
                    st.session_state['gdd_result'] = response.text
                else:
                    st.error("AI가 빈 답변을 보냈습니다. 다시 시도해 주세요.")

            except Exception as e:
                # 만약 404가 나면 다른 모델명으로 재시도
                try:
                    model = genai.GenerativeModel('gemini-flash-latest')
                    response = model.generate_content(prompt)
                    st.session_state['gdd_result'] = response.text
                except:
                    st.error(f"상세 에러: {e}")

# 4. 결과 출력 및 PDF 다운로드
if st.session_state['gdd_result']:
    st.markdown("---")
    st.markdown("### 📝 생성된 기획서 초안")
    st.markdown(st.session_state['gdd_result'])
    
    try:
        pdf_bytes = create_pdf(st.session_state['gdd_result'])
        st.download_button(
            label="📄 PDF로 다운로드",
            data=bytes(pdf_bytes),
            file_name=f"GDD_{keywords}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF 생성 실패: {e}")

st.caption("비토쨩이 테스트로 만들었단다.")