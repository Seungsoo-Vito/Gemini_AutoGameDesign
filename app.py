import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import io
import re
import os.path
import streamlit.components.v1 as components

# 1. Page Configuration (최대 너비 확보)
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
    
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    .main-title {
        font-size: calc(2.5rem + 2vw) !important; 
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
        height: 3.8rem;
    }
    
    .status-card {
        padding: 12px;
        border-radius: 10px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API 키 설정 ---
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
        st.info("✅ API 키 로드 완료")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 🎨 초고화질 이미지 생성 엔진 (Advanced Prompts) ---
def generate_specialized_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    # 퀄리티를 극대화하기 위한 상세 프롬프트 설계
    prompts = {
        "concept": f"A breathtaking high-quality masterpiece game key visual art, {genre}, theme: {key}, style: {art}. 8k resolution, cinematic lighting, dramatic composition, professional digital concept art, epic scale.",
        "ui": f"A sophisticated high-fidelity mobile game UI/UX design mockup, {genre} interface, style: {art}. Clean layout, premium dashboard, intricate menu buttons, user-friendly HUD, inspired by {key}. Digital game design sheet, professional 4k.",
        "world": f"A stunningly detailed environment concept art, vast immersive game world of {genre}, location theme: {key}, style: {art}. Epic scenery, beautiful landscape, atmospheric lighting, masterpiece level, sharp focus.",
        "character": f"A high-quality character concept art portrait, {genre} hero unit, motif: {key}, style: {art}. Full body asset sheet, professional game character design, sharp focus, detailed textures, high detail."
    }
    selected_prompt = prompts.get(prompt_type, prompts["concept"])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": selected_prompt}], "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=90) # 타임아웃 넉넉히 설정
        if response.status_code == 200:
            return response.json()["predictions"][0]["bytesBase64Encoded"]
    except: pass
    return None

# 세션 상태 관리
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}
if 'history' not in st.session_state: st.session_state['history'] = []

# 사이드바 히스토리 및 결과 표시
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
        st.header("🖼️ 생성 이미지 분석")
        for k, v in st.session_state['generated_images'].items():
            color = "#10b981" if v else "#ef4444"
            status = "고화질 생성 성공" if v else "생성 실패"
            st.markdown(f"<div class='status-card'>{k.upper()}: <b style='color:{color}'>{status}</b></div>", unsafe_allow_html=True)

# 메인 UI
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습. (시간이 조금 더 걸리더라도 고퀄리티 결과물을 생성합니다.)")
st.divider()

# 입력 섹션
genres = ["방치형 RPG", "수집형 RPG", "액션 RPG", "MMORPG", "로그라이크", "전략 시뮬레이션", "FPS/TPS"]
targets = ["글로벌", "한국", "일본", "중국", "북미", "유럽"]
styles = ["픽셀 아트 (Retro)", "2D 카툰/애니메이션", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지", "수묵화풍"]

with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", genres)
    with c2: target = st.selectbox("타겟 시장", targets)
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", styles)
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 차원이동, 기계도시")
    
    if st.button("고품격 기획서 & 이미지 생성 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력해 주세요.")
        elif not key: st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("최고의 시니어 기획자가 기획서를 작성하고 아트를 렌더링 중입니다 (최대 2분 소요)..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다. 
                장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문 GDD를 작성하세요.
                
                [작성 지침]
                1. ## 섹션 제목 형식을 엄격히 유지하세요.
                2. 본문의 줄바꿈을 넉넉히 하여 가독성을 높이세요.
                3. 의미 없는 '#' 한 줄 구분선은 절대 넣지 마세요.
                4. 전투 공식, 경제 수치, 콘텐츠 사이클을 구체적으로 포함하세요.
                """
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # 이미지 생성 (시간이 걸려도 4종 모두 시도)
                imgs = {
                    "concept": generate_specialized_image("concept", genre, art, key),
                    "world": generate_specialized_image("world", genre, art, key),
                    "ui": generate_specialized_image("ui", genre, art, key),
                    "character": generate_specialized_image("character", genre, art, key)
                }
                st.session_state['generated_images'] = imgs
                st.session_state['history'].append({"key": key, "content": gdd_res.text, "images": imgs})

# --- 🚀 고도화된 결과 출력 & 렌더링 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    export_payload = {
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }
    
    # f-string 에러를 방지하고 렌더링을 보장하는 템플릿
    html_template = """
    <div id="render-target"></div>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        const data = ST_DATA_JSON;
        
        // 🚀 본문의 마크다운 기호를 완벽하게 세척하고 태그로 변환하는 정밀 파서
        function robustParse(text) {
            return text
                .split('\\n')
                .map(line => {
                    let l = line.trim();
                    if (l === '#' || l === '##' || l === '###') return ''; // 찌꺼기 제거
                    
                    // ## 제목 처리
                    if (l.startsWith('##')) {
                        return `<h2 style="font-size:36px; font-weight:900; color:#4f46e5; border-left:12px solid #4f46e5; padding-left:25px; background:#f8fafc; margin-top:80px; margin-bottom:30px; border-radius:0 15px 15px 0; letter-spacing:-0.03em;">${l.replace(/^##\s*/, '')}</h2>`;
                    }
                    // ### 소제목 처리
                    if (l.startsWith('###')) {
                        return `<h3 style="font-size:26px; font-weight:700; color:#1e293b; margin-top:40px; border-bottom:3px solid #f1f5f9; padding-bottom:12px;">${l.replace(/^###\s*/, '')}</h3>`;
                    }
                    // 불렛 포인트 처리
                    if (l.startsWith('* ') || l.startsWith('- ')) {
                        return `<li style="font-size:21px; color:#475569; margin-bottom:12px; margin-left:25px; line-height:1.6;">${l.replace(/^[*|-]\s*/, '')}</li>`;
                    }
                    // 강조 텍스트 처리
                    if (l.includes('**')) {
                        l = l.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:700;">$1</strong>');
                    }
                    
                    // 일반 본문
                    return l ? `<p style="font-size:21px; color:#334155; line-height:1.9; text-align:justify; margin-bottom:20px;">${l}</p>` : '';
                })
                .join('');
        }

        function buildPremiumHTML(data) {
            let html = `<div id="export-area" style="background:white; padding:120px 90px; border-radius:32px; font-family:'Pretendard', sans-serif; color:#1e293b; line-height:1.9; max-width:1200px; margin:0 auto; border:1px solid #e2e8f0; box-shadow:0 30px 60px rgba(0,0,0,0.08);">`;
            
            // 0. 최상단 프로젝트 타이틀
            html += `<h1 style="font-size:72px; font-weight:900; text-align:center; border-bottom:15px solid #4f46e5; padding-bottom:40px; margin-bottom:80px; letter-spacing:-0.05em;">${data.title}</h1>`;
            
            // 1. [메인 컨셉 이미지] - 무조건 상단
            if(data.images.concept) {
                html += `<div style="text-align:center; margin-bottom:100px;"><img src="data:image/png;base64,${data.images.concept}" style="width:100%; border-radius:24px; box-shadow:0 20px 50px rgba(0,0,0,0.15); border:1px solid #f1f5f9;"><div style="color:#64748b; font-size:18px; margin-top:20px; font-weight:600; font-style:italic;">[PROJECT CORE VISUAL ARCHITECTURE]</div></div>`;
            }
            
            const rawSections = data.content.split('## ');
            const otherImgs = [
                {data: data.images.world, label: 'WORLD CONCEPT VIEW'},
                {data: data.images.ui, label: 'UI/UX SYSTEM MOCKUP'},
                {data: data.images.character, label: 'CHARACTER ASSET DESIGN'}
            ].filter(x => x.data);

            rawSections.forEach((sec, i) => {
                if(!sec.trim()) return;
                
                // 첫 조각이 단순 개요인 경우 스킵 방지
                if (i === 0 && !sec.includes('\\n')) return;

                // 본문 파싱 및 추가
                html += robustParse((i > 0 ? '## ' : '') + sec);
                
                // 🚀 전략적 이미지 삽입 (섹션이 넘어갈 때마다 40% 확률로 다음 이미지 삽입, 혹은 마지막 섹션 전까지 분배)
                let imgIdx = i - 1;
                if(imgIdx >= 0 && imgIdx < otherImgs.length) {
                    html += `<div style="text-align:center; margin:80px 0; padding:40px; background:#f8fafc; border-radius:24px;"><img src="data:image/png;base64,${otherImgs[imgIdx].data}" style="width:100%; border-radius:20px; box-shadow:0 15px 40px rgba(0,0,0,0.1);"><div style="color:#64748b; font-size:18px; margin-top:20px; font-weight:600;">[Design Reference: ${otherImgs[imgIdx].label}]</div></div>`;
                }
            });
            
            html += `</div>`;
            return html;
        }

        const target = document.getElementById('render-target');
        target.innerHTML = `
            <div style="display:flex; gap:30px; margin-bottom:60px; max-width:1200px; margin-left:auto; margin-right:auto;">
                <button id="pdfBtn" style="flex:1; background:#4f46e5; color:white; border:none; padding:28px; border-radius:20px; font-weight:900; cursor:pointer; font-size:22px; box-shadow:0 12px 30px rgba(79,70,229,0.3); transition:all 0.3s;">📄 PDF 기획서로 저장 (인쇄용)</button>
                <button id="pngBtn" style="flex:1; background:#7c3aed; color:white; border:none; padding:28px; border-radius:20px; font-weight:900; cursor:pointer; font-size:22px; box-shadow:0 12px 30px rgba(124,58,237,0.3); transition:all 0.3s;">🖼️ 고화질 이미지 리포트 저장</button>
            </div>
            <div id="preview-box">${buildPremiumHTML(data)}</div>
        `;

        // PDF 및 이미지 저장 로직
        document.getElementById('pdfBtn').onclick = () => {
            const win = window.open('', '_blank');
            win.document.write('<html><head><meta charset="UTF-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css"></head><body style="margin:0; background:#f1f5f9; padding:0;">' + document.getElementById('export-area').outerHTML + '</body></html>');
            win.document.close();
            win.onload = () => setTimeout(() => { win.focus(); win.print(); }, 1200);
        };

        document.getElementById('pngBtn').onclick = () => {
            const btn = document.getElementById('pngBtn');
            const original = btn.innerText;
            btn.innerText = "⏳ 고해상도 렌더링 중 (약 5초)...";
            html2canvas(document.getElementById('export-area'), { 
                useCORS: true, 
                scale: 2.2, 
                backgroundColor: "#f1f5f9" 
            }).then(canvas => {
                const a = document.createElement('a');
                a.download = `VitoGDD_${data.title}.png`;
                a.href = canvas.toDataURL('image/png');
                a.click();
                btn.innerText = original;
            });
        };
    </script>
    """
    
    final_html = html_template.replace("ST_DATA_JSON", json.dumps(export_payload))
    components.html(final_html, height=5500, scrolling=True)

st.caption("비토쨩 연습하기")