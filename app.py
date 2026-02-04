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
st.set_page_config(page_title="비토쨩 자동 기획서 연습", page_icon="🎮", layout="wide")

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
    #gdd-preview-container {
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
        max-width: 700px; /* 크기 최적화 */
        margin: 30px auto;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
    }
    
    .img-caption {
        font-size: 0.85rem;
        color: #64748b;
        text-align: center;
        margin-top: -20px;
        margin-bottom: 30px;
        font-weight: 500;
        font-style: italic;
    }
    
    /* 마크다운 요소별 디테일 디자인 */
    h1.gdd-h1 { font-size: 2.8rem; font-weight: 900; text-align: center; margin-bottom: 35px; color: #1e293b; border-bottom: 6px solid #4f46e5; padding-bottom: 15px; }
    h2.gdd-h2 { font-size: 1.7rem; font-weight: 800; color: #4f46e5; margin-top: 45px; margin-bottom: 18px; border-left: 10px solid #4f46e5; padding: 10px 18px; background: #f8fafc; border-radius: 0 8px 8px 0; }
    h3.gdd-h3 { font-size: 1.3rem; font-weight: 700; margin-top: 28px; margin-bottom: 12px; color: #334155; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px; }
    .gdd-p { font-size: 1.05rem; margin-bottom: 16px; color: #334155; text-align: justify; word-break: keep-all; }
    .gdd-li { font-size: 1rem; margin-bottom: 8px; color: #475569; }

    /* 버튼 스타일 */
    div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.2s;
    }

    @media (max-width: 768px) {
        #gdd-preview-container { padding: 30px 15px; }
        .main-title { font-size: 2.1rem !important; }
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
        "concept": f"Cinematic epic game key visual, {genre}, {key} theme, {art} style. 8k, high quality professional art.",
        "ui": f"Professional game UI/UX design mockup, {genre} mobile game interface, {art} style. Inventory screen, menu buttons, high fidelity digital design.",
        "world": f"Immersive environment background art, world of {genre}, location based on {key}, {art} style. Detailed scenery.",
        "character": f"Character concept art or detailed asset sheet, {genre}, {key} motif, {art} style. Clear presentation."
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

# Input Options
genres = ["방치형 RPG", "수집형 RPG", "액션 RPG", "MMORPG", "로그라이크", "FPS/TPS", "전략 시뮬레이션", "공포/호러", "퍼즐", "비주얼 노벨"]
targets = ["글로벌", "한국", "일본", "중국", "북미", "유럽", "동남아시아"]
styles = ["픽셀 아트 (Retro)", "2D 카툰/애니메이션", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지", "현대/어반"]

with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", genres)
    with c2: target = st.selectbox("타겟 국가", targets)
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", styles)
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 우주선")
    
    if st.button("기획서 생성 및 이미지 생성 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력해 주세요.")
        elif not key: st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("시니어 기획자가 시스템과 콘텐츠를 설계 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 GDD를 작성하세요.
                
                특히 다음 섹션을 매우 상세하게 작성해 주세요:
                1. ## 핵심 게임 시스템: 핵심 메커니즘, 전투/성장 공식, 주요 수치 밸런싱 가이드.
                2. ## 주요 콘텐츠 및 순환 구조: 초기/중기/말기 콘텐츠 구성, 유저의 일일 플레이 사이클(Daily Loop).
                3. ## UI/UX 및 편의성 전략: 사용자 경험을 극대화하기 위한 인터페이스 설계 방향.
                
                [형식 지시]
                - ## 섹션 제목, ### 소제목 형식을 유지하세요.
                - 마크다운 불렛(*)과 **강조**를 적극적으로 사용하세요.
                - 전문적이고 구체적인 용어를 사용하세요.
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

# --- 5. Result Display Logic ---
def render_gdd_content(content, imgs, title_key):
    # 이 함수는 화면 출력용 HTML을 생성합니다.
    html = f"<div id='gdd-preview-container'>"
    html += f"<h1 class='gdd-h1'>{title_key.upper()} 기획안</h1>"
    
    if imgs.get("concept"):
        html += f"<div class='img-wrapper'><img src='data:image/png;base64,{imgs['concept']}' style='width:100%;'></div><div class='img-caption'>[Main Concept Visual]</div>"
    
    parts = content.split("## ")
    for i, part in enumerate(parts):
        if not part.strip(): continue
        
        # 제목과 본문 분리
        lines = part.split("\n")
        section_title = lines[0].strip()
        section_body = "\n".join(lines[1:]).strip()
        
        html += f"<h2 class='gdd-h2'>{section_title}</h2>"
        
        # 마크다운 기본 변환 (볼드, 소제목, 불렛)
        processed_body = section_body.replace("### ", "<h3 class='gdd-h3'>").replace("\n", "<br>")
        processed_body = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', processed_body)
        processed_body = re.sub(r'^\* (.*?)$', r'<li class="gdd-li">\1</li>', processed_body, flags=re.M)
        
        html += f"<div class='gdd-p'>{processed_body}</div>"
        
        # 지능형 이미지 배치
        if i == 1 and imgs.get("world"):
            html += f"<div class='img-wrapper'><img src='data:image/png;base64,{imgs['world']}' style='width:100%;'></div><div class='img-caption'>[World & Concept Reference]</div>"
        elif ("시스템" in section_title or "UI" in section_title) and imgs.get("ui"):
            html += f"<div class='img-wrapper'><img src='data:image/png;base64,{imgs['ui']}' style='width:100%;'></div><div class='img-caption'>[UI/UX Mockup Design]</div>"
        elif i == len(parts)-1 and imgs.get("asset"):
            html += f"<div class='img-wrapper'><img src='data:image/png;base64,{imgs['asset']}' style='width:100%;'></div><div class='img-caption'>[Core Asset & Character]</div>"

    html += "</div>"
    return html

if st.session_state['gdd_result']:
    st.divider()
    
    gdd_html = render_gdd_content(st.session_state['gdd_result'], st.session_state['generated_images'], key)
    st.markdown(gdd_html, unsafe_allow_html=True)

    # --- 📥 저장 엔진 (서식 유지 파서) ---
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
            
            function cleanMd(md) {{
                return md
                    .replace(/^### (.*$)/gim, '<h3 style="font-size:20px; font-weight:700; color:#1e293b; margin-top:25px; border-bottom:1px solid #f1f5f9;">$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2 style="font-size:26px; font-weight:800; color:#4f46e5; border-left:10px solid #4f46e5; padding:10px 20px; background:#f8fafc; margin-top:40px;">$1</h2>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/^\\* (.*$)/gim, '<li style="margin-bottom:8px;">$1</li>')
                    .replace(/\\n/g, '<br>');
            }}

            function buildDoc(data) {{
                let html = `<html><head><meta charset="UTF-8">`;
                html += `<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">`;
                html += `<style>
                    body {{ font-family: 'Pretendard', sans-serif; padding: 50px; color: #1e293b; max-width: 800px; margin: 0 auto; line-height: 1.8; }}
                    h1 {{ font-size: 42px; border-bottom: 6px solid #4f46e5; padding-bottom: 15px; text-align: center; font-weight: 900; }}
                    img {{ max-width: 100%; border-radius: 12px; margin: 25px 0; }}
                    p, li {{ font-size: 17px; color: #334155; }}
                    strong {{ color: #4f46e5; }}
                    .cap {{ text-align: center; color: #94a3b8; font-size: 13px; margin-top: -15px; margin-bottom: 30px; font-weight: 500; }}
                </style></head><body>`;
                
                html += `<h1>${{data.title}}</h1>`;
                if(data.images.concept) html += `<center><img src="data:image/png;base64,${{data.images.concept}}"></center><div class="cap">[Main Concept]</div>`;
                
                const parts = data.content.split('## ');
                parts.forEach((p, i) => {{
                    if(!p.trim()) return;
                    html += cleanMd((i > 0 ? '## ' : '') + p);
                    if(i === 1 && data.images.world) html += `<center><img src="data:image/png;base64,${{data.images.world}}"></center><div class="cap">[World View]</div>`;
                    if(i === 3 && data.images.ui) html += `<center><img src="data:image/png;base64,${{data.images.ui}}"></center><div class="cap">[UI/UX Design]</div>`;
                }});
                
                html += `</body></html>`;
                return html;
            }}

            document.getElementById('pdfBtn').onclick = () => {{
                const win = window.open('', '_blank');
                win.document.write(buildDoc(data));
                win.document.close();
                win.onload = () => setTimeout(() => {{ win.focus(); win.print(); }}, 600);
            }};

            document.getElementById('pngBtn').onclick = () => {{
                const btn = document.getElementById('pngBtn');
                btn.innerText = "⏳ 렌더링 중...";
                const div = document.createElement('div');
                div.style.position = 'absolute'; div.style.left = '-9999px'; div.style.width = '800px';
                div.innerHTML = buildDoc(data);
                document.body.appendChild(div);

                setTimeout(() => {{
                    html2canvas(div, {{ useCORS: true, scale: 2.5, backgroundColor: "#ffffff" }}).then(canvas => {{
                        const a = document.createElement('a');
                        a.download = `GDD_${{data.title}}.png`;
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