import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import requests
import base64
import json

# 1. 페이지 설정 (넓은 화면 모드 적용)
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# API 설정 (환경에서 제공하는 키 사용을 위해 빈 문자열로 설정하거나 기존 변수 유지)
API_KEY = "AIzaSyBpUR0gl_COhxbFPWxTiW6JJMuGgDF4Ams"
genai.configure(api_key=API_KEY)

# --- 🎨 이미지 생성 함수 (Imagen 4.0 사용) ---
def generate_game_image(prompt_text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {
        "instances": [{"prompt": prompt_text}],
        "parameters": {"sampleCount": 1}
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        if "predictions" in result:
            return result["predictions"][0]["bytesBase64Encoded"]
    except Exception as e:
        return None
    return None

# 세션 상태 초기화
if 'gdd_result' not in st.session_state:
    st.session_state['gdd_result'] = None
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'generated_images' not in st.session_state:
    st.session_state['generated_images'] = {}

# --- 📄 PDF 생성 함수 ---
def create_pdf(text, keywords):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    
    try:
        pdf.add_font('Nanum', '', 'NanumGothic-Regular.ttf')
        pdf.set_font('Nanum', size=16)
    except:
        pdf.set_font('Arial', 'B', 16)

    pdf.cell(0, 15, f"Game Design Document: {keywords}", ln=True, align='C')
    pdf.ln(5)

    clean_text = text.replace('###', '').replace('##', '').replace('#', '').replace('**', '').replace('*', '')
    
    try:
        pdf.set_font('Nanum', size=11)
    except:
        pdf.set_font('Arial', size=11)

    page_width = pdf.w - 2 * pdf.l_margin
    lines = clean_text.split('\n')
    for line in lines:
        if line.strip() == "":
            pdf.ln(4)
        else:
            pdf.multi_cell(page_width, 8, txt=line.strip())
            
    return pdf.output()

# 2. 웹 화면 UI 구성
st.title("비토쨩 자동 기획서")
st.write("제미나이로 기획서 만들기")
st.divider()

# 사이드바 설정
with st.sidebar:
    st.header("📋 기획 옵션")
    detail_level = st.select_slider("내용 상세도", options=["표준", "상세", "전문가"])
    
    st.divider()
    st.header("🕒 기획 히스토리")
    if not st.session_state['history']:
        st.write("생성된 기록이 없습니다.")
    else:
        for i, item in enumerate(reversed(st.session_state['history'])):
            if st.button(f"📄 {item['keywords']} ({item['genre']})", key=f"hist_{i}"):
                st.session_state['gdd_result'] = item['content']
                st.session_state['generated_images'] = item.get('images', {})
        if st.button("히스토리 비우기"):
            st.session_state['history'] = []
            st.rerun()

# 메인 입력창
col1, col2 = st.columns([1, 1])
with col1:
    genre = st.selectbox("게임 장르", ["방치형 RPG", "서브컬처 수집형", "오픈월드", "로그라이크", "매치3 퍼즐", "액션 어드벤처"])
    target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])
with col2:
    art_style = st.selectbox("아트 스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크"])
    keywords = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 덱빌딩")

# 3. 생성 로직
if st.button("기획서 및 AI 이미지 ✨", type="primary"):
    if not keywords:
        st.warning("핵심 키워드를 입력해 주세요.")
    else:
        with st.spinner("AI PM이 기획서를 작성하고 이미지를 생성 중입니다..."):
            # 기획서 텍스트 생성
            prompt = f"""
            당신은 15년 경력의 게임 디렉터입니다. 다음 조건으로 전문적인 GDD를 한국어로 작성하세요.
            문서 수준: {detail_level}
            조건 - 장르: {genre}, 타겟: {target}, 키워드: {keywords}, 아트 스타일: {art_style}
            구조: 1. Concept Summary, 2. World Building, 3. Core Loop, 4. Key Systems, 5. Business Model, 6. UI/UX Concept
            """
            
            try:
                model = genai.GenerativeModel('gemini-flash-latest')
                response = model.generate_content(prompt)
                result_text = response.text
                
                # 시각적 레퍼런스 이미지 생성 (3종)
                img_prompts = {
                    "main": f"A professional high-quality game concept art of a {genre} game, {art_style} style, theme: {keywords}. Cinematic lighting, detailed background.",
                    "world": f"Environment concept art for a {genre} game world, {art_style} style, featuring {keywords}. Immersive atmosphere.",
                    "ui": f"Game user interface (UI) design for mobile {genre}, {art_style} style, buttons and menus matching {keywords} theme. Clean and modern."
                }
                
                images = {}
                for key, p in img_prompts.items():
                    img_b64 = generate_game_image(p)
                    if img_b64:
                        images[key] = img_b64
                
                # 결과 저장
                st.session_state['gdd_result'] = result_text
                st.session_state['generated_images'] = images
                st.session_state['history'].append({
                    "keywords": keywords, "genre": genre, "content": result_text, "images": images
                })
                
            except Exception as e:
                st.error(f"생성 중 오류 발생: {e}")

# 4. 결과 출력 섹션
if st.session_state['gdd_result']:
    st.divider()
    st.subheader(f"📝 기획서 본문 및 맞춤형 레퍼런스")
    
    sections = st.session_state['gdd_result'].split('\n\n')
    images = st.session_state['generated_images']
    
    for i, section in enumerate(sections):
        st.markdown(section)
        
        # 맥락에 맞는 생성 이미지 삽입
        if i == 0 and "main" in images:
            st.image(base64.b64decode(images["main"]), caption=f"AI 생성 레퍼런스: {genre} 메인 컨셉", width=800)
        elif ("World" in section or "세계관" in section) and "world" in images:
            st.image(base64.b64decode(images["world"]), caption=f"AI 생성 레퍼런스: {keywords} 테마 세계관 비주얼", width=800)
        elif ("UI" in section or "인터페이스" in section) and "ui" in images:
            st.image(base64.b64decode(images["ui"]), caption=f"AI 생성 레퍼런스: {art_style} 스타일 UI/UX 가이드", width=800)

    # PDF 다운로드 버튼 (최하단)
    st.divider()
    try:
        current_kw = keywords if keywords else "Game"
        pdf_bytes = create_pdf(st.session_state['gdd_result'], current_kw)
        st.download_button(
            label="📄 완성된 기획서 PDF 다운로드",
            data=bytes(pdf_bytes),
            file_name=f"GDD_Pro_{current_kw}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"PDF 생성 중 문제가 발생했습니다.")

st.caption("비토쨩이 테스트로 만들었단다.")