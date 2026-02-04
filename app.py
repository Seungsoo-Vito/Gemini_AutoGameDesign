import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# 1. 페이지 설정 (넓은 화면 모드 적용)
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# API 설정
API_KEY = "AIzaSyDsZOnRpEaT6DYRmBtPn2GF_Zg6HmD8FBM"
genai.configure(api_key=API_KEY)

# 장르별 대표 이미지 매핑
GENRE_IMAGES = {
    "방치형 RPG": "http://googleusercontent.com/image_collection/image_retrieval/18046117240916034651",
    "서브컬처 수집형": "http://googleusercontent.com/image_collection/image_retrieval/17222878873756685304",
    "오픈월드": "http://googleusercontent.com/image_collection/image_retrieval/12652131905489824931",
    "로그라이크": "http://googleusercontent.com/image_collection/image_retrieval/17019173616965837555",
    "매치3 퍼즐": "http://googleusercontent.com/image_collection/image_retrieval/13557754272071633945"
}

# 세션 상태 초기화
if 'gdd_result' not in st.session_state:
    st.session_state['gdd_result'] = None

# --- 📄 PDF 생성 함수 ---
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.add_font('Nanum', '', 'NanumGothic-Regular.ttf')
        pdf.set_font('Nanum', size=11)
    except:
        pdf.set_font('Arial', size=11)
    
    # 텍스트 출력 및 자동 줄바꿈
    pdf.multi_cell(0, 8, txt=text)
    return pdf.output()

# 2. 웹 화면 UI 구성
st.title("🚀 비토쨩 자동 기획서 Pro")
st.write("전문 PM의 분석과 컨셉 이미지가 포함된 고품격 기획서 생성기")
st.divider()

# 사이드바 설정
with st.sidebar:
    st.header("📋 기획 옵션")
    detail_level = st.select_slider("내용 상세도", options=["표준", "상세", "전문가"])
    st.info(f"선택된 상세도: {detail_level}")

# 메인 입력창
col1, col2 = st.columns([1, 1])

with col1:
    genre = st.selectbox("게임 장르", list(GENRE_IMAGES.keys()))
    target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])

with col2:
    art_style = st.selectbox("아트 스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크"])
    keywords = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 덱빌딩")

# 3. 생성 로직
if st.button("전문 기획서 및 컨셉 아트 생성 ✨", type="primary"):
    if not keywords:
        st.warning("핵심 키워드를 입력해 주세요.")
    else:
        with st.spinner("PM AI가 시장 데이터와 기획안을 분석 중입니다..."):
            prompt = f"""
            당신은 15년 경력의 시니어 게임 PM이자 디렉터입니다. 
            다음 조건을 바탕으로 투자자에게 제출할 수준의 전문적인 GDD 초안을 한국어로 작성하세요.
            문서 수준은 '{detail_level}'에 맞춰 매우 구체적이고 논리적으로 작성해야 합니다.
            
            [조건]
            - 장르: {genre} / 타겟 국가: {target} / 키워드: {keywords} / 아트 스타일: {art_style}
            
            [필수 포함 구조]
            1. Concept Summary: 게임의 High-Concept와 시장 경쟁력 분석 (USP).
            2. World Building & Story: 세계관의 깊이 있는 설정과 유저가 몰입할 수 있는 시나리오 핵심.
            3. Core Loop: [Core Action - Reward - Meta Game]으로 이어지는 선순환 구조 상세 설명.
            4. Key Systems: 기획자가 즉시 구현 가능할 정도의 수치적 예시가 포함된 3가지 핵심 시스템.
            5. Business Model: 타겟 국가 유저의 결제 성향을 고려한 정교한 BM 및 매출 방어 전략.
            6. UI/UX Concept: 유저가 느낄 첫인상과 주요 화면 동선 가이드.
            """
            
            try:
                model = genai.GenerativeModel('gemini-flash-latest')
                response = model.generate_content(prompt)
                st.session_state['gdd_result'] = response.text
                
            except Exception as e:
                st.error(f"생성 중 오류 발생: {e}")

# 4. 결과 출력 섹션
if st.session_state['gdd_result']:
    st.divider()
    
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("🖼️ Game Concept Art")
        # ✅ use_column_width를 use_container_width로 수정하였습니다.
        st.image(GENRE_IMAGES[genre], caption=f"{genre} 스타일 컨셉 아트 프리뷰", use_container_width=True)
        
        # PDF 다운로드 버튼
        try:
            pdf_bytes = create_pdf(st.session_state['gdd_result'])
            st.download_button(
                label="📄 기획서 PDF 다운로드",
                data=bytes(pdf_bytes),
                file_name=f"GDD_Pro_{keywords}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF 생성 실패: {e}")

    with res_col2:
        st.subheader("📝 기획서 본문")
        st.markdown(st.session_state['gdd_result'])

st.caption("비토쨩이 테스트로 만들었단다. © 2026 Game PM AI Assistant")