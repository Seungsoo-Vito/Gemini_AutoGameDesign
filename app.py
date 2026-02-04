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

# --- 🎨 프리미엄 에디토리얼 UI 스타일링 (Ultra-Wide) ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Pretendard', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .main-title {
        font-size: calc(2.5rem + 2vw) !important; font-weight: 900 !important;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0.5rem !important;
    }
    div.stButton > button {
        border-radius: 12px !important; font-weight: 700 !important;
        transition: all 0.2s; height: 3.8rem;
    }
    .status-card {
        padding: 12px; border-radius: 10px; background: #f8fafc; border: 1px solid #e2e8f0; margin-bottom: 8px; font-size: 0.9rem;
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

# --- 🎨 고화질 이미지 엔진 (Imagen 4.0) ---
def generate_hd_image(prompt_type, genre, art, key):
    if not API_KEY: return None
    prompts = {
        "concept": f"Masterpiece cinematic game key visual, {genre}, theme: {key}, style: {art}. 8k resolution, professional game lighting, epic scale, concept art.",
        "ui": f"Professional High-fidelity mobile game UI design mockup, {genre}, style: {art}. Clean layout, inventory, dashboard, inspired by {key}.",
        "world": f"Environment concept art, immersive game world of {genre}, theme: {key}, style: {art}. Beautiful landscape, masterpiece lighting.",
        "character": f"High-quality character concept portrait, {genre} hero, motif: {key}, style: {art}. Professional asset sheet design."
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {"instances": [{"prompt": prompts.get(prompt_type, prompts["concept"])}], "parameters": {"sampleCount": 1}}
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()["predictions"][0]["bytesBase64Encoded"]
    except: pass
    return None

# 세션 상태
if 'gdd_result' not in st.session_state: st.session_state['gdd_result'] = None
if 'generated_images' not in st.session_state: st.session_state['generated_images'] = {}

# 사이드바 결과 분석
with st.sidebar:
    if st.session_state['generated_images']:
        st.divider()
        st.header("🖼️ 생성 이미지 분석")
        for k, v in st.session_state['generated_images'].items():
            color = "#10b981" if v else "#ef4444"
            st.markdown(f"<div class='status-card'>{k.upper()}: <b style='color:{color}'>{'준비됨' if v else '실패'}</b></div>", unsafe_allow_html=True)

# 메인 UI
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습.")
st.divider()

# 입력 섹션
with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "FPS/TPS", "전략 시뮬레이션"])
    with c2: target = st.selectbox("타겟 시장", ["글로벌", "한국", "일본", "북미", "유럽", "중국"])
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", ["픽셀 아트 (Retro)", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프, 지하철")
    
    if st.button("고품격 기획서 빌드 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력하세요.")
        elif not key: st.warning("키워드를 입력하세요.")
        else:
            with st.spinner("전문 기획자가 모든 텍스트와 아트를 완벽하게 렌더링 중입니다 (최대 2분 소요)..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 시니어 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문 GDD를 작성하세요.
                
                [중요 지침]
                1. 섹션 제목은 반드시 '## 제목' 형식을 사용하세요.
                2. 본문의 **강조 텍스트**를 적극적으로 활용하되 마크다운 기호가 그대로 남지 않도록 주의하세요.
                3. 의미 없는 '#' 한 줄 구분선은 절대 넣지 마세요.
                4. 전투 공식, 시너지 시스템, 경제 구조를 매우 구체적으로 기술하세요.
                5. 복잡한 시스템이나 흐름은 반드시 | 헤더 | 마크다운 표 형식으로 작성하세요.
                """
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # 이미지 생성
                st.session_state['generated_images'] = {
                    "concept": generate_hd_image("concept", genre, art, key),
                    "world": generate_hd_image("world", genre, art, key),
                    "ui": generate_hd_image("ui", genre, art, key),
                    "character": generate_hd_image("character", genre, art, key)
                }

# --- 🚀 [핵심] 마크다운 정화, 이미지 강제 출력, 표 렌더링 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    # 데이터 안전 전송
    safe_data = json.dumps({
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }).replace("\\", "\\\\").replace("'", "\\'")

    html_code = """
    <div id="root-container"></div>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {
            const data = JSON.parse('ST_DATA_JSON');
            
            // 🚀 마크다운 기호 제거 및 고품격 태그 변환기 (표 지원)
            function formatText(text) {
                const lines = text.split('\\n');
                let result = [];
                let inTable = false;
                let tableData = [];

                function flushTable() {
                    if (tableData.length === 0) return '';
                    let html = '<div style="margin:30px 0; overflow-x:auto;"><table style="width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; box-shadow:0 4px 15px rgba(0,0,0,0.05);">';
                    tableData.forEach((row, idx) => {
                        const cells = row.split('|').filter(c => c.trim() !== '' || row.indexOf('|') !== row.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0) return;
                        if (row.includes('---')) return; // 구분선 스킵

                        if (idx === 0) {
                            html += '<thead style="background:#4f46e5; color:white;"><tr>';
                            cells.forEach(c => html += `<th style="padding:18px 20px; text-align:left; font-weight:700;">${processInline(c)}</th>`);
                            html += '</tr></thead><tbody>';
                        } else {
                            html += '<tr style="border-bottom:1px solid #f1f5f9;">';
                            cells.forEach(c => html += `<td style="padding:18px 20px; font-size:18px; color:#334155;">${processInline(c)}</td>`);
                            html += '</tr>';
                        }
                    });
                    html += '</tbody></table></div>';
                    return html;
                }

                function processInline(t) {
                    return t.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:800;">$1</strong>');
                }

                lines.forEach(line => {
                    let l = line.trim();
                    if (!l || l === '#' || l === '##') {
                        if (inTable) { result.push(flushTable()); tableData = []; inTable = false; }
                        return;
                    }

                    // 표 감지
                    if (l.startsWith('|')) {
                        inTable = true;
                        tableData.push(l);
                        return;
                    } else if (inTable) {
                        result.push(flushTable());
                        tableData = [];
                        inTable = false;
                    }

                    // ## 제목 변환
                    if (l.startsWith('##')) {
                        result.push(`<h2 style="font-size:36px; font-weight:900; color:#4f46e5; border-left:12px solid #4f46e5; padding-left:25px; background:#f8fafc; margin-top:80px; margin-bottom:30px; border-radius:0 15px 15px 0;">${l.replace(/^##\s*/, '')}</h2>`);
                    }
                    // ### 소제목 변환
                    else if (l.startsWith('###')) {
                        result.push(`<h3 style="font-size:24px; font-weight:700; color:#1e293b; margin-top:40px; border-bottom:2px solid #f1f5f9; padding-bottom:12px;">${l.replace(/^###\s*/, '')}</h3>`);
                    }
                    // 불렛 포인트
                    else if (l.startsWith('* ') || l.startsWith('- ')) {
                        result.push(`<li style="font-size:21px; color:#475569; margin-bottom:15px; margin-left:25px; line-height:1.6; list-style-type:square;">${processInline(l.replace(/^[*|-]\s*/, ''))}</li>`);
                    }
                    // 일반 본문
                    else {
                        result.push(`<p style="font-size:21px; color:#334155; line-height:1.9; text-align:justify; margin-bottom:25px;">${processInline(l)}</p>`);
                    }
                });

                if (inTable) result.push(flushTable());
                return result.join('');
            }

            function imgBox(b64, label) {
                if (!b64) return '';
                const src = b64.startsWith('data:') ? b64 : `data:image/png;base64,${b64}`;
                return `
                    <div style="text-align:center; margin:90px 0; padding:40px; background:#f8fafc; border-radius:32px; border:1px solid #e2e8f0;">
                        <img src="${src}" style="width:100%; max-width:1100px; border-radius:20px; box-shadow:0 25px 50px rgba(0,0,0,0.15);">
                        <div style="color:#64748b; font-size:18px; margin-top:25px; font-weight:700; font-style:italic; letter-spacing:1px;">[REFERENCE: ${label}]</div>
                    </div>`;
            }

            function renderAll() {
                const root = document.getElementById('root-container');
                
                let btns = `
                    <div style="display:flex; gap:30px; margin-bottom:60px; max-width:1200px; margin:0 auto;">
                        <button onclick="window.print()" style="flex:1; background:#4f46e5; color:white; border:none; padding:30px; border-radius:20px; font-weight:900; cursor:pointer; font-size:22px; box-shadow:0 12px 30px rgba(79,70,229,0.3);">📄 PDF 문서로 저장하기</button>
                        <button id="imgDown" style="flex:1; background:#7c3aed; color:white; border:none; padding:30px; border-radius:20px; font-weight:900; cursor:pointer; font-size:22px; box-shadow:0 12px 30px rgba(124,58,237,0.3);">🖼️ 전체 리포트 이미지 저장</button>
                    </div>`;

                let doc = `<div id="capture-page" style="background:white; padding:120px 100px; border-radius:40px; font-family:'Pretendard', sans-serif; color:#1e293b; max-width:1200px; margin:0 auto; border:1px solid #e2e8f0; box-shadow:0 40px 80px rgba(0,0,0,0.08);">`;
                
                doc += `<h1 style="font-size:80px; font-weight:900; text-align:center; border-bottom:15px solid #4f46e5; padding-bottom:50px; margin-bottom:100px; letter-spacing:-0.05em;">${data.title}</h1>`;
                
                doc += imgBox(data.images.concept, 'PROJECT KEY VISUAL');
                
                const parts = data.content.split('## ');
                const availableImages = [
                    { data: data.images.world, lbl: 'WORLD CONCEPT' },
                    { data: data.images.ui, lbl: 'UI/UX MOCKUP' },
                    { data: data.images.character, lbl: 'CHARACTER DESIGN' }
                ].filter(x => x.data);

                parts.forEach((sec, i) => {
                    if (!sec.trim()) return;
                    doc += formatText((i > 0 ? '## ' : '') + sec);
                    
                    if (i % 2 === 1 && availableImages.length > 0) {
                        const nextImg = availableImages.shift();
                        doc += imgBox(nextImg.data, nextImg.lbl);
                    }
                });

                doc += `</div>`;
                root.innerHTML = btns + doc;

                document.getElementById('imgDown').onclick = function() {
                    this.innerText = "⏳ 고화질 렌더링 중 (잠시만 기다려주세요)...";
                    html2canvas(document.getElementById('capture-page'), { scale: 2, useCORS: true }).then(canvas => {
                        const a = document.createElement('a');
                        a.download = `GDD_REPORT_${data.title}.png`;
                        a.href = canvas.toDataURL('image/png');
                        a.click();
                        this.innerText = "🖼️ 전체 리포트 이미지 저장";
                    });
                };
            }

            renderAll();
        })();
    </script>
    """
    
    final_html = html_code.replace("ST_DATA_JSON", safe_data)
    components.html(final_html, height=6000, scrolling=True)

st.caption("비토쨩 연습하기")