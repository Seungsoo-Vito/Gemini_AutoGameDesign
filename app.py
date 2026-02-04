import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import re

# 1. 페이지 설정 (넓은 화면 모드 적용)
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# API 설정
API_KEY = "AIzaSyDsZOnRpEaT6DYRmBtPn2GF_Zg6HmD8FBM"
genai.configure(api_key=API_KEY)

# 레퍼런스 이미지 키워드 매핑 (Unsplash API 활용)
REFERENCE_IMAGES = {
    "방치형 RPG": "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&q=80&w=800",
    "서브컬처 수집형": "https://images.unsplash.com/photo-1614728263952-84ea256f9679?auto=format&fit=crop&q=80&w=800",
    "오픈월드": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&q=80&w=800",
    "로그라이크": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&q=80&w=800",
    "매치3 퍼즐": "https://images.unsplash.com/photo-1605870445919-838d190e8e1b?auto=format&fit=crop&q=80&w=800",
    "World Building": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&q=80&w=800",
    "Core Loop": "https://images.unsplash.com/photo-1558483306-0504655ae27d?auto=format&fit=crop&q=80&w=800",
    "UI/UX": "https://images.unsplash.com/photo-1586717791821-3f44a563eb4c?auto=format&fit=crop&q=80&w=800"
}

# 세션 상태 초기화
if 'gdd_result' not in st.session_state:
    st.session_state['gdd_result'] = None

# --- 📄 PDF 생성 함수 개선 (오류 수정 및 최적화) ---
def create_pdf(text, keywords):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 기본 여백 설정
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    
    # 폰트 설정
    try:
        pdf.add_font('Nanum', '', 'NanumGothic-Regular.ttf')
        pdf.set_font('Nanum', size=16)
    except:
        pdf.set_font('Arial', 'B', 16)
        st.warning("나눔고딕 폰트를 찾을 수 없어 기본 폰트로 대체됩니다.")

    # 문서 제목
    pdf.cell(0, 15, f"Game Design Document: {keywords}", ln=True, align='C')
    pdf.ln(5)

    # 텍스트 정제 (마크다운 기호 제거 및 인코딩 안전 처리)
    clean_text = text.replace('###', '').replace('##', '').replace('#', '')
    clean_text = clean_text.replace('**', '').replace('*', '')
    clean_text = clean_text.replace('\t', '    ') # 탭 문자 공백 처리
    
    try:
        pdf.set_font('Nanum', size=11)
    except:
        pdf.set_font('Arial', size=11)

    # 줄바꿈 처리 및 텍스트 출력
    # 에러 방지를 위해 multi_cell의 너비를 명시적으로 지정 (0 대신 실질적 너비 계산)
    page_width = pdf.w - 2 * pdf.l_margin
    
    lines = clean_text.split('\n')
    for line in lines:
        if line.strip() == "":
            pdf.ln(4)
        else:
            # fpdf2의 multi_cell 안정성을 위해 문자열 앞뒤 공백 제거 후 출력
            pdf.multi_cell(page_width, 8, txt=line.strip())
            
    return pdf.output()

# 2. 웹 화면 UI 구성
st.title("🚀 비토쨩 자동 기획서 Pro")
st.write("전문 PM의 분석과 시각적 레퍼런스가 포함된 고품격 기획서 생성기")
st.divider()

# 사이드바 설정
with st.sidebar:
    st.header("📋 기획 옵션")
    detail_level = st.select_slider("내용 상세도", options=["표준", "상세", "전문가"])
    st.info(f"선택된 상세도: {detail_level}")

# 메인 입력창
col1, col2 = st.columns([1, 1])

with col1:
    genre = st.selectbox("게임 장르", list(REFERENCE_IMAGES.keys())[:5])
    target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])

with col2:
    art_style = st.selectbox("아트 스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크"])
    keywords = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 덱빌딩")

# 3. 생성 로직
if st.button("전문 기획서 및 레퍼런스 분석 생성 ✨", type="primary"):
    if not keywords:
        st.warning("핵심 키워드를 입력해 주세요.")
    else:
        with st.spinner("PM AI가 기획안과 시각적 레퍼런스를 매칭 중입니다..."):
            prompt = f"""
            당신은 15년 경력의 시니어 게임 PM이자 디렉터입니다. 
            다음 조건을 바탕으로 투자자에게 제출할 수준의 전문적인 GDD 초안을 한국어로 작성하세요.
            문서 수준은 '{detail_level}'에 맞춰 매우 구체적이고 논리적으로 작성해야 합니다.
            
            [조건]
            - 장르: {genre} / 타겟 국가: {target} / 키워드: {keywords} / 아트 스타일: {art_style}
            
            [필수 포함 구조]
            1. Concept Summary: 게임의 High-Concept와 시장 경쟁력 분석 (USP).
            2. World Building & Story: 세계관의 깊이 있는 설정.
            3. Core Loop: 핵심 순환 구조 상세 설명.
            4. Key Systems: 구체적인 시스템 설계.
            5. Business Model: 매출 전략.
            6. UI/UX Concept: 유저 경험 가이드.
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
    
    # PDF 다운로드 버튼 상단 배치
    try:
        pdf_bytes = create_pdf(st.session_state['gdd_result'], keywords)
        st.download_button(
            label="📄 완성된 기획서 PDF 다운로드",
            data=bytes(pdf_bytes),
            file_name=f"GDD_Pro_{keywords}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"PDF 생성 중 문제가 발생했습니다: {e}")

    # 기획서 본문 및 이미지 통합 출력
    st.subheader("📝 기획서 본문 및 시각적 레퍼런스")
    
    # 텍스트 섹션별로 나누어 이미지 삽입 (단순 파싱 로직)
    sections = st.session_state['gdd_result'].split('\n\n')
    
    for i, section in enumerate(sections):
        st.markdown(section)
        
        # 특정 섹션 뒤에 레퍼런스 이미지 삽입
        if i == 0: # Concept Summary 뒤
            st.image(REFERENCE_IMAGES[genre], caption=f"레퍼런스: {genre} 컨셉 비주얼", width=700)
        elif "World Building" in section or i == 2:
            st.image(REFERENCE_IMAGES["World Building"], caption="레퍼런스: 세계관 분위기 가이드", width=700)
        elif "Core Loop" in section:
            st.image(REFERENCE_IMAGES["Core Loop"], caption="레퍼런스: 게임 시스템 흐름 예시", width=700)
        elif "UI/UX" in section:
            st.image(REFERENCE_IMAGES["UI/UX"], caption="레퍼런스: 인터페이스 및 사용자 경험 설계", width=700)

st.caption("비토쨩이 테스트로 만들었단다. © 2026 Game PM AI Assistant")