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
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# --- 🎨 프리미엄 에디토리얼 UI 스타일링 ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    .stApp { 
        background-color: #f1f5f9; 
        color: #1e293b; 
        font-family: 'Pretendard', sans-serif; 
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    .main-title {
        font-size: calc(2rem + 1.5vw) !important; 
        font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: -0.05em;
        margin-bottom: 0.5rem !important;
    }
    
    /* 📸 기획서 렌더링 영역 (Modern Paper Design) */
    #gdd-capture-area {
        background: #ffffff;
        padding: 60px 50px;
        border-radius: 16px; 
        color: #1e293b;
        line-height: 1.8;
        max-width: 850px;
        width: 100%;
        margin: 20px auto;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
    }
    
    /* 이미지 및 캡션 최적화 */
    .img-wrapper {
        max-width: 800px;
        margin: 40px auto;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    .img-caption {
        font-size: 0.9rem;
        color: #64748b;
        text-align: center;
        margin-top: -30px;
        margin-bottom: 40px;
        font-weight: 500;
        font-style: italic;
    }
    
    /* 마크다운 요소별 디테일 디자인 */
    #gdd-capture-area h1 { font-size: 3rem; font-weight: 900; text-align: center; margin-bottom: 40px; color: #1e293b; border-bottom: 8px solid #4f46e5; padding-bottom: 20px; }
    #gdd-capture-area h2 { font-size: 1.8rem; font-weight: 800; color: #4f46e5; margin-top: 50px; margin-bottom: 20px; border-left: 10px solid #4f46e5; padding: 12px 20px; background: #f8fafc; border-radius: 0 8px 8px 0; }
    #gdd-capture-area h3 { font-size: 1.4rem; font-weight: 700; margin-top: 30px; margin-bottom: 15px; color: #334155; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; }
    #gdd-capture-area p { font-size: 1.1rem; margin-bottom: 18px; color: #334155; text-align: justify; word-break: keep-all; }
    #gdd-capture-area li { font-size: 1.05rem; margin-bottom: 10px; color: #475569; }
    #gdd-capture-area strong { color: #4f46e5; font-weight: 700; }

    /* 버튼 스타일 */
    div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(79, 70, 229, 0.2);
    }

    @media (max-width: 768px) {
        #gdd-capture-area { padding: 30px 20px; }
        .main-title { font-size: 2.2rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API Key Security ---
def load_api_key():
    for k in ["GEMINI_API_KEY", "gemini_api_key", "API_KEY"]:
        if k in st.secrets: return st.secrets[k]
    return ""

API_KEY = load_api_key()

with st.sidebar:
    st.header("🔑 보안 및 설정")
    if not API_KEY:
        API_KEY = st.text_input("Gemini API Key를 입력하세요", type="password")
    else:
        st.info("✅ API 키가 클라우드에서 로드되었습니다.")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 Intelligent Image Engine ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"Cinematic epic game key visual, {genre}, {key} theme, {art} style. 8k, professional game art.",
        "ui": f"Modern game UI/UX mockup, {genre} mobile game interface, {art} style. Clean layout, icons.",
        "world": f"Environment concept art, world of {genre} game, location: {key}, {art} style. Atmospheric.",
        "character": f"Character concept art or asset sheet, {genre}, {key} motif, {art} style. High detail."
    }
    selected_prompt = prompts.get(prompt_type, prompts["concept"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": selected_prompt}], "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json()["predictions"][0]["bytesBase64Encoded"]
    except: return None

# Session State
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []

# --- 3. Sidebar History ---
with st.sidebar:
    st.divider()
    st.header("🕒 기획 히스토리")
    if st.session_state['history']:
        for i, item in enumerate(st.session_state['history'][::-1]):
            if st.button(f"📄 {item['key'][:12]}", key=f"hist_{i}", use_container_width=True):
                st.session_state['gdd_result'] = item['content']
                st.session_state['generated_images'] = item.get('images', {})
                st.rerun()

# --- 4. UI Main ---
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습.")
st.divider()

# Input Section
with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르", ["방치형 RPG", "수집형 RPG", "오픈월드", "로그라이크", "액션"])
    with c2: target = st.selectbox("타겟 국가", ["글로벌", "한국", "일본", "북미/유럽"])
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프")
    
    if st.button("기획서 생성 및 이미지 생성 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력해 주세요.")
        elif not key: st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("최고의 시니어 기획자가 기획서를 작성 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다.
                다음 조건으로 전문적인 게임 디자인 문서(GDD)를 작성하세요: 장르={genre}, 국가={target}, 키워드={key}, 아트={art}.
                
                [문서 구조 지시]
                1. ## 섹션 제목, ### 소제목 형식을 엄격히 지키세요.
                2. 각 항목은 마크다운 불렛(*)을 사용하세요.
                3. **강조 텍스트**를 적절히 섞어 가독성을 높이세요.
                4. 시스템 수치나 운영 전략을 구체적으로 포함하세요.
                """
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                imgs = {
                    "concept": generate_specialized_image("concept", genre, art, key),
                    "ui": generate_specialized_image("ui", genre, art, key),
                    "world": generate_specialized_image("world", genre, art, key),
                    "asset": generate_specialized_image("character", genre, art, key)
                }
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# Result Display Logic
if st.session_state['gdd_result']:
    st.divider()
    
    # 📸 GDD 미리보기 (화면 표시용)
    st.markdown('<div id="gdd-capture-area">', unsafe_allow_html=True)
    st.markdown(f"<h1>{key.upper()} 기획안</h1>", unsafe_allow_html=True)
    
    imgs = st.session_state['generated_images']
    
    if imgs.get("concept"):
        st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
        st.image(base64.b64decode(imgs["concept"]), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<p class="img-caption">[Concept Art Visual]</p>', unsafe_allow_html=True)

    content = st.session_state['gdd_result']
    sections = content.split("## ")
    for i, section in enumerate(sections):
        if not section.strip(): continue
        sec_text = "## " + section if i > 0 else section
        st.markdown(sec_text) 
        
        if i == 1 and imgs.get("world"):
            st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
            st.image(base64.b64decode(imgs["world"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<p class="img-caption">[World & Environment Reference]</p>', unsafe_allow_html=True)
        elif i == 3 and imgs.get("ui"):
            st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
            st.image(base64.b64decode(imgs["ui"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<p class="img-caption">[UI/UX Mockup Design]</p>', unsafe_allow_html=True)
        elif i == 5 and imgs.get("asset"):
            st.markdown('<div class="img-wrapper">', unsafe_allow_html=True)
            st.image(base64.b64decode(imgs["asset"]), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<p class="img-caption">[Character & Asset Concept]</p>', unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 📥 저장 엔진 (서식 깨짐 방지 파서 고도화) ---
    st.write("---")
    
    export_data = {
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }
    
    components.html(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 20px;">
            <button id="pdfBtn" style="flex:1; background: #4f46e5; color: white; border: none; padding: 18px; border-radius: 12px; font-weight: 800; cursor: pointer; font-size: 17px;">
                📄 PDF로 저장 (인쇄)
            </button>
            <button id="pngBtn" style="flex:1; background: #7c3aed; color: white; border: none; padding: 18px; border-radius: 12px; font-weight: 800; cursor: pointer; font-size: 17px;">
                🖼️ 고화질 이미지(PNG) 저장
            </button>
        </div>
        
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
            const data = {json.dumps(export_data)};
            
            // 🚀 정교한 마크다운 HTML 파서
            function cleanMd(md) {{
                return md
                    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/^\\* (.*$)/gim, '<li>$1</li>')
                    .replace(/\\n/g, '<br>')
                    .replace(/(<li>.*<\\/li>)/s, '<ul>$1</ul>');
            }}

            function buildDoc(data) {{
                let html = `<html><head><meta charset="UTF-8"><title>${{data.title}}</title>`;
                html += `<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">`;
                html += `<style>
                    body {{ font-family: 'Pretendard', sans-serif; padding: 60px; color: #1e293b; max-width: 800px; margin: 0 auto; line-height: 1.8; background: white; }}
                    h1 {{ font-size: 48px; border-bottom: 8px solid #4f46e5; padding-bottom: 20px; text-align: center; font-weight: 900; }}
                    h2 {{ color: #4f46e5; margin-top: 50px; border-left: 10px solid #4f46e5; padding: 12px 20px; background: #f8fafc; font-size: 26px; font-weight: 800; }}
                    h3 {{ font-size: 20px; font-weight: 700; margin-top: 30px; color: #1e293b; border-bottom: 2px solid #f1f5f9; }}
                    img {{ max-width: 100%; border-radius: 12px; margin: 35px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
                    p, li {{ font-size: 17px; margin-bottom: 12px; color: #334155; text-align: justify; }}
                    ul {{ padding-left: 20px; margin-bottom: 25px; }}
                    li {{ list-style-type: disc; }}
                    strong {{ color: #4f46e5; }}
                    .cap {{ text-align: center; color: #94a3b8; font-size: 14px; margin-top: -30px; margin-bottom: 45px; font-weight: 500; }}
                </style></head><body>`;
                
                html += `<h1>${{data.title}}</h1>`;
                if(data.images.concept) html += `<center><img src="data:image/png;base64,${{data.images.concept}}"></center><div class="cap">[Main Concept]</div>`;
                
                const parts = data.content.split('## ');
                parts.forEach((p, i) => {{
                    if(!p.trim()) return;
                    html += cleanMd((i > 0 ? '## ' : '') + p);
                    if(i === 1 && data.images.world) html += `<center><img src="data:image/png;base64,${{data.images.world}}"></center><div class="cap">[World View]</div>`;
                    if(i === 3 && data.images.ui) html += `<center><img src="data:image/png;base64,${{data.images.ui}}"></center><div class="cap">[UI/UX Design]</div>`;
                    if(i === 5 && data.images.asset) html += `<center><img src="data:image/png;base64,${{data.images.asset}}"></center><div class="cap">[Asset Concept]</div>`;
                }});
                
                html += `</body></html>`;
                return html;
            }}

            document.getElementById('pdfBtn').onclick = () => {{
                const win = window.open('', '_blank');
                win.document.write(buildDoc(data));
                win.document.close();
                win.onload = () => setTimeout(() => {{ win.focus(); win.print(); }}, 500);
            }};

            document.getElementById('pngBtn').onclick = () => {{
                const btn = document.getElementById('pngBtn');
                btn.innerText = "⏳ 고화질 렌더링 중...";
                const div = document.createElement('div');
                div.style.position = 'absolute'; div.style.left = '-9999px'; div.style.width = '800px';
                div.innerHTML = buildDoc(data);
                document.body.appendChild(div);

                setTimeout(() => {{
                    html2canvas(div, {{ useCORS: true, scale: 2.5, backgroundColor: "#ffffff" }}).then(canvas => {{
                        const a = document.createElement('a');
                        a.download = `VitoGDD_${{data.title}}.png`;
                        a.href = canvas.toDataURL('image/png');
                        a.click();
                        btn.innerText = "🖼️ 고화질 이미지(PNG) 저장";
                        document.body.removeChild(div);
                    }});
                }}, 1200);
            }};
        </script>
    """, height=100)

st.caption("비토쨩 연습하기")