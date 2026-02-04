# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="비토쨩 자동 기획서 연습 B-Ver", page_icon="🎮", layout="wide")

# --- 🎨 프리미엄 에디토리얼 UI 스타일링 (Streamlit 영역) ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Pretendard', sans-serif; }
    
    /* 사이드바 스타일 강화 */
    [data-testid="stSidebar"] { 
        background-color: #ffffff; 
        border-right: 1px solid #e2e8f0; 
    }
    
    .main-title {
        font-size: calc(2.2rem + 1.5vw) !important; 
        font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 0.5rem !important;
    }
    
    div.stButton > button {
        border-radius: 12px !important; 
        font-weight: 700 !important;
        transition: all 0.2s; 
        height: 3.5rem;
    }
    
    .status-card {
        padding: 12px; 
        border-radius: 10px; 
        background: #f8fafc; 
        border: 1px solid #e2e8f0; 
        margin-bottom: 8px; 
        font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API 키 설정 및 사이드바 복구 ---
def load_api_key():
    for k in ["GEMINI_API_KEY", "gemini_api_key", "API_KEY"]:
        if k in st.secrets: return st.secrets[k]
    return ""

# 세션 상태 초기화
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []

# 사이드바 구성
with st.sidebar:
    st.header("🔑 보안 및 설정")
    API_KEY = load_api_key()
    if not API_KEY:
        API_KEY = st.text_input("Gemini API Key를 입력하세요", type="password")
    else:
        st.info("✅ API 키 로드 완료")
    
    if API_KEY:
        genai.configure(api_key=API_KEY)
        
    # 히스토리 목록
    if st.session_state['history']:
        st.divider()
        st.header("🕒 기획 히스토리")
        for i, item in enumerate(st.session_state['history'][::-1]):
            if st.button(f"📄 {item['key'][:12]}...", key=f"hist_{i}", use_container_width=True):
                st.session_state['gdd_result'] = item['content']
                st.session_state['generated_images'] = item.get('images', {})
                st.rerun()

    # 이미지 상태 정보
    if st.session_state['generated_images']:
        st.divider()
        st.header("🖼️ 생성 이미지 상태")
        for k, v in st.session_state['generated_images'].items():
            color = "#10b981" if v else "#ef4444"
            status = "준비됨" if v else "실패"
            st.markdown(f"<div class='status-card'>{k.upper()}: <b style='color:{color}'>{status}</b></div>", unsafe_allow_html=True)

# --- 🎨 고화질 이미지 엔진 (Imagen 4.0 - 규격 엄수 버전) ---
def generate_hd_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"A breathtaking high-quality masterpiece game key visual art, {genre}, theme: {key}, style: {art}. 8k resolution, cinematic lighting, professional digital art, epic scale.",
        "ui": f"High-fidelity professional mobile game UI/UX design mockup, {genre} HUD interface, style: {art}. Dashboard, inventory, clean layout, inspired by {key}. Digital game design sheet, 4k.",
        "world": f"Environment concept art, immersive game world of {genre}, theme: {key}, style: {art}. Beautiful landscape, masterpiece lighting.",
        "character": f"High-quality character concept portrait, {genre} unit, motif: {key}, style: {art}. Professional character asset sheet."
    }
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    # instances가 단일 객체여야 함
    payload = {
        "instances": {"prompt": prompts[prompt_type]}, 
        "parameters": {"sampleCount": 1}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            result = response.json()
            return result["predictions"][0]["bytesBase64Encoded"]
    except Exception:
        pass
    return None

# 메인 UI
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 B-Ver 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습. (좌측 기획서 / 우측 이미지 갤러리 분할 레이아웃)")
st.divider()

# 입력 섹션
with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "FPS/TPS", "전략 시뮬레이션"])
    with c2: target = st.selectbox("타겟 시장", ["글로벌", "한국", "일본", "북미", "유럽", "중국"])
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", ["픽셀 아트 (Retro)", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프")
    
    if st.button("B 버전 기획서 빌드 시작 ✨", key="btn_main", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력하세요.")
        elif not key: st.warning("키워드를 입력하세요.")
        else:
            with st.spinner("텍스트와 아트를 분리하여 고품격 렌더링 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문 GDD를 작성하세요.
                
                [작성 지침]
                1. 섹션 제목은 반드시 '## 제목' 형식을 사용하세요.
                2. 본문의 **강조 텍스트**를 적극 활용하세요.
                3. 전투 공식은 '$$ 공식 내용 $$' 형태로 작성하세요.
                4. '## UI/UX 전략 및 인터페이스 설계' 섹션을 필수 포함하고 하위에 '### UI/UX 목업'을 만드세요.
                5. 복잡한 시스템은 | 표 형식으로 설명하고, 의미 없는 '#' 구분선은 넣지 마세요.
                """
                gdd_res = model.generate_content(prompt)
                
                # 이미지 생성 4종
                imgs = {
                    "concept": generate_hd_image("concept", genre, art, key),
                    "world": generate_hd_image("world", genre, art, key),
                    "ui": generate_hd_image("ui", genre, art, key),
                    "character": generate_hd_image("character", genre, art, key)
                }
                
                st.session_state['gdd_result'] = gdd_res.text
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# --- 🚀 [핵심] B 버전: 영역 분리 렌더링 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    # 데이터 직렬화
    safe_data = json.dumps({
        "title": f"{key.upper()} 게임 디자인 리포트",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }).replace("\\", "\\\\").replace("'", "\\'")

    html_code = """
    <style>
        @media print {
            .control-bar, .image-gallery-pane { display: none !important; }
            body { background: white !important; padding: 0 !important; }
            #gdd-document-pane { 
                box-shadow: none !important; border: none !important; 
                margin: 0 !important; width: 100% !important; max-width: none !important;
            }
        }
        
        body { background: #f1f5f9; padding: 20px; font-family: 'Pretendard', sans-serif; color: #1e293b; overflow-x: hidden; }
        
        .control-bar { max-width: 1550px; margin: 0 auto 40px auto; display: flex; gap: 20px; }
        .btn { flex: 1; padding: 22px; border-radius: 16px; font-size: 19px; font-weight: 900; cursor: pointer; border: none; transition: all 0.3s ease; color: white; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .btn-pdf { background: #4f46e5; }
        .btn-img { background: #7c3aed; }

        .workspace { display: flex; gap: 40px; max-width: 1550px; margin: 0 auto; align-items: flex-start; }
        
        #gdd-document-pane {
            flex: 0 0 65%; background: white; padding: 100px 80px; border-radius: 40px;
            border: 1px solid #e2e8f0; box-shadow: 0 40px 80px rgba(0,0,0,0.06);
            min-height: 1200px; line-height: 1.9;
        }
        
        .image-gallery-pane { flex: 1; position: sticky; top: 30px; display: flex; flex-direction: column; gap: 30px; }

        h1.doc-title { font-size: 64px; font-weight: 900; text-align: center; border-bottom: 12px solid #4f46e5; padding-bottom: 40px; margin-bottom: 80px; letter-spacing: -0.05em; }
        h2 { font-size: 34px; font-weight: 800; color: #4f46e5; margin-top: 60px; margin-bottom: 30px; padding-left: 20px; border-left: 10px solid #4f46e5; background: #f8fafc; padding-top: 15px; padding-bottom: 15px; border-radius: 0 12px 12px 0; }
        h3 { font-size: 26px; font-weight: 700; color: #1e293b; margin-top: 45px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; }
        p { font-size: 21px; color: #334155; margin-bottom: 25px; text-align: justify; }
        
        .math-box { background: #f8faff; border-top: 2px solid #c7d2fe; border-bottom: 2px solid #c7d2fe; padding: 30px; border-radius: 12px; text-align: center; font-size: 24px; font-weight: 700; margin: 40px 0; color: #3730a3; font-family: 'Times New Roman', serif; }
        
        table { width: 100%; border-collapse: collapse; margin: 30px 0; border-radius: 15px; overflow: hidden; font-size: 18px; border: 1px solid #e2e8f0; }
        th { background: #4f46e5; color: white; padding: 18px; text-align: left; }
        td { padding: 18px; border-bottom: 1px solid #f1f5f9; color: #475569; }

        .img-card { background: white; border: 1px solid #e2e8f0; padding: 20px; border-radius: 25px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.05); }
        .img-card img { width: 100%; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .img-tag { font-size: 16px; color: #6366f1; font-weight: 900; margin-top: 20px; text-transform: uppercase; letter-spacing: 2px; }
        
        hr { border: none; border-top: 1px solid #e2e8f0; margin: 50px 0; }
    </style>

    <div class="control-bar">
        <button class="btn btn-pdf" onclick="window.print()">📄 기획서 PDF 저장</button>
        <button class="btn btn-img" id="downloadReport">🖼️ 전체 통합 리포트 저장</button>
    </div>

    <div class="workspace" id="capture-all">
        <div id="gdd-document-pane">
            <h1 class="doc-title" id="main-title-view"></h1>
            <div id="doc-content-root"></div>
        </div>
        <div class="image-gallery-pane" id="image-gallery-root"></div>
    </div>

    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {
            const data = JSON.parse('ST_DATA_JSON');
            document.getElementById('main-title-view').innerText = data.title;
            
            function cleanAndRender(text) {
                return text.split('\\n').map(line => {
                    let l = line.trim();
                    if (!l || l === '#' || l === '##' || l === '###') return '';

                    if (l.startsWith('$$') && l.endsWith('$$')) {
                        return '<div class="math-box">' + processInline(l.replace(/\\$\\$/g, '')) + '</div>';
                    }
                    if (l.startsWith('|')) {
                        const cells = l.split('|').filter(c => c.trim() !== '' || l.indexOf('|') !== l.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0 || l.includes('---')) return '';
                        return '<tr>' + cells.map(c => '<td>' + processInline(c) + '</td>').join('') + '</tr>';
                    }
                    if (l.startsWith('##')) return '<h2>' + l.replace(/^##\s*/, '') + '</h2>';
                    if (l.startsWith('###')) return '<h3>' + l.replace(/^###\s*/, '') + '</h3>';
                    if (l === '---' || l === '***') return '<hr>';
                    
                    return '<p>' + processInline(l) + '</p>';
                }).join('');
            }

            function processInline(t) {
                return t
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:800;">$1</strong>')
                    .replace(/\\\\text\{(.*?)\}/g, '$1')
                    .replace(/\\\\times/g, '×')
                    .replace(/\\\\cdot/g, '·');
            }

            function addImageCard(base64, label) {
                if (!base64) return '';
                const src = base64.startsWith('data:') ? base64 : 'data:image/png;base64,' + base64;
                return '<div class="img-card"><img src="' + src + '"><div class="img-tag">' + label + '</div></div>';
            }

            const docRoot = document.getElementById('doc-content-root');
            const galleryRoot = document.getElementById('image-gallery-root');
            
            let bodyHtml = cleanAndRender(data.content);
            bodyHtml = bodyHtml.replace(/(<tr>.*?<\\/tr>)+/g, m => '<div style="overflow-x:auto;"><table>' + m + '</table></div>');
            docRoot.innerHTML = bodyHtml;
            
            let galleryHtml = "";
            if(data.images.concept) galleryHtml += addImageCard(data.images.concept, 'Key Concept Art');
            if(data.images.world) galleryHtml += addImageCard(data.images.world, 'World Environment');
            if(data.images.ui) galleryHtml += addImageCard(data.images.ui, 'UI/UX Mockup');
            if(data.images.character) galleryHtml += addImageCard(data.images.character, 'Main Asset');
            galleryRoot.innerHTML = galleryHtml;

            document.getElementById('downloadReport').onclick = function() {
                const btn = this;
                btn.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('capture-all'), { 
                    scale: 2, useCORS: true, backgroundColor: "#f1f5f9"
                }).then(canvas => {
                    const a = document.createElement('a');
                    a.download = 'Vito_B_Premium_Report.png';
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    btn.innerText = "🖼️ 전체 통합 리포트 저장";
                });
            };
        })();
    </script>
    """
    
    final_html = html_code.replace("ST_DATA_JSON", safe_data)
    components.html(final_html, height=8000, scrolling=True)

st.caption("비토쨩 연습하기 - B 버전 (영역 분리형)")