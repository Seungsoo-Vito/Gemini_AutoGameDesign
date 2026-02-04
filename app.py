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
st.set_page_config(page_title="비토쨩 자동 기획서 연습 B-Ver", page_icon="🎮", layout="wide")

# --- 🎨 프리미엄 에디토리얼 UI 스타일링 (Streamlit 영역) ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #f1f5f9; color: #1e293b; font-family: 'Pretendard', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
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
        padding: 10px; 
        border-radius: 10px; 
        background: #f8fafc; 
        border: 1px solid #e2e8f0; 
        margin-bottom: 8px; 
        font-size: 0.85rem;
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
        "concept": f"A breathtaking high-quality masterpiece game key visual art, {genre}, theme: {key}, style: {art}. 8k resolution, cinematic lighting, professional digital art, epic scale.",
        "ui": f"High-fidelity professional mobile game UI/UX design mockup, {genre} HUD interface, style: {art}. Dashboard, inventory, clean layout, inspired by {key}. Digital game design sheet, 4k."
    }
    if prompt_type not in prompts: return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {
        "instances": {"prompt": prompts[prompt_type]}, 
        "parameters": {"sampleCount": 1}
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        if response.status_code == 200:
            result = response.json()
            return result["predictions"][0]["bytesBase64Encoded"]
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
            status = "준비됨" if v else "실패"
            st.markdown(f"""<div class='status-card'>{k.upper()}: <b style='color:{color}'>{status}</b></div>""", unsafe_allow_html=True)

# 메인 UI
st.markdown('<h1 class="main-title">비토쨩 자동 기획서 만들기 B-Ver 🎮</h1>', unsafe_allow_html=True)
st.write("제미나이를 활용한 연습. (좌측 텍스트 / 우측 이미지 분할 레이아웃)")
st.divider()

# 입력 섹션
with st.container():
    c1, c2 = st.columns(2)
    with c1: genre = st.selectbox("장르 선택", ["방치형 RPG", "수집형 RPG", "MMORPG", "로그라이크", "FPS/TPS", "전략 시뮬레이션"])
    with c2: target = st.selectbox("타겟 시장", ["글로벌", "한국", "일본", "북미", "유럽", "중국"])
    c3, c4 = st.columns(2)
    with c3: art = st.selectbox("아트 스타일", ["픽셀 아트 (Retro)", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크", "다크 판타지"])
    with c4: key = st.text_input("핵심 키워드", placeholder="예: 고양이, 타임루프")
    
    if st.button("B 버전 기획서 빌드 시작 ✨", type="primary", use_container_width=True):
        if not API_KEY: st.error("API 키를 입력하세요.")
        elif not key: st.warning("키워드를 입력하세요.")
        else:
            with st.spinner("텍스트와 이미지를 분리하여 정밀 렌더링 중입니다..."):
                model = genai.GenerativeModel('gemini-flash-latest')
                prompt = f"""
                당신은 전설적인 게임 기획자입니다. 장르={genre}, 국가={target}, 키워드={key}, 아트={art} 조건으로 전문 GDD를 작성하세요.
                
                [중요 지침]
                1. 섹션 제목은 반드시 '## 제목' 형식을 사용하세요.
                2. 본문의 **강조 텍스트**를 적극적으로 활용하세요.
                3. 전투 공식이나 성장 공식은 반드시 '$$ 공식 내용 $$' 형태의 LaTeX 문법으로 작성하세요.
                4. '## UI/UX 전략 및 인터페이스 설계' 섹션을 반드시 포함하세요.
                5. 위 섹션 하위에 '### UI/UX 목업' 항목을 만드세요.
                6. 복잡한 시스템 설명은 | 헤더 | 마크다운 표 형식으로 작성하세요.
                7. 의미 없는 '#' 한 줄 구분선은 절대 넣지 마세요.
                """
                gdd_res = model.generate_content(prompt)
                st.session_state['gdd_result'] = gdd_res.text
                
                # 이미지 생성
                st.session_state['generated_images'] = {
                    "concept": generate_hd_image("concept", genre, art, key),
                    "ui": generate_hd_image("ui", genre, art, key)
                }

# --- 🚀 [핵심] B 버전: 좌우 분할 렌더링 엔진 ---
if st.session_state['gdd_result']:
    st.divider()
    
    # 데이터 안전 전송
    safe_data = json.dumps({
        "title": f"{key.upper()} 기획안",
        "content": st.session_state['gdd_result'],
        "images": st.session_state['generated_images']
    }).replace("\\", "\\\\").replace("'", "\\'")

    html_code = """
    <style>
        /* 1. 기본 스타일 및 인쇄 설정 */
        @media print {
            .control-bar { display: none !important; }
            body { background: white !important; padding: 0 !important; }
            #capture-page { 
                box-shadow: none !important; border: none !important; 
                margin: 0 !important; width: 100% !important; max-width: none !important;
            }
        }
        
        body { background: #f1f5f9; padding: 20px; font-family: 'Pretendard', sans-serif; color: #1e293b; }
        
        /* 2. 상단 컨트롤 바 */
        .control-bar {
            max-width: 1400px; margin: 0 auto 30px auto;
            display: flex; gap: 20px;
        }
        .btn {
            flex: 1; padding: 20px; border-radius: 12px;
            font-size: 18px; font-weight: 900; cursor: pointer; border: none;
            transition: all 0.3s ease; color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .btn-pdf { background: #4f46e5; }
        .btn-img { background: #7c3aed; }
        .btn:hover { opacity: 0.9; transform: translateY(-1px); }

        /* 3. 문서 레이아웃 (좌우 분할) */
        #capture-page {
            background: white; padding: 80px 60px; border-radius: 30px;
            max-width: 1400px; margin: 0 auto;
            border: 1px solid #e2e8f0; box-shadow: 0 20px 50px rgba(0,0,0,0.05);
        }
        
        .main-header { text-align: center; margin-bottom: 70px; border-bottom: 10px solid #4f46e5; padding-bottom: 30px; }
        
        .split-container { display: flex; gap: 50px; align-items: flex-start; }
        
        /* 좌측: 기획서 텍스트 영역 */
        .text-column { flex: 0 0 65%; border-right: 2px solid #f1f5f9; padding-right: 40px; }
        
        /* 우측: 이미지 갤러리 영역 */
        .image-column { flex: 1; position: sticky; top: 40px; display: flex; flex-direction: column; gap: 40px; }

        /* 4. 세부 요소 스타일링 */
        h2 { font-size: 32px; font-weight: 800; color: #4f46e5; margin-top: 50px; margin-bottom: 25px; padding-left: 15px; border-left: 8px solid #4f46e5; background: #f8fafc; padding-top: 10px; padding-bottom: 10px; border-radius: 0 8px 8px 0; }
        h3 { font-size: 24px; font-weight: 700; color: #1e293b; margin-top: 35px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px; }
        p { font-size: 19px; line-height: 1.8; margin-bottom: 20px; text-align: justify; color: #334155; }
        
        .math-block { background: #f8faff; border: 1px solid #c7d2fe; padding: 25px; border-radius: 12px; text-align: center; font-size: 20px; font-weight: 700; margin: 30px 0; color: #3730a3; }
        
        table { width: 100%; border-collapse: collapse; margin: 25px 0; border-radius: 8px; overflow: hidden; font-size: 16px; }
        th { background: #4f46e5; color: white; padding: 12px; text-align: left; }
        td { padding: 12px; border-bottom: 1px solid #f1f5f9; color: #475569; border: 1px solid #f1f5f9; }

        .img-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 16px; text-align: center; }
        .img-card img { width: 100%; border-radius: 10px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
        .img-label { font-size: 14px; color: #64748b; font-weight: 700; margin-top: 12px; font-style: italic; }
        
        hr { border: none; border-top: 1px solid #e2e8f0; margin: 40px 0; }
    </style>

    <div class="control-bar">
        <button class="btn btn-pdf" onclick="window.print()">📄 PDF 기획서 저장</button>
        <button class="btn btn-img" id="capImg">🖼️ 고화질 이미지 저장</button>
    </div>

    <div id="capture-page">
        <div class="main-header">
            <h1 style="font-size: 60px; font-weight: 900; margin: 0; letter-spacing: -0.04em;">${data.title}</h1>
        </div>
        
        <div class="split-container">
            <!-- 좌측: 텍스트 및 시스템 설명 -->
            <div class="text-column" id="text-root"></div>
            
            <!-- 우측: 시각적 리소스 갤러리 -->
            <div class="image-column" id="image-root"></div>
        </div>
    </div>

    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
        (function() {
            const data = JSON.parse('ST_DATA_JSON');
            
            // 🚀 마크다운 텍스트 처리
            function parseContent(text) {
                return text.split('\\n').map(line => {
                    let l = line.trim();
                    if (!l || l === '#' || l === '##' || l === '###') return '';

                    // 수식 처리
                    if (l.startsWith('$$') && l.endsWith('$$')) {
                        return `<div class="math-block">${processInline(l.replace(/\\$\\$/g, ''))}</div>`;
                    }
                    
                    // 표 처리
                    if (l.startsWith('|')) {
                        const cells = l.split('|').filter(c => c.trim() !== '' || l.indexOf('|') !== l.lastIndexOf('|')).map(c => c.trim());
                        if (cells.length === 0 || l.includes('---')) return '';
                        return `<tr>${cells.map(c => `<td>${processInline(c)}</td>`).join('')}</tr>`;
                    }

                    // 제목 처리
                    if (l.startsWith('##')) {
                        return `<h2>${l.replace(/^##\s*/, '')}</h2>`;
                    }
                    if (l.startsWith('###')) {
                        return `<h3>${l.replace(/^###\s*/, '')}</h3>`;
                    }
                    
                    // 구분선
                    if (l === '---' || l === '***') return '<hr>';

                    return `<p>${processInline(l)}</p>`;
                }).join('');
            }

            function processInline(t) {
                return t
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color:#4f46e5; font-weight:800;">$1</strong>')
                    .replace(/\\\\text\{(.*?)\}/g, '$1')
                    .replace(/\\\\times/g, '×')
                    .replace(/\\\\cdot/g, '·');
            }

            function createImgCard(b64, label) {
                if (!b64) return '';
                const src = b64.startsWith('data:') ? b64 : `data:image/png;base64,${b64}`;
                return `
                    <div class="img-card">
                        <img src="${src}">
                        <div class="img-label">[REF: ${label}]</div>
                    </div>`;
            }

            // 빌드 실행
            const textRoot = document.getElementById('text-root');
            const imageRoot = document.getElementById('image-root');
            
            // 텍스트 렌더링
            let body = parseContent(data.content);
            body = body.replace(/(<tr>.*?<\\/tr>)+/g, m => `<div style="overflow-x:auto;"><table>${m}</table></div>`);
            textRoot.innerHTML = body;
            
            // 이미지 렌더링 (우측 배치)
            let imgHtml = "";
            imgHtml += createImgCard(data.images.concept, 'PROJECT KEY VISUAL');
            imgHtml += createImgCard(data.images.ui, 'UI/UX SYSTEM MOCKUP');
            imageRoot.innerHTML = imgHtml;

            // 저장 핸들러
            document.getElementById('capImg').onclick = function() {
                const btn = this;
                btn.innerText = "⏳ 렌더링 중...";
                html2canvas(document.getElementById('capture-page'), { scale: 2, useCORS: true }).then(canvas => {
                    const a = document.createElement('a');
                    a.download = `Vito_B_Report_${data.title}.png`;
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    btn.innerText = "🖼️ 고화질 이미지 저장";
                });
            };
        })();
    </script>
    """
    
    # 데이터 주입 및 출력
    final_html = html_code.replace("ST_DATA_JSON", safe_data)
    components.html(final_html, height=7000, scrolling=True)

st.caption("비토쨩 연습하기")