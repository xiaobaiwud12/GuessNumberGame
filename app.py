# app.py
import streamlit as st
import json
import os
import random
import hashlib
from pathlib import Path
from datetime import datetime
import base64
import requests
import sys

# 页面配置必须在最前面
st.set_page_config(
    page_title="猜数字游戏",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- 获取真实运行目录（支持EXE打包）----------
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，使用 exe 所在的文件夹
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行，使用当前脚本所在的文件夹
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- 配置 ----------
DATA_FILE = os.path.join(ROOT_DIR, "users.json")
BG_IMAGE = os.path.join(ROOT_DIR, "bg.jpg")
SECRET_MIN, SECRET_MAX = 1, 100
LOLICON_API = "https://api.lolicon.app/setu/v2"

# ---------- 工具函数 ----------
def create_kill_bat():
    """在程序目录生成一个【双击关闭程序.bat】"""
    # 只有在打包成 exe 运行时才执行此逻辑
    if getattr(sys, 'frozen', False):
        try:
            # 1. 获取当前运行的 exe 文件名 (例如 GuessNumberGame.exe)
            exe_name = os.path.basename(sys.executable)
            
            # 2. 定义 bat 文件路径 (在 exe 同级目录)
            bat_path = os.path.join(ROOT_DIR, "双击关闭程序.bat")
            
            # 3. 定义批处理内容
            # chcp 65001: 防止中文乱码
            # taskkill /F (强制) /IM (镜像名) /T (包括子进程)
            bat_content = f"""@echo off
chcp 65001 >nul
echo 正在关闭 {exe_name} ...
taskkill /F /IM "{exe_name}" /T
echo.
echo 程序已安全关闭。
timeout /t 2 >nul
exit
"""
            # 4. 写入文件 (使用 gbk 或 utf-8 均可，这里用 utf-8 配合 chcp 65001)
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
                
        except Exception as e:
            # 也就是静默失败，不影响主程序
            pass

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def load_users() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_users(users: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def ensure_session():
    ss = st.session_state
    ss.setdefault("logged_in", False)
    ss.setdefault("username", None)
    ss.setdefault("secret", None)
    ss.setdefault("guess_count", 0)
    ss.setdefault("login_error", 0)
    ss.setdefault("force_exit", False)
    ss.setdefault("game_ended", False)

def get_base64_of_bin_file(bin_file):
    """将图片文件转换为base64编码"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def fetch_lolicon_image():
    """从Lolicon API获取背景图片（横屏版本）- 支持多反代"""
    # 中国大陆可用的反代列表（按优先级排序）
    proxy_list = [
        "i.pixiv.cat",      # 国内可用的反代1
        "i.pximg.net",      # 国内可用的反代2  
        "i.pixiv.re",       # 备用反代3
        "i-cf.pximg.net"    # Cloudflare反代
    ]
    
    for proxy in proxy_list:
        try:
            params = {
                "r18": 0,
                "num": 10,
                "size": ["regular"],  # 使用regular更稳定
                "proxy": proxy
            }
            
            st.info(f"🔄 尝试使用反代: {proxy}")
            response = requests.get(LOLICON_API, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("error"):
                    st.warning(f"API错误，尝试下一个反代...")
                    continue
                
                if data.get("data") and len(data["data"]) > 0:
                    # 筛选横屏图片
                    landscape_images = []
                    for artwork in data["data"]:
                        width = artwork.get('width', 0)
                        height = artwork.get('height', 0)
                        if width > height and width / height >= 1.2:
                            landscape_images.append(artwork)
                    
                    if not landscape_images:
                        landscape_images = [data["data"][0]]
                    
                    # 尝试下载前3张横屏图片
                    for artwork in landscape_images[:3]:
                        image_url = None
                        if "urls" in artwork:
                            urls = artwork["urls"]
                            image_url = urls.get("regular") or urls.get("original") or urls.get("small")
                        
                        if not image_url:
                            continue
                        
                        width = artwork.get('width', '?')
                        height = artwork.get('height', '?')
                        aspect_ratio = f"{width/height:.2f}:1" if isinstance(width, int) and isinstance(height, int) else "?"
                        
                        st.info(f"🎨 正在下载横屏图片 ({width}x{height}, 宽高比: {aspect_ratio})")
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Referer': 'https://www.pixiv.net/',
                            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        }
                        
                        try:
                            img_response = requests.get(image_url, headers=headers, timeout=45, stream=True)
                            
                            if img_response.status_code == 200:
                                with open(BG_IMAGE, 'wb') as f:
                                    for chunk in img_response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                
                                if os.path.exists(BG_IMAGE) and os.path.getsize(BG_IMAGE) > 0:
                                    file_size = os.path.getsize(BG_IMAGE) / (1024 * 1024)
                                    st.success(f"✅ 图片下载成功！{width}x{height}, {file_size:.2f}MB, 反代: {proxy}")
                                    return True
                            elif img_response.status_code == 403:
                                st.warning(f"403错误，尝试下一个反代...")
                                break
                            else:
                                continue
                                
                        except requests.exceptions.Timeout:
                            st.warning(f"下载超时，尝试下一张...")
                            continue
                        except Exception as e:
                            st.warning(f"下载失败，尝试下一张...")
                            continue
                    
                    st.warning(f"反代 {proxy} 的图片下载失败，尝试下一个反代...")
                    continue
                    
        except Exception as e:
            st.warning(f"反代 {proxy} 发生错误，尝试下一个...")
            continue
    
    st.error("❌ 所有反代服务器都无法使用，请稍后重试")
    st.info("💡 提示：如果持续失败，可能需要使用VPN或等待服务恢复")
    return False

def check_and_fetch_bg():
    """检查背景图片，如果不存在则自动获取"""
    if not os.path.exists(BG_IMAGE):
        with st.spinner("🎨 正在获取背景图片..."):
            if fetch_lolicon_image():
                st.success("✅ 背景图片获取成功！")
                return True
            else:
                st.info("ℹ️ 使用默认渐变背景")
                return False
    return True

# ---------- 样式 ----------
def inject_css(bg_exists: bool):
    bg_css = ""
    if bg_exists and os.path.exists(BG_IMAGE):
        bg_base64 = get_base64_of_bin_file(BG_IMAGE)
        bg_css = f"""
        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            background-image: url('data:image/jpg;base64,{bg_base64}') !important;
            background-size: cover !important;
            background-attachment: fixed !important;
            background-position: center top !important;
            background-repeat: no-repeat !important;
        }}
        """
    else:
        bg_css = """
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #243b55) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite;
        }
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        """

    css = f"""
    <style>
    /* 全局重置 */
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    {bg_css}

    html, body {{
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden !important;
    }}

    /* 隐藏无关 UI */
    header, footer, #MainMenu, .stDeployButton, [data-testid="stHeader"],
    [data-testid="stToolbar"], [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"], section[data-testid="stSidebar"] {{
        display: none !important;
    }}

    .stApp, .main, [data-testid="stAppViewContainer"], .block-container {{
        padding-top: 0 !important;
        margin-top: 0 !important;
        background: transparent !important;
    }}
    
    .block-container {{
        max-width: 900px !important;
        padding-bottom: 2rem !important;
    }}

    /* 标题 */
    .title-outside {{
        text-align: center;
        margin-top: 40px;
        margin-bottom: 20px;
        padding: 0 10px;
    }}

    .title-outside h1 {{
        font-size: 36px !important;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
        color: white !important;
        text-shadow: 0 4px 20px rgba(0,0,0,0.6);
    }}

    .title-outside .subtitle {{
        font-size: 16px;
        color: rgba(255,255,255,0.95);
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }}

    h1, h2, h3, h4 {{
        color: white !important;
        text-shadow: 0 2px 12px rgba(0,0,0,0.4);
    }}

    /* 玻璃大卡片 */
    .glass {{
        padding: 30px;
        border-radius: 24px;
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-top: 1px solid rgba(255, 255, 255, 0.4);
        color: white;
        box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        margin: 20px 0;
    }}

    /* 自定义液态玻璃提示框 */
    .glass-alert {{
        padding: 16px 20px;
        border-radius: 16px;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        color: white;
        font-weight: 500;
        font-size: 15px;
        border: 1px solid rgba(255,255,255,0.2);
        animation: fadeIn 0.3s ease-out;
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(-5px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .glass-alert-red {{
        background: rgba(255, 59, 48, 0.2);
        border-left: 5px solid rgba(255, 59, 48, 0.8);
        text-shadow: 0 0 10px rgba(255, 59, 48, 0.3);
    }}

    .glass-alert-blue {{
        background: rgba(10, 132, 255, 0.2);
        border-left: 5px solid rgba(10, 132, 255, 0.8);
        text-shadow: 0 0 10px rgba(10, 132, 255, 0.3);
    }}

    .glass-alert-green {{
        background: rgba(48, 209, 88, 0.2);
        border-left: 5px solid rgba(48, 209, 88, 0.8);
        text-shadow: 0 0 10px rgba(48, 209, 88, 0.3);
    }}
    
    .glass-alert-yellow {{
        background: rgba(255, 159, 10, 0.2);
        border-left: 5px solid rgba(255, 159, 10, 0.8);
    }}

    /* 输入框 - 液态玻璃 */
    .stTextInput div[data-baseweb="input"],
    .stTextInput div[data-baseweb="input"]:focus-within,
    .stTextInput div[data-baseweb="base-input"] {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    
    .stTextInput input {{
        color: white !important;
        caret-color: white !important;
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.45) !important;
        border-radius: 20px !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    }}
    
    .stTextInput input::placeholder {{
        color: rgba(255, 255, 255, 0.6) !important;
        font-weight: 300 !important;
    }}
    
    .stTextInput input:focus {{
        background: rgba(20, 20, 20, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        border-color: rgba(255, 255, 255, 0.9) !important;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2), 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        transform: translateY(-2px);
    }}
    
    .stTextInput input[type="password"] {{
        letter-spacing: 3px !important;
        font-weight: 600 !important;
    }}

    /* ================= 按钮修复版 (解决点击闪烁问题) ================= */
    /* 1. 基础样式：作用于所有类型的按钮 */
    .stButton > button, 
    div.stButton > button:first-child {{
        background: rgba(255, 255, 255, 0.1) !important; /* 基础半透明 */
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 14px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        transition: transform 0.1s, background 0.2s, border-color 0.2s !important; /* 优化过渡 */
    }}

    /* 2. 悬停状态 (Hover) */
    .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.25) !important; /* 稍微变亮 */
        border-color: white !important;
        color: white !important;
        transform: scale(1.02) !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.3) !important;
    }}

    /* 3. 点击瞬间/激活状态 (Active) - 关键修复点 */
    /* 这里的背景色不能是不透明的，必须保持 rgba 格式 */
    .stButton > button:active,
    .stButton > button:focus:active {{
        background-color: rgba(255, 255, 255, 0.35) !important; /* 点击时更亮，但仍透明 */
        backdrop-filter: blur(12px) !important; /* 保持磨砂 */
        border-color: rgba(255, 255, 255, 0.6) !important;
        color: white !important;
        transform: scale(0.98) !important; /* 按下缩小效果 */
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }}

    /* 4. 聚焦状态 (Focus) - 点击后保留的状态 */
    /* 防止出现默认的红色/白色边框和背景 */
    .stButton > button:focus,
    .stButton > button:focus:not(:active) {{
        background: rgba(255, 255, 255, 0.1) !important; /* 回复到基础透明度 */
        border-color: rgba(255, 255, 255, 0.5) !important;
        color: white !important;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2) !important; /* 白色光晕替代默认红框 */
        outline: none !important;
    }}

    /* Radio按钮 */
    .stRadio > div {{
        flex-direction: row !important;
        gap: 12px !important;
    }}

    .stRadio > div > label {{
        color: white !important;
        background: rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(10px) !important;
        padding: 10px 18px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        transition: all 0.3s ease !important;
    }}

    .stRadio > div > label:hover {{
        background: rgba(255,255,255,0.2) !important;
        border-color: rgba(255,255,255,0.4) !important;
    }}

    /* 表格 - 液态玻璃效果 */
    .stTable {{
        border-radius: 16px;
        overflow: hidden;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }}
    
    .stTable table {{
        color: white !important;
        background: rgba(255,255,255,0.08) !important;
        backdrop-filter: blur(16px) saturate(150%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(150%) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }}
    
    .stTable thead {{
        background: rgba(255,255,255,0.15) !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
    }}
    
    .stTable th {{
        color: white !important;
        background: rgba(255,255,255,0.15) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-top: 1px solid rgba(255,255,255,0.35) !important;
        padding: 14px 16px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        text-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}
    
    .stTable tbody tr {{
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
    }}
    
    .stTable tbody tr:hover {{
        background: rgba(255,255,255,0.15) !important;
        transform: scale(1.01);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }}
    
    .stTable td {{
        color: white !important;
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
    }}
    
    /* 排行榜高亮样式 */
    .stTable tbody tr:first-child {{
        background: rgba(255, 215, 0, 0.12) !important;
        border-left: 3px solid rgba(255, 215, 0, 0.8) !important;
    }}
    .stTable tbody tr:first-child td {{
        background: rgba(255, 215, 0, 0.08) !important;
        font-weight: 600 !important;
    }}
    
    .stTable tbody tr:nth-child(2) {{
        background: rgba(192, 192, 192, 0.12) !important;
        border-left: 3px solid rgba(192, 192, 192, 0.8) !important;
    }}
    .stTable tbody tr:nth-child(2) td {{
        background: rgba(192, 192, 192, 0.08) !important;
        font-weight: 500 !important;
    }}
    
    .stTable tbody tr:nth-child(3) {{
        background: rgba(205, 127, 50, 0.12) !important;
        border-left: 3px solid rgba(205, 127, 50, 0.8) !important;
    }}
    .stTable tbody tr:nth-child(3) td {{
        background: rgba(205, 127, 50, 0.08) !important;
        font-weight: 500 !important;
    }}

    /* 响应式 */
    @media (max-width: 768px) {{
        .glass {{ padding: 20px; }}
        .title-outside h1 {{ font-size: 28px !important; }}
        .stTextInput input {{ font-size: 14px !important; }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
# ---------- 登录 / 注册 ----------
def do_login(users, username, pw):
    if username not in users:
        return False, "用户名不存在"
    if users[username]["password"] != hash_pw(pw):
        return False, "密码错误"
    return True, "登录成功"

def do_register(users, username, pw):
    if not username or not pw:
        return False, "用户名或密码不能为空"
    if username in users:
        return False, "用户名已存在"
    users[username] = {
        "password": hash_pw(pw),
        "best_score": None,
        "created_at": datetime.utcnow().isoformat()
    }
    save_users(users)
    return True, "注册成功"

# ---------- 游戏逻辑 ----------
def new_round():
    st.session_state.secret = random.randint(SECRET_MIN, SECRET_MAX)
    st.session_state.guess_count = 0
    st.session_state.game_ended = False

def do_guess(users, username, guess_text):
    if not guess_text:
        st.warning("⚠️ 请输入一个数字")
        return False

    if not guess_text.isdigit():
        st.warning("⚠️ 必须输入整数")
        return False

    guess = int(guess_text)
    if guess < SECRET_MIN or guess > SECRET_MAX:
        st.warning(f"⚠️ 范围是 {SECRET_MIN} ~ {SECRET_MAX}")
        return False

    st.session_state.guess_count += 1
    secret = st.session_state.secret

    if guess < secret:
        st.markdown(
            f"""
            <div class='glass-alert glass-alert-red'>
                📉 太小了，再试试！（你猜了 {guess}）
            </div>
            """, 
            unsafe_allow_html=True
        )
        return False
        
    elif guess > secret:
        st.markdown(
            f"""
            <div class='glass-alert glass-alert-blue'>
                📈 太大了，再试试！（你猜了 {guess}）
            </div>
            """, 
            unsafe_allow_html=True
        )
        return False
        
    else:
        st.markdown(
            f"""
            <div class='glass-alert glass-alert-green'>
                🎉 恭喜猜对！数字就是 {secret}，你用了 {st.session_state.guess_count} 次。
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.balloons()
        
        best = users[username].get("best_score")
        if best is None or st.session_state.guess_count < best:
            users[username]["best_score"] = st.session_state.guess_count
            save_users(users)
            st.markdown(
                """
                <div class='glass-alert glass-alert-yellow'>
                    🏆 哇！你创造了新的个人纪录！
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        st.session_state.game_ended = True
        return True

# ---------- 排行榜 ----------
def show_rank(users):
    data = []
    for name, d in users.items():
        if d.get("best_score") is not None:
            data.append((name, d["best_score"]))
    data.sort(key=lambda x: x[1])

    if not data:
        st.info("📊 暂无成绩，快来成为第一名吧！")
        return

    st.markdown("#### 🏆 排行榜")
    medals = ["🥇", "🥈", "🥉"]
    st.table([
        {
            "排名": f"{medals[i] if i < 3 else '🎖️'} {i + 1}",
            "用户": name,
            "最好成绩": f"{score} 次"
        }
        for i, (name, score) in enumerate(data)
    ])

# ---------- 主 UI ----------
def main():
    create_kill_bat()
    ensure_session()
    users = load_users()
    
    check_and_fetch_bg()
    inject_css(Path(BG_IMAGE).exists())

    st.markdown("<div class='center'>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='title-outside'>
        <h1>🎮 猜数字游戏</h1>
        <p class='subtitle'>iOS 液态玻璃风格 · 自动记录最好成绩 · 本地数据存储</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    if st.session_state.force_exit:
        st.error("🔒 密码连续错误三次，会话已停止。请刷新页面重新开始。")
        st.markdown("</div></div>", unsafe_allow_html=True)
        st.stop()

    if not st.session_state.logged_in:
        mode = st.radio("请选择操作", ["登录", "注册", "排行榜"], horizontal=True)

        if mode == "登录":
            st.markdown("#### 🔐 登录账号")
            username = st.text_input("用户名", placeholder="请输入用户名", key="login_user")
            pw = st.text_input("密码", type="password", placeholder="请输入密码", key="login_pw")

            if st.button("🚀 立即登录", use_container_width=True):
                ok, msg = do_login(users, username, pw)
                if ok:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.login_error = 0
                    new_round()
                    st.success("✅ 登录成功！")
                    st.rerun()
                else:
                    st.session_state.login_error += 1
                    remain = 3 - st.session_state.login_error
                    st.error(f"❌ {msg}（剩余尝试次数：{remain}）")
                    if st.session_state.login_error >= 3:
                        st.session_state.force_exit = True
                        st.rerun()

        elif mode == "注册":
            st.markdown("#### ✨ 创建新账号")
            username = st.text_input("新用户名", placeholder="请输入新用户名", key="reg_user")
            pw = st.text_input("新密码", type="password", placeholder="请输入新密码", key="reg_pw")

            if st.button("📝 立即注册", use_container_width=True):
                ok, msg = do_register(users, username, pw)
                if ok:
                    st.success("✅ 注册成功！请返回登录页面。")
                else:
                    st.error(f"❌ {msg}")

        else:
            show_rank(users)

    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**👤 当前用户：** {st.session_state.username}")
        with col2:
            if st.button("🚪 退出", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()

        best = users[st.session_state.username].get("best_score")
        st.markdown(f"**🏆 最好成绩：** {best if best is not None else '暂无'} {'次' if best else ''}")

        st.markdown("---")

        if st.session_state.game_ended:
            st.success("🎯 本轮游戏结束！")
            st.markdown(f"**📊 本轮成绩：** {st.session_state.guess_count} 次")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 再来一局", use_container_width=True):
                    new_round()
                    st.rerun()
            with col2:
                if st.button("📊 查看排行榜", use_container_width=True):
                    show_rank(users)
        else:
            st.markdown("#### 🎯 开始猜测")
            st.markdown(f"💡 猜一个 **{SECRET_MIN}~{SECRET_MAX}** 之间的数字")
            
            guess = st.text_input(
                "你的答案",
                placeholder="请输入1-100之间的数字",
                key="guess_input",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎯 提交猜测", use_container_width=True):
                    guessed_correctly = do_guess(users, st.session_state.username, guess)
                    if guessed_correctly:
                        st.rerun()
            with col2:
                if st.button("🔄 重新开始", use_container_width=True):
                    new_round()
                    st.rerun()
            
            st.markdown(f"**📝 已猜次数：** {st.session_state.guess_count}")

        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚪 退出登录", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()
        with col2:
            if st.button("🎨 更换背景", use_container_width=True):
                with st.spinner("🎨 正在获取新背景..."):
                    if fetch_lolicon_image():
                        st.success("✅ 背景更换成功！")
                        st.rerun()
                    else:
                        st.error("❌ 背景更换失败")

    st.markdown("</div></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()