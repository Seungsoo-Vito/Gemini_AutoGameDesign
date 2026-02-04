import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration (Wide 모드 활성화)
st.set_page_config(page_title="비토쨩 자동 기획서 연습", page_icon="🎮", layout="wide")

# --- 🎨 프리미엄 에디토리얼 UI 스타일링 (너비 확장 버전) ---
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
        font-size: calc(2.2rem + 1.8vw) !important; 
        font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: -0.05em;
        margin-bottom: 0.5rem !important;
    }
    
    div.stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.2s;
        height: 3.5rem;
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
        "concept": f"Cinematic epic game key visual art, {genre}, theme: {key}, style: {art}. 8k resolution, professional game lighting.",
        "ui": f"Professional High-fidelity mobile game UI/UX mockup design, {genre} interface, style: {art}. HUD, dashboard, inventory, menu screens, inspired by {key}. Digital game design sheet.",
        "world": f"Environment concept art, immersive game world of {genre}, location theme: {key}, style: {art}. Beautiful landscape.",
        "character": f"Character concept art portrait or unit asset, {genre} game, motif: {key}, style: {art}. Clear presentation."
    }
    selected_prompt = prompts.get(prompt_type, prompts["concept"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": selected_prompt}], "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()["predictions"][0]["bytesBase64Encoded"]
    except: pass
    return None

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
    
    if st.session_state['generated_images']:
        st.divider()
        st.caption("🖼️ 이미지 생성 상태")
        for k, v in st.session_state['generated_images'].items():
            status = "✅ 성공" if v else "❌ 실패"
            st.caption(f"{k.capitalize()}: {status}")

# --- 4. UI Main ---
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습. (확장된 너비와 개선된 이미지 엔진)")
st.divider()

# Input Options
genres = ["방치형 RPG", "수집형 RPG", "액션 RPG", "MMORPG", "로그라이크", "전략 시뮬레이션", "FPS/TPS", "퍼즐"]
targets = ["글로벌", "한국", "일본", "중국", "북미", "유럽", "동남아시아"]
styles = ["픽셀 아트 (Retro)", "2D 카툰/애니메이션", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지"]

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
            with st.spinner("시니어 기획자가 시스템과 이미지를 생성 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문적인 게임 디자인 문서(GDD)를 작성하세요.
                
                [문서 보강 지시]
                - "## 핵심 게임 시스템" 섹션: 전투 밸런스 공식, 성장 테이블(EXP), 경제 시스템을 전문 수치를 포함해 상세히 작성하세요.
                - "## 주요 콘텐츠 구성" 섹션: 유저의 하루 플레이 동선과 초기-중기-말기 콘텐츠 순환 구조를 상세히 포함하세요.
                - 전체 분량은 최소 4500자 이상의 매우 상세한 기획안이어야 합니다.
                - 섹션 제목은 반드시 '## '로 시작하고, 섹션 사이의 불필요한 '#' 기호는 절대 넣지 마세요.
                """
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # 이미지 생성 4종
                imgs = {
                    "concept": generate_specialized_image("concept", genre, art, key),
                    "ui": generate_specialized_image("ui", genre, art, key),
                    "world": generate_specialized_image("world", genre, art, key),
                    "asset": generate_specialized_image("character", genre, art, key)
                }
                
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# --- 5. Result Display & Export Engine (너비 및 이미지 최적화) ---
if st.session_state['gdd_result']:
    st.divider()
    
    export_data = {
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }
    
    # height를 충분히 확보하고 scrolling 활성화
    components.html(f"""
        <div id="render-target"></div>
        
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
            const data = {json.dumps(export_data)};
            
            function cleanMd(md) {{
                return md
                    .replace(/^#\s*$/gm, '') // 홀로 남은 # 제거
                    .replace(/^### (.*$)/gim, '<h3 style="font-size:24px; font-weight:700; color:#1e293b; margin-top:35px; border-bottom:2px solid #f1f5f9; padding-bottom:8px;">$1</h3>')
                    .replace(/^## (.*$)/gim, '<h2 style="font-size:32px; font-weight:800; color:#4f46e5; border-left:12px solid #4f46e5; padding:15px 25px; background:#f8fafc; margin-top:60px; border-radius:0 12px 12px 0;">$1</h2>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/^\\* (.*$)/gim, '<li style="margin-bottom:12px; font-size:19px;">$1</li>')
                    .replace(/\\n/g, '<br>')
                    .replace(/(<li>.*<\\/li>)/s, '<ul style="padding-left:30px; margin-bottom:30px;">$1</ul>');
            }}

            function generateFullHTML(data) {{
                // 메인 컨테이너 너비를 1100px로 확장
                let html = `<div id="gdd-doc-area" style="background:white; padding:80px 70px; border-radius:16px; font-family:'Pretendard', sans-serif; color:#1e293b; line-height:1.8; max-width:1100px; margin:0 auto; border:1px solid #e2e8f0; box-shadow:0 15px 40px rgba(0,0,0,0.06);">`;
                html += `<h1 style="font-size:56px; font-weight:900; text-align:center; border-bottom:10px solid #4f46e5; padding-bottom:25px; margin-bottom:50px; letter-spacing:-0.03em;">${{data.title}}</h1>`;
                
                // 1. 메인 컨셉 이미지 (확장 너비 적용)
                if(data.images.concept) {{
                    html += `<div style="text-align:center; margin-bottom:60px;"><img src="data:image/png;base64,${{data.images.concept}}" style="max-width:950px; width:100%; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.12);"><div style="color:#64748b; font-size:16px; margin-top:15px; font-style:italic; font-weight:600;">[Main Concept Architecture]</div></div>`;
                }}
                
                const parts = data.content.split('## ');
                let usedImages = new Set(["concept"]);
                
                const imgMap = {{
                    "world": ["세계관", "배경", "아트", "컨셉", "분위기", "콘텐츠", "지도"],
                    "ui": ["시스템", "UI", "UX", "인터페이스", "메커니즘", "성장", "전투", "플레이", "화면"],
                    "asset": ["캐릭터", "에셋", "유닛", "몬스터", "아이템", "영웅", "스킬"]
                }};

                parts.forEach((p, i) => {{
                    if(!p.trim()) return;
                    let sectionTitle = p.split('\\n')[0];
                    html += cleanMd((i > 0 ? '## ' : '') + p);
                    
                    // 지능형 섹션별 이미지 자동 배치
                    for(let key in imgMap) {{
                        if(!usedImages.has(key)) {{
                            if(imgMap[key].some(kw => sectionTitle.includes(kw)) && data.images[key]) {{
                                html += `<div style="text-align:center; margin:50px 0;"><img src="data:image/png;base64,${{data.images[key]}}" style="max-width:950px; width:100%; border-radius:16px; box-shadow:0 10px 25px rgba(0,0,0,0.1);"><div style="color:#64748b; font-size:15px; margin-top:12px; font-style:italic; font-weight:600;">[${{key.toUpperCase()}} Visual Reference]</div></div>`;
                                usedImages.add(key);
                                break;
                            }}
                        }}
                    }}
                }});
                
                // 매칭 안 된 남은 이미지 하단 '디자인 가이드' 부록으로 자동 배치
                const remaining = ["world", "ui", "asset"].filter(k => !usedImages.has(k) && data.images[k]);
                if(remaining.length > 0) {{
                    html += `<h2 style="font-size:32px; font-weight:800; color:#4f46e5; border-left:12px solid #4f46e5; padding:15px 25px; background:#f8fafc; margin-top:80px;">부록: 통합 디자인 리소스</h2>`;
                    remaining.forEach(key => {{
                        html += `<div style="text-align:center; margin:45px 0;"><img src="data:image/png;base64,${{data.images[key]}}" style="max-width:950px; width:100%; border-radius:16px;"><div style="color:#64748b; font-size:15px; margin-top:12px; font-weight:600;">[${{key}} Reference Guide]</div></div>`;
                    }});
                }}

                html += `</div>`;
                return html;
            }}

            const container = document.getElementById('render-target');
            container.innerHTML = `
                <div style="display:flex; gap:20px; margin-bottom:40px; max-width:1100px; margin-left:auto; margin-right:auto;">
                    <button id="pdfBtn" style="flex:1; background:#4f46e5; color:white; border:none; padding:20px; border-radius:14px; font-weight:800; cursor:pointer; font-size:18px; box-shadow:0 4px 15px rgba(79,70,229,0.3);">📄 PDF로 저장 (확장 레이아웃)</button>
                    <button id="pngBtn" style="flex:1; background:#7c3aed; color:white; border:none; padding:20px; border-radius:14px; font-weight:800; cursor:pointer; font-size:18px; box-shadow:0 4px 15px rgba(124,58,237,0.3);">🖼️ 고화질 이미지 저장</button>
                </div>
                <div>${{generateFullHTML(data)}}</div>
            `;

            document.getElementById('pdfBtn').onclick = () => {{
                const win = window.open('', '_blank');
                win.document.write('<html><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"></head><body style="margin:0; padding:0; background:#f1f5f9;">' + document.getElementById('gdd-doc-area').outerHTML + '</body></html>');
                win.document.close();
                win.onload = () => setTimeout(() => {{ win.focus(); win.print(); }}, 800);
            }};

            document.getElementById('pngBtn').onclick = () => {{
                const btn = document.getElementById('pngBtn');
                const original = btn.innerText;
                btn.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('gdd-doc-area'), {{ useCORS: true, scale: 2 }}).then(canvas => {{
                    const a = document.createElement('a');
                    a.download = `GDD_${{data.title}}.png`;
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    btn.innerText = original;
                }});
            }};
        </script>
    """, height=3500, scrolling=True)

st.caption("비토쨩 연습하기")