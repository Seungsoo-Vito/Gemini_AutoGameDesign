import streamlit as st
import google.generativeai as genai
import requests
import base64
import json
import zlib
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="비토쨩 GDD Pro", page_icon="🎮", layout="wide")

# --- 🎨 커스텀 CSS (부드러운 파스텔 & 고가독성 디자인) ---
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 전체 배경 및 라이트 테마 설정 */
    .stApp {
        background-color: #fdfdfd;
        color: #2d3436;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }

    /* 사이드바 스타일 (부드러운 연그레이) */
    [data-testid="stSidebar"] {
        background-color: #f1f3f5;
        border-right: 1px solid #e9ecef;
    }
    
    /* 메인 타이틀 디자인 (파스텔 그라데이션) */
    .main-title {
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #ff9a9e 0%, #fad0c4 50%, #a1c4fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.05rem;
        margin-bottom: 0.5rem !important;
    }
    
    /* 카드형 컨테이너 (Soft White Card) */
    .gdd-card {
        background: #ffffff;
        border: 1px solid #f1f3f5;
        border-radius: 24px;
        padding: 40px;
        margin-bottom: 30px;
        box-shadow: 0 12px 24px rgba(149, 157, 165, 0.1);
    }
    
    /* 본문 가독성 설정 */
    .gdd-card p, .gdd-card li {
        font-size: 1.1rem !important;
        line-height: 1.8 !important;
        color: #4b5563 !important;
    }
    
    .gdd-card h1, .gdd-card h2, .gdd-card h3 {
        color: #1f2937 !important;
        margin-top: 1.8rem !important;
        margin-bottom: 1.2rem !important;
        border-bottom: 3px solid #e0e7ff;
        display: inline-block;
        padding-bottom: 4px;
    }

    /* 파스텔 버튼 스타일링 */
    div.stButton > button {
        border-radius: 14px;
        font-size: 1rem;
        font-weight: 700;
        height: 3.2rem;
        transition: all 0.25s ease;
        border: none;
    }
    
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
        color: #4b5563;
        box-shadow: 0 4px 12px rgba(161, 196, 253, 0.3);
    }
    
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(161, 196, 253, 0.5);
        color: #1e293b;
    }

    /* 히스토리 아이템 (파스텔 포인트) */
    .history-item {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        transition: all 0.2s;
    }
    .history-item:hover {
        border-color: #a1c4fd;
        background-color: #f8faff;
    }
    
    /* 입력 위젯 스타일 */
    .stSelectbox label, .stTextInput label {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #64748b !important;
    }

    /* 구글 슬라이드 전용 버튼 스타일 */
    .google-slide-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #ffffff;
        color: #5f6368;
        border: 1px solid #dadce0;
        padding: 15px 25px;
        border-radius: 14px;
        text-decoration: none;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.2s;
        width: 100%;
        text-align: center;
    }
    .google-slide-btn:hover {
        background-color: #f8f9fa;
        border-color: #34a853;
        color: #34a853;
        box-shadow: 0 4px 12px rgba(52, 168, 83, 0.2);
    }

    /* 구분선 */
    hr { border-color: #f1f3f5 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔒 API 설정 ---
# 승수님, 아래 따옴표 안에 API 키를 정확히 입력해 주세요.
API_KEY = "AIzaSyBpUR0gl_COhxbFPWxTiW6JJMuGgDF4Ams" 

if API_KEY.strip():
    genai.configure(api_key=API_KEY.strip())

# --- 🎨 이미지 생성 함수 (Imagen 4.0 사용) ---
def generate_game_image(prompt_text):
    current_key = API_KEY.strip()
    if not current_key:
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={current_key}"
    payload = {
        "instances": [{"prompt": prompt_text}],
        "parameters": {"sampleCount": 1}
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        if "predictions" in result:
            return result["predictions"][0]["bytesBase64Encoded"]
    except:
        return None
    return None

# --- 📋 클립보드 복사 자바스크립트 ---
def copy_content_to_clipboard(text):
    text_json = json.dumps(text)
    js_code = f"""
    <script>
    const textToCopy = {text_json};
    const el = document.createElement('textarea');
    el.value = textToCopy;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    alert('기획서 본문이 클립보드에 복사되었습니다!\\n구글 슬라이드 편집창에서 붙여넣기(Ctrl+V) 하세요.');
    </script>
    """
    components.html(js_code, height=0)

# --- 🔗 공유 데이터 인코딩/디코딩 ---
def encode_data(data_dict):
    json_str = json.dumps(data_dict)
    compressed = zlib.compress(json_str.encode())
    return base64.urlsafe_b64encode(compressed).decode()

def decode_data(encoded_str):
    try:
        decoded = base64.urlsafe_b64decode(encoded_str.encode())
        decompressed = zlib.decompress(decoded)
        return json.loads(decompressed.decode())
    except:
        return None

# 세션 상태 초기화
if 'gdd_result' not in st.session_state:
    st.session_state['gdd_result'] = None
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'generated_images' not in st.session_state:
    st.session_state['generated_images'] = {}
if 'editing_index' not in st.session_state:
    st.session_state['editing_index'] = -1

# 2. 공유 링크 확인
if "shared_data" in st.query_params:
    encoded_data = st.query_params["shared_data"]
    shared_content = decode_data(encoded_data)
    if shared_content:
        st.session_state['gdd_result'] = shared_content.get('content')
        st.session_state['shared_keywords'] = shared_content.get('keywords', 'Shared GDD')
        st.session_state['generated_images'] = {} 

# 3. 웹 화면 UI 구성
st.markdown('<h1 class="main-title">비토쨩 GDD Pro</h1>', unsafe_allow_html=True)
st.write("감성적인 파스텔 톤의 전문 게임 기획서 제작 도구")
st.divider()

# 사이드바 설정
with st.sidebar:
    st.header("🎨 테마 & 설정")
    st.write("부드러운 파스텔 테마가 적용되었습니다.")
    detail_level = st.select_slider("상세도 설정", options=["표준", "상세", "전문가"])
    
    st.divider()
    st.header("🕒 기획 기록")
    if not st.session_state['history']:
        st.write("기록이 비어 있습니다.")
    else:
        for i in range(len(st.session_state['history']) - 1, -1, -1):
            item = st.session_state['history'][i]
            display_name = item.get('custom_name') or f"{item['keywords']}"
            
            with st.container():
                st.markdown(f'<div class="history-item">', unsafe_allow_html=True)
                col_main, col_tools = st.columns([3, 1.5])
                if col_main.button(f"📄 {display_name[:10]}", key=f"hist_l_{i}", use_container_width=True):
                    st.session_state['gdd_result'] = item['content']
                    st.session_state['generated_images'] = item.get('images', {})
                    st.session_state['editing_index'] = -1
                    if "shared_data" in st.query_params:
                        st.query_params.clear()
                
                edit_cols = col_tools.columns(2)
                if edit_cols[0].button("✏️", key=f"h_e_{i}"):
                    st.session_state['editing_index'] = i
                    st.rerun()
                if edit_cols[1].button("🔗", key=f"h_s_{i}"):
                    share_payload = {"content": item['content'], "keywords": item['keywords']}
                    encoded = encode_data(share_payload)
                    st.query_params["shared_data"] = encoded
                    st.success("링크 생성!")

                if st.session_state['editing_index'] == i:
                    new_name = st.text_input("수정", value=display_name, key=f"h_n_i_{i}")
                    if st.button("저장", key=f"h_s_b_{i}"):
                        st.session_state['history'][i]['custom_name'] = new_name
                        st.session_state['editing_index'] = -1
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        if st.button("모든 기록 비우기", use_container_width=True):
            st.session_state['history'] = []
            st.rerun()

# 4. 입력창 및 생성 로직
if "shared_data" in st.query_params:
    st.info("💡 공유받은 문서를 읽고 있습니다.")
    if st.button("새로 만들기", type="secondary"):
        st.query_params.clear()
        st.session_state['gdd_result'] = None
        st.rerun()
else:
    with st.container():
        st.markdown('<div class="gdd-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            genre = st.selectbox("장르", ["방치형 RPG", "수집형 RPG", "오픈월드", "로그라이크", "매치3 퍼즐", "액션 어드벤처"])
            target = st.selectbox("국가", ["글로벌", "한국", "일본", "북미/유럽"])
        with col2:
            art_style = st.selectbox("스타일", ["픽셀 아트", "2D 카툰", "실사풍", "3D 캐주얼", "사이버펑크"])
            keywords = st.text_input("키워드", placeholder="예: 고양이, 타임루프")
        with col3:
            st.write("") 
            st.write("") 
            generate_btn = st.button("기획서 생성하기 ✨", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if generate_btn:
        final_key = API_KEY.strip()
        if not final_key:
            st.error("코드 상단의 API_KEY 변수에 키를 입력해 주세요.")
        elif not keywords:
            st.warning("키워드를 입력해 주세요.")
        else:
            with st.spinner("비토쨩이 감성을 담아 기획 중..."):
                genai.configure(api_key=final_key)
                prompt = f"""당신은 15년 경력의 시니어 게임 PM입니다. 
                장르: {genre}, 타겟: {target}, 키워드: {keywords}, 아트 스타일: {art_style} 
                조건으로 전문적인 GDD를 한국어로 작성하세요. 문서 수준: {detail_level}."""
                try:
                    model = genai.GenerativeModel('gemini-flash-latest')
                    response = model.generate_content(prompt)
                    result_text = response.text
                    
                    img_prompts = {
                        "main": f"Soft pastel game concept art, {genre}, {art_style}, theme of {keywords}. Watercolor style, soft lighting, 8k.",
                        "world": f"Soft pastel environment art, {genre} game world, {keywords}. Dreamy atmosphere, pastel palette.",
                        "ui": f"Soft pastel game UI design, mobile {genre}, {art_style}, matching {keywords} color scheme."
                    }
                    
                    images = {}
                    for key, p in img_prompts.items():
                        img_b64 = generate_game_image(p)
                        if img_b64: images[key] = img_b64
                    
                    st.session_state['gdd_result'] = result_text
                    st.session_state['generated_images'] = images
                    st.session_state['history'].append({
                        "keywords": keywords, "genre": genre, "content": result_text, "images": images, "custom_name": None
                    })
                except Exception as e:
                    st.error(f"오류: {e}")

# 5. 결과 출력 섹션
if st.session_state['gdd_result']:
    st.divider()
    
    sections = st.session_state['gdd_result'].split('\n\n')
    images = st.session_state['generated_images']
    
    for i, section in enumerate(sections):
        if not section.strip(): continue
            
        st.markdown(f'<div class="gdd-card">', unsafe_allow_html=True)
        st.markdown(section)
        
        # 이미지 출력 로직 (사이즈 조절 및 중앙 정렬)
        show_img = False
        img_data = None
        
        if i == 0 and images.get("main"):
            show_img = True
            img_data = images["main"]
        elif ("World" in section or "세계관" in section) and images.get("world"):
            show_img = True
            img_data = images["world"]
        elif ("UI" in section or "인터페이스" in section) and images.get("ui"):
            show_img = True
            img_data = images["ui"]
        
        if show_img:
            img_cols = st.columns([1, 2, 1])
            img_cols[1].image(base64.b64decode(img_data), width=600)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # 🚀 구글 슬라이드 제작 도구 섹션
    st.divider()
    st.subheader("🚀 구글 슬라이드 기획서 만들기")
    st.info("아래 버튼을 순서대로 눌러 전문가용 슬라이드 기획서를 완성하세요.")
    
    col_slide_a, col_slide_b = st.columns(2)
    
    with col_slide_a:
        if st.button("📋 1단계: 기획서 내용 복사하기", use_container_width=True):
            copy_content_to_clipboard(st.session_state['gdd_result'])

    with col_slide_b:
        # 전문가용 슬라이드 템플릿 복사 링크
        template_url = "https://docs.google.com/presentation/d/1B-iO8pY6X0i-W_l88S7XpE79_v7Yn_6tD9_k-07W07U/copy"
        st.markdown(f"""
            <a href="{template_url}" target="_blank" class="google-slide-btn">
                <img src="https://upload.wikimedia.org/wikipedia/commons/1/16/Google_Slides_2020_Logo.svg" width="22" style="margin-right:12px;">
                2단계: 구글 슬라이드 템플릿 열기
            </a>
            """, unsafe_allow_html=True)

st.caption("비토쨩 GDD Pro | Google Slides Edition | Powered by Google AI")