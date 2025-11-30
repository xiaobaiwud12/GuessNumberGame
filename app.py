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
from io import BytesIO

# ... import ...
import sys # 确保导入了 sys

# --- 新增：获取真实的运行目录 ---
if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe，使用 exe 所在的文件夹
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    # 如果是脚本运行，使用当前脚本所在的文件夹
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 修改配置路径 ---
# 使用 os.path.join 拼接路径
DATA_FILE = os.path.join(ROOT_DIR, "users.json")
BG_IMAGE = os.path.join(ROOT_DIR, "bg.jpg")


# 页面配置必须在最前面
st.set_page_config(
    page_title="猜数字游戏",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------- 配置 ----------
DATA_FILE = "users.json"
BG_IMAGE = "bg.jpg"
SECRET_MIN, SECRET_MAX = 1, 100
LOLICON_API = "https://api.lolicon.app/setu/v2"

# ---------- 工具函数 ----------
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
    """从Lolicon API获取背景图片（横屏版本）"""
    # 中国大陆可用的反代列表（按优先级排序）
    proxy_list = [
        "i.pixiv.cat",      # 国内可用的反代1
        "i.pximg.net",      # 国内可用的反代2  
        "i.pixiv.re",       # 备用反代3
        "i-cf.pximg.net"    # Cloudflare反代
    ]
    
    for proxy in proxy_list:
        try:
            # 请求参数：r18=0 表示非R18内容
            params = {
                "r18": 0,
                "num": 5,  # 获取5张图片，增加找到横屏图的概率
                "size": ["original"],  # 请求原始尺寸
                "proxy": proxy  # 使用当前反代服务器
            }
            
            st.info(f"🔄 尝试使用反代: {proxy}")
            response = requests.get(LOLICON_API, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("error"):
                    st.warning(f"API错误: {data.get('error')}，尝试下一个反代...")
                    continue
                
                if data.get("data") and len(data["data"]) > 0:
                    # 筛选横屏图片（宽度 > 高度）
                    landscape_images = []
                    for artwork in data["data"]:
                        width = artwork.get('width', 0)
                        height = artwork.get('height', 0)
                        # 只选择横屏图片，且宽高比至少为 1.2:1
                        if width > height and width / height >= 1.2:
                            landscape_images.append(artwork)
                    
                    # 如果没有找到横屏图片，使用第一张
                    if not landscape_images:
                        st.info("⚠️ 未找到横屏图片，使用默认图片")
                        landscape_images = [data["data"][0]]
                    
                    # 尝试每一张横屏图片，直到成功下载
                    for artwork in landscape_images:
                        # 优先获取原始尺寸
                        image_url = None
                        if "urls" in artwork:
                            urls = artwork["urls"]
                            # 按优先级尝试：original > regular > small
                            image_url = urls.get("original") or urls.get("regular") or urls.get("small")
                        
                        if not image_url:
                            continue
                        
                        width = artwork.get('width', '?')
                        height = artwork.get('height', '?')
                        aspect_ratio = f"{width/height:.2f}:1" if isinstance(width, int) and isinstance(height, int) else "?"
                        
                        st.info(f"🎨 正在下载全尺寸横屏图片 (分辨率: {width}x{height}, 宽高比: {aspect_ratio})")
                        
                        # 设置请求头，模拟浏览器访问
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': 'https://www.pixiv.net/',
                            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                            'Accept-Encoding': 'gzip, deflate, br'
                        }
                        
                        try:
                            # 下载图片，全尺寸图片可能较大，给予充足时间
                            img_response = requests.get(image_url, headers=headers, timeout=45, stream=True)
                            
                            if img_response.status_code == 200:
                                # 保存图片
                                total_size = 0
                                with open(BG_IMAGE, 'wb') as f:
                                    for chunk in img_response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                            total_size += len(chunk)
                                
                                # 验证文件是否成功保存
                                if os.path.exists(BG_IMAGE) and os.path.getsize(BG_IMAGE) > 0:
                                    file_size = os.path.getsize(BG_IMAGE) / (1024 * 1024)  # MB
                                    st.success(f"✅ 全尺寸横屏图片下载成功！")
                                    st.success(f"📐 分辨率: {width}x{height} | 大小: {file_size:.2f}MB | 反代: {proxy}")
                                    return True
                                else:
                                    st.warning("文件保存失败，尝试下一张图片...")
                                    continue
                            elif img_response.status_code == 403:
                                st.warning(f"403 Forbidden，尝试下一个反代...")
                                break  # 403错误说明这个反代不可用，直接尝试下一个反代
                            elif img_response.status_code == 500:
                                st.warning(f"500 服务器错误，尝试下一张图片...")
                                continue
                            else:
                                st.warning(f"HTTP {img_response.status_code}，尝试下一张图片...")
                                continue
                                
                        except requests.exceptions.Timeout:
                            st.warning(f"⏱️ 下载超时（可能文件较大），尝试下一张图片...")
                            continue
                        except Exception as e:
                            st.warning(f"下载失败: {str(e)}，尝试下一张图片...")
                            continue
                    
                    # 当前反代的所有图片都下载失败，尝试下一个反代
                    st.warning(f"反代 {proxy} 的所有图片下载失败，尝试下一个反代...")
                    continue
                else:
                    st.warning(f"反代 {proxy} 未返回图片数据，尝试下一个反代...")
                    continue
            else:
                st.warning(f"反代 {proxy} API请求失败: HTTP {response.status_code}，尝试下一个反代...")
                continue
                
        except requests.exceptions.Timeout:
            st.warning(f"⏱️ 反代 {proxy} 请求超时，尝试下一个反代...")
            continue
        except requests.exceptions.RequestException as e:
            st.warning(f"🌐 反代 {proxy} 网络错误: {str(e)}，尝试下一个反代...")
            continue
        except Exception as e:
            st.warning(f"❌ 反代 {proxy} 发生错误: {str(e)}，尝试下一个反代...")
            continue
    
    # 所有反代都失败
    st.error("❌ 所有反代服务器都无法使用，请稍后重试或检查网络连接")
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
            margin: 0 !important;
            padding: 0 !important;
        }}
        """
    else:
        bg_css = """
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #243b55) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite;
            margin: 0 !important;
            padding: 0 !important;
            height: 100%;
        }
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        """

    css = f"""
    <style>
    /* ================= 全局重置 ================= */
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
        height: 100%;
    }}

    /* ================= 隐藏无关 UI ================= */
    header, footer, #MainMenu, .stDeployButton, [data-testid="stHeader"] {{
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
    }}
    
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], section[data-testid="stSidebar"] {{
        display: none !important;
    }}

    /* ================= 布局容器 ================= */
    .stApp {{
        background: transparent !important;
        margin: 0 !important;
        padding: 0 !important;
        top: 0 !important;
    }}
    
    .main, [data-testid="stAppViewContainer"], .block-container {{
        padding-top: 0 !important;
        margin-top: 0 !important;
        background: transparent !important;
    }}
    
    .block-container {{
        padding-bottom: 2rem !important;
        max-width: 900px !important;
    }}
    
    .center {{
        margin: 0 auto;
        padding: 10px;
        max-width: 900px;
    }}

    /* ================= 标题 ================= */
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
    
    h4 {{ margin-top: 15px !important; }}

    /* ================= 玻璃大卡片 ================= */
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

    /* ================= 自定义液态玻璃提示框 (核心修改) ================= */
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

    /* 🔴 红色液态玻璃 (猜小了) */
    .glass-alert-red {{
        background: rgba(255, 59, 48, 0.2); /* iOS Red Transparent */
        border-left: 5px solid rgba(255, 59, 48, 0.8);
        text-shadow: 0 0 10px rgba(255, 59, 48, 0.3);
    }}

    /* 🔵 蓝色液态玻璃 (猜大了) */
    .glass-alert-blue {{
        background: rgba(10, 132, 255, 0.2); /* iOS Blue Transparent */
        border-left: 5px solid rgba(10, 132, 255, 0.8);
        text-shadow: 0 0 10px rgba(10, 132, 255, 0.3);
    }}

    /* 🟢 绿色液态玻璃 (猜对了/成功) */
    .glass-alert-green {{
        background: rgba(48, 209, 88, 0.2); /* iOS Green Transparent */
        border-left: 5px solid rgba(48, 209, 88, 0.8);
        text-shadow: 0 0 10px rgba(48, 209, 88, 0.3);
    }}
    
    /* ⚠️ 黄色液态玻璃 (警告) */
    .glass-alert-yellow {{
        background: rgba(255, 159, 10, 0.2); /* iOS Yellow Transparent */
        border-left: 5px solid rgba(255, 159, 10, 0.8);
    }}

    /* ================= 输入框 (保持之前的核弹级去边框) ================= */
    .stTextInput div[data-baseweb="input"] {{
        background-color: transparent !important;
        border: none !important;
        border-radius: 20px !important;
        box-shadow: none !important;
    }}
    .stTextInput div[data-baseweb="input"]:focus-within {{
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    .stTextInput div[data-baseweb="base-input"] {{
        background-color: transparent !important;
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
        color: white !important;
        transform: translateY(-2px);
    }}
    .stTextInput input[type="password"] {{
        letter-spacing: 3px !important;
        font-weight: 600 !important;
    }}

    /* ================= 按钮 ================= */
    .stButton > button {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 14px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: white !important;
        color: white !important;
        transform: scale(1.02);
        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
    }}
    .stButton > button:active {{
        transform: scale(0.98);
        background: rgba(255, 255, 255, 0.15) !important;
    }}

    /* ================= 表格与Alert重置 ================= */
    .stTable table, .stTable th, .stTable td {{
        color: white !important;
        background: rgba(255,255,255,0.05) !important;
        border-color: rgba(255,255,255,0.1) !important;
    }}
    /* 通用 Alert 透明化 (作为默认样式的兜底) */
    [data-testid="stAlert"] {{
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: white !important;
        backdrop-filter: blur(10px);
    }}

    /* 移动端适配 */
    @media (max-width: 768px) {{
        .glass {{ padding: 20px; }}
        .title-outside h1 {{ font-size: 28px !important; }}
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

    # 使用自定义的 HTML/CSS 替代 st.info，实现真正的液态玻璃颜色
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
        # 猜对了
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
    ensure_session()
    users = load_users()
    
    # 检查并获取背景图片
    check_and_fetch_bg()
    
    inject_css(Path(BG_IMAGE).exists())

    st.markdown("<div class='center'>", unsafe_allow_html=True)
    
    # 标题在玻璃容器外
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

    st.markdown("</div></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()