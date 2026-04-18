# user_app/app_user.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from common.data_processor import DataProcessor
from supabase import create_client, Client
import numpy as np
from datetime import datetime, timedelta
import random
import math

# ------------------ Supabase 客户端初始化 ------------------
def get_supabase_client():
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Supabase 连接失败: {e}\n请检查 .streamlit/secrets.toml 配置")
        return None

supabase = get_supabase_client()

# ------------------ 数据库操作函数（保持不变） ------------------
def register_user(username, password):
    if not username or not password:
        return False, "用户名和密码不能为空"
    if supabase is None:
        return False, "数据库连接失败"
    try:
        existing = supabase.table("users").select("*").eq("username", username).execute()
        if existing.data:
            return False, "用户名已存在"
        supabase.table("users").insert({"username": username, "password": password}).execute()
        return True, "注册成功"
    except Exception as e:
        print(f"注册失败: {e}")
        return False, f"注册失败: {e}"

def check_login(username, password):
    if not username or not password:
        return False, "用户名和密码不能为空"
    if supabase is None:
        return False, "数据库连接失败"
    try:
        resp = supabase.table("users").select("password").eq("username", username).execute()
        if resp.data and resp.data[0]["password"] == password:
            return True, "登录成功"
        else:
            return False, "用户名或密码错误"
    except Exception as e:
        print(f"登录失败: {e}")
        return False, "系统错误"

def insert_charging_history(username, station_name, date, cost):
    if supabase is None:
        return False
    try:
        supabase.table("charging_history").insert({
            "username": username,
            "station_name": station_name,
            "date": date,
            "cost": cost
        }).execute()
        return True
    except Exception as e:
        print(f"插入充电历史失败: {e}")
        return False

def get_charging_history(username):
    if supabase is None:
        return pd.DataFrame()
    try:
        resp = supabase.table("charging_history")\
            .select("date, station_name, cost")\
            .eq("username", username)\
            .order("date", desc=True)\
            .execute()
        if resp.data:
            return pd.DataFrame(resp.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"读取充电历史失败: {e}")
        return pd.DataFrame()

def insert_appointment(username, station_name, date, time):
    if supabase is None:
        return False, "数据库连接失败"
    try:
        supabase.table("appointments").insert({
            "username": username,
            "station_name": station_name,
            "date": date,
            "time": time,
            "status": "有效"
        }).execute()
        return True, "预约成功"
    except Exception as e:
        print(f"插入预约失败: {e}")
        return False, str(e)

def get_appointments(username, status='有效'):
    if supabase is None:
        return pd.DataFrame()
    try:
        resp = supabase.table("appointments")\
            .select("*")\
            .eq("username", username)\
            .eq("status", status)\
            .order("date")\
            .order("time")\
            .execute()
        if resp.data:
            return pd.DataFrame(resp.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"读取预约失败: {e}")
        return pd.DataFrame()

def cancel_appointment(appointment_id):
    if supabase is None:
        return False
    try:
        supabase.table("appointments")\
            .update({"status": "已取消"})\
            .eq("id", appointment_id)\
            .execute()
        return True
    except Exception as e:
        print(f"取消预约失败: {e}")
        return False

def insert_feedback(username, fb_type, location, message):
    if 'local_feedbacks' not in st.session_state:
        st.session_state.local_feedbacks = []
    new_fb = {
        "username": username,
        "type": fb_type,
        "location": location,
        "message": message,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db_success = False
    if supabase is not None:
        try:
            supabase.table("feedbacks").insert(new_fb).execute()
            db_success = True
        except Exception as e:
            print(f"数据库写入反馈失败: {e}")
    st.session_state.local_feedbacks.append(new_fb)
    return True, "反馈已提交，感谢您的建议！"

def get_feedbacks(limit=20):
    all_feedbacks = []
    if supabase is not None:
        try:
            resp = supabase.table("feedbacks").select("*").order("created_at", desc=True).limit(limit).execute()
            if resp.data:
                all_feedbacks.extend(resp.data)
        except Exception as e:
            print(f"读取反馈失败: {e}")
    if 'local_feedbacks' in st.session_state:
        all_feedbacks.extend(st.session_state.local_feedbacks)
    seen = set()
    unique = []
    for fb in all_feedbacks:
        key = (fb.get('username'), fb.get('message'), fb.get('created_at'))
        if key not in seen:
            seen.add(key)
            unique.append(fb)
    unique.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return pd.DataFrame(unique[:limit])

# ------------------ 页面配置 ------------------
st.set_page_config(
    page_title="智能充电导航",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ 响应式 CSS（电脑/手机自适应） ------------------
st.markdown("""
<style>
    /* 全局基础变量 */
    :root {
        --card-radius: 16px;
    }
    /* 电脑默认样式 */
    body {
        font-size: 16px;
    }
    /* 卡片网格布局：电脑3列，手机自动1列 */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1rem 0;
    }
    /* 手机样式 */
    @media (max-width: 768px) {
        body, .stMarkdown, .stText, .stButton button {
            font-size: 14px !important;
        }
        .card-grid {
            grid-template-columns: 1fr !important;
            gap: 0.75rem;
        }
        .stDataFrame {
            font-size: 12px;
        }
        iframe {
            height: 40vh !important;
        }
        .stButton button {
            min-height: 44px;
        }
        .stSidebar {
            width: 100% !important;
        }
        [data-testid="stSidebar"] {
            min-width: 100% !important;
        }
        .feedback-card {
            padding: 8px !important;
        }
        h1 {
            font-size: 1.6rem !important;
        }
        h2 {
            font-size: 1.3rem !important;
        }
        h3 {
            font-size: 1.1rem !important;
        }
        .desktop-only {
            display: none;
        }
    }
    @media (min-width: 769px) {
        .mobile-only {
            display: none;
        }
    }
    /* 卡片样式 */
    .charger-card {
        background-color: #FFFFFF;
        border-radius: var(--card-radius);
        padding: 12px 16px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: 0.1s;
    }
    .charger-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .card-title {
        font-weight: 700;
        font-size: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .card-type {
        background-color: #E3F2FD;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
    }
    .card-stats {
        display: flex;
        gap: 12px;
        margin-top: 8px;
        font-size: 0.75rem;
        flex-wrap: wrap;
    }
    .progress-bar {
        background-color: #E5E7EB;
        border-radius: 20px;
        height: 6px;
        margin-top: 8px;
    }
    .progress-fill {
        height: 6px;
        border-radius: 20px;
    }
    [data-testid="stSidebar"] {
        padding: 1rem 0.5rem;
    }
</style>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
""", unsafe_allow_html=True)

# ------------------ 获取屏幕宽度（用于动态布局） ------------------
try:
    from streamlit_js_eval import get_geolocation, get_window_width
    if 'screen_width' not in st.session_state:
        width = get_window_width()
        if width:
            st.session_state.screen_width = width
        else:
            st.session_state.screen_width = 1200
except ImportError:
    st.session_state.screen_width = 1200

is_mobile = st.session_state.get('screen_width', 1200) < 768

# ------------------ 辅助函数 ------------------
def get_popup_html(row):
    return f"""
    <div style="font-size:12px; min-width:220px;">
        <b>{row['name']}</b><br>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:5px;">
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">类型: {row['type']}</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">利用率: {row['utilization']:.1%}</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">价格: {row['price']}元/度</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">空闲: {row['available_slots']}</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">功率: {row['power']}kW</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">距离: {row['distance_km']:.1f}km</span>
        </div>
    </div>
    """

def generate_mock_chargers(lat, lon, radius_km=5, count=15, refresh_seed=False):
    name_templates = ["星星充电站", "特来电超充站", "国家电网快充站", "小桔充电", "云快充", "万马爱充", "蔚来换电站", "小鹏超充站"]
    types = ["快充", "慢充"]
    if refresh_seed:
        random.seed()
    else:
        random.seed(int(lat * 1000 + lon * 1000) % 2 ** 32)

    chargers = []
    for i in range(count):
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, radius_km) / 111.0
        dlat = r * math.cos(angle)
        dlon = r * math.sin(angle) / math.cos(math.radians(lat))
        new_lat = lat + dlat
        new_lon = lon + dlon
        charger_type = random.choice(types)
        utilization = random.uniform(0.1, 0.9)
        price = 1.2 if charger_type == "快充" else 0.8
        available = random.randint(1, 8)
        power = 60 if charger_type == "快充" else 7
        chargers.append({
            "name": f"{random.choice(name_templates)}{i+1}",
            "lat": new_lat, "lon": new_lon, "type": charger_type,
            "utilization": utilization, "price": price,
            "available_slots": available, "power": power, "distance": None
        })
    return pd.DataFrame(chargers)

processor = DataProcessor()
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
processor.db_path = os.path.join(base_dir, "data", "charger_data.db")

# ------------------ 从 Supabase 加载用户数据 ------------------
def load_user_data_from_db(username):
    if not username:
        return
    history_df = get_charging_history(username)
    if not history_df.empty:
        st.session_state.user_history = history_df.rename(columns={"date": "日期", "station_name": "充电站", "cost": "费用"})
    else:
        st.session_state.user_history = pd.DataFrame(columns=["日期", "充电站", "费用"])
    apps_df = get_appointments(username, status='有效')
    if not apps_df.empty:
        st.session_state.user_appointments[username] = apps_df.to_dict('records')
    else:
        st.session_state.user_appointments[username] = []
    feedbacks_df = get_feedbacks(limit=20)
    if not feedbacks_df.empty:
        st.session_state.feedback_list = feedbacks_df.to_dict('records')
    else:
        st.session_state.feedback_list = []

# ------------------ session_state 初始化 ------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_history' not in st.session_state:
    st.session_state.user_history = pd.DataFrame(columns=["日期", "充电站", "费用"])
if 'feedback_list' not in st.session_state:
    st.session_state.feedback_list = []
if 'user_appointments' not in st.session_state:
    st.session_state.user_appointments = {}

def login(username):
    st.session_state.logged_in = True
    st.session_state.username = username
    load_user_data_from_db(username)

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None

# ------------------ 主界面 ------------------
st.title("🔋 智能充电导航")
st.markdown("根据您的当前位置，智能推荐利用率低、距离近的充电桩，助您快速充电，避开高峰。")

# ------------------ 侧边栏（响应式） ------------------
with st.sidebar:
    st.header("👤 用户")
    if st.session_state.logged_in:
        st.success(f"欢迎，{st.session_state.username}！")
        if st.button("🚪 退出登录", use_container_width=True):
            logout()
            st.rerun()
    else:
        st.info("未登录，部分功能受限（个人中心、预约需登录）")
        with st.expander("🔐 登录 / 注册", expanded=False):
            tab_login, tab_reg = st.tabs(["登录", "注册"])
            with tab_login:
                with st.form("quick_login"):
                    login_user = st.text_input("用户名", key="quick_login_user")
                    login_pwd = st.text_input("密码", type="password", key="quick_login_pwd")
                    if st.form_submit_button("登录"):
                        if not login_user or not login_pwd:
                            st.error("请输入用户名和密码")
                        else:
                            success, msg = check_login(login_user, login_pwd)
                            if success:
                                login(login_user)
                                st.rerun()
                            else:
                                st.error(msg)
            with tab_reg:
                with st.form("quick_reg"):
                    reg_user = st.text_input("新用户名", key="quick_reg_user")
                    reg_pwd = st.text_input("新密码", type="password", key="quick_reg_pwd")
                    reg_pwd_confirm = st.text_input("确认密码", type="password", key="quick_reg_confirm")
                    if st.form_submit_button("注册"):
                        if not reg_user or not reg_pwd:
                            st.error("用户名和密码不能为空")
                        elif reg_pwd != reg_pwd_confirm:
                            st.error("两次输入的密码不一致")
                        else:
                            success, msg = register_user(reg_user, reg_pwd)
                            if success:
                                st.success(msg + "，请登录")
                            else:
                                st.error(msg)
        st.markdown("---")

    st.header("📍 我的位置")
    loc_mode = st.radio("定位方式", ["自动定位", "手动输入"], index=0)
    user_lat, user_lon = None, None
    if loc_mode == "自动定位":
        try:
            from streamlit_js_eval import get_geolocation
            if st.button("📡 获取当前位置", use_container_width=True):
                with st.spinner("正在获取位置..."):
                    loc = get_geolocation()
                    if loc and 'coords' in loc:
                        user_lat = loc['coords']['latitude']
                        user_lon = loc['coords']['longitude']
                        st.success(f"定位成功：纬度 {user_lat:.4f}, 经度 {user_lon:.4f}")
                    else:
                        st.error("定位失败，请检查浏览器权限或切换手动输入")
        except ImportError:
            st.warning("自动定位库未安装，将使用模拟位置。如需自动定位，请运行：pip install streamlit-js-eval")
            user_lat, user_lon = 39.9, 116.4
            st.info(f"使用默认模拟位置：国贸CBD (39.9, 116.4)")
    else:
        # 手动输入模式
        col1, col2 = st.columns(2)
        with col1:
            user_lat = st.number_input("纬度", value=39.9042, format="%.4f", key="manual_lat")
        with col2:
            user_lon = st.number_input("经度", value=116.4074, format="%.4f", key="manual_lon")

        # 当前省份显示 + 更换省份按钮（将城市改为省份）
        if 'current_province' not in st.session_state:
            st.session_state.current_province = "北京市"
        if 'show_province_picker' not in st.session_state:
            st.session_state.show_province_picker = False

        prov_col1, prov_col2 = st.columns([3, 1])
        with prov_col1:
            st.info(f"📍 当前省份：{st.session_state.current_province}")
        with prov_col2:
            if st.button("🗺️ 更换省份", use_container_width=True):
                st.session_state.show_province_picker = not st.session_state.show_province_picker

        # 省份选择器（模拟独立页面）
        if st.session_state.show_province_picker:
            with st.container():
                st.markdown("---")
                st.markdown("## 🗺️ 选择省份")
                st.caption("点击省份自动切换定位（省会/代表性城市坐标）")

                # 省份数据库（名称: (纬度, 经度)）
                province_db = {
                    "北京市": (39.9042, 116.4074),
                    "上海市": (31.2304, 121.4737),
                    "天津市": (39.0841, 117.2009),
                    "重庆市": (29.4316, 106.9123),
                    "黑龙江省": (45.8038, 126.5343),
                    "吉林省": (43.8171, 125.3235),
                    "辽宁省": (41.8057, 123.4315),
                    "内蒙古自治区": (40.8175, 111.6708),
                    "河北省": (38.0428, 114.5149),
                    "山西省": (37.8735, 112.5624),
                    "陕西省": (34.3416, 108.9402),
                    "甘肃省": (36.0611, 103.8343),
                    "宁夏回族自治区": (38.4712, 106.2590),
                    "青海省": (36.6232, 101.7806),
                    "新疆维吾尔自治区": (43.8256, 87.6168),
                    "西藏自治区": (29.6469, 91.1409),
                    "四川省": (30.5728, 104.0668),
                    "云南省": (24.8801, 102.8329),
                    "贵州省": (26.6477, 106.6302),
                    "广西壮族自治区": (22.8167, 108.3669),
                    "海南省": (20.0440, 110.1999),
                    "广东省": (23.1291, 113.2644),
                    "福建省": (26.0789, 119.2965),
                    "江西省": (28.6765, 115.8925),
                    "湖南省": (28.2282, 112.9388),
                    "湖北省": (30.5928, 114.3055),
                    "河南省": (34.7466, 113.6253),
                    "山东省": (36.0671, 120.3826),
                    "江苏省": (32.0603, 118.7969),
                    "浙江省": (30.2741, 120.1551),
                    "安徽省": (31.8612, 117.2850),
                    "香港特别行政区": (22.3193, 114.1694),
                    "澳门特别行政区": (22.1987, 113.5439),
                    "台湾省": (25.0330, 121.5654),
                }

                # 搜索框
                search_term = st.text_input("🔍 搜索省份", placeholder="输入省份中文名", key="province_search")
                if search_term:
                    filtered = {name: coord for name, coord in province_db.items() if search_term in name}
                    if filtered:
                        st.markdown("**搜索结果**")
                        cols = st.columns(3)
                        for idx, (prov, (lat, lon)) in enumerate(filtered.items()):
                            with cols[idx % 3]:
                                if st.button(prov, key=f"search_{prov}"):
                                    st.session_state.manual_lat = lat
                                    st.session_state.manual_lon = lon
                                    st.session_state.current_province = prov
                                    st.session_state.show_province_picker = False
                                    st.rerun()
                    else:
                        st.warning("未找到该省份")

                # 热门省份（常用）
                st.markdown("**🔥 热门省份**")
                hot_provinces = ["北京市", "上海市", "广东省", "江苏省", "浙江省", "四川省", "湖北省", "陕西省", "重庆市", "山东省"]
                hot_cols = st.columns(4)
                for idx, prov in enumerate(hot_provinces):
                    with hot_cols[idx % 4]:
                        if st.button(prov, key=f"hot_{prov}"):
                            lat, lon = province_db[prov]
                            st.session_state.manual_lat = lat
                            st.session_state.manual_lon = lon
                            st.session_state.current_province = prov
                            st.session_state.show_province_picker = False
                            st.rerun()

                # 按拼音首字母分组（需要 pypinyin）
                st.markdown("**📚 所有省份**")
                try:
                    import pypinyin
                    def get_first_letter(text):
                        first_char = text[0]
                        try:
                            return pypinyin.pinyin(first_char, style=pypinyin.NORMAL)[0][0][0].upper()
                        except:
                            return "#"
                    grouped = {}
                    for prov in sorted(province_db.keys()):
                        letter = get_first_letter(prov)
                        if letter.isalpha():
                            grouped.setdefault(letter, []).append(prov)
                        else:
                            grouped.setdefault("#", []).append(prov)
                    letters = sorted(grouped.keys())
                    selected_letter = st.selectbox("快速跳转", ["请选择"] + letters, key="letter_jump")
                    if selected_letter != "请选择":
                        st.markdown(f"**{selected_letter}**")
                        prov_list = grouped[selected_letter]
                        prov_cols = st.columns(3)
                        for idx, prov in enumerate(prov_list):
                            with prov_cols[idx % 3]:
                                if st.button(prov, key=f"group_{prov}"):
                                    lat, lon = province_db[prov]
                                    st.session_state.manual_lat = lat
                                    st.session_state.manual_lon = lon
                                    st.session_state.current_province = prov
                                    st.session_state.show_province_picker = False
                                    st.rerun()
                    else:
                        for letter in letters:
                            with st.expander(f"{letter}"):
                                prov_cols = st.columns(3)
                                for idx, prov in enumerate(grouped[letter]):
                                    with prov_cols[idx % 3]:
                                        if st.button(prov, key=f"letter_{letter}_{prov}"):
                                            lat, lon = province_db[prov]
                                            st.session_state.manual_lat = lat
                                            st.session_state.manual_lon = lon
                                            st.session_state.current_province = prov
                                            st.session_state.show_province_picker = False
                                            st.rerun()
                except ImportError:
                    st.warning("未安装 pypinyin，请运行 pip install pypinyin 以获得字母分组功能。暂时显示简单列表。")
                    for prov in sorted(province_db.keys()):
                        if st.button(prov, key=f"simple_{prov}"):
                            lat, lon = province_db[prov]
                            st.session_state.manual_lat = lat
                            st.session_state.manual_lon = lon
                            st.session_state.current_province = prov
                            st.session_state.show_province_picker = False
                            st.rerun()

                # 关闭按钮
                if st.button("✖ 关闭省份列表", use_container_width=True):
                    st.session_state.show_province_picker = False
                    st.rerun()
                st.markdown("---")

    if user_lat is None or user_lon is None:
        user_lat, user_lon = 39.9, 116.4
        st.info("使用默认模拟位置：国贸CBD (39.9, 116.4)")

    st.markdown("---")
    radius = st.slider("搜索半径（公里）", 1, 20, 5)
    filter_type = st.selectbox("充电类型", ["全部", "快充", "慢充"])
    st.markdown("---")
    if st.button("🔄 刷新空闲桩数据", use_container_width=True):
        st.session_state.refresh_trigger = not st.session_state.get('refresh_trigger', False)
        st.rerun()

# ------------------ 获取充电桩数据（使用 session_state 缓存） ------------------
if 'cached_charger_params' not in st.session_state:
    st.session_state.cached_charger_params = None
if 'cached_charger_data' not in st.session_state:
    st.session_state.cached_charger_data = pd.DataFrame()
if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = False

current_params = (user_lat, user_lon, radius, st.session_state.refresh_trigger)
need_refresh = (
    st.session_state.cached_charger_params != current_params or
    st.session_state.cached_charger_data.empty or
    st.session_state.refresh_trigger
)

if need_refresh:
    with st.spinner("正在搜索周边充电桩..."):
        nearby = processor.get_nearby_chargers(user_lat, user_lon, radius)
        if nearby.empty:
            mock_count = max(10, int(radius * 2))
            nearby = generate_mock_chargers(
                user_lat, user_lon, radius, mock_count,
                refresh_seed=st.session_state.refresh_trigger
            )
        st.session_state.cached_charger_data = nearby
        st.session_state.cached_charger_params = current_params
        if st.session_state.refresh_trigger:
            st.session_state.refresh_trigger = False
else:
    nearby = st.session_state.cached_charger_data

if filter_type != "全部" and not nearby.empty:
    nearby = nearby[nearby['type'] == filter_type]

if not nearby.empty:
    nearby['distance'] = ((nearby['lat'] - user_lat) ** 2 + (nearby['lon'] - user_lon) ** 2) ** 0.5 * 111
    nearby['distance_km'] = nearby['distance'].round(2)
    nearby['score'] = (1 - nearby['utilization']) * 0.7 + (1 / (nearby['distance_km'] + 0.1)) * 0.3
    nearby_sorted = nearby.sort_values('score', ascending=False).head(20)
else:
    nearby_sorted = pd.DataFrame()

# ------------------ 标签页 ------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ 充电导航", "📅 预约充电", "💰 价格预测", "👤 个人中心", "📢 用户反馈"])

with tab1:
    if not nearby_sorted.empty:
        # 地图
        st.subheader("🗺️ 周边充电桩地图（高德底图）")
        tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        m = folium.Map(location=[user_lat, user_lon], zoom_start=12, tiles=tiles, attr='高德地图')
        folium.Marker([user_lat, user_lon], popup=folium.Popup("<b>我的位置</b>", max_width=200), icon=folium.Icon(color='blue', icon='user', prefix='fa')).add_to(m)
        for _, row in nearby_sorted.iterrows():
            color = 'red' if row['utilization'] > 0.7 else ('green' if row['utilization'] < 0.3 else 'orange')
            folium.Marker([row['lat'], row['lon']], popup=folium.Popup(get_popup_html(row), max_width=300), icon=folium.Icon(color=color, icon='bolt', prefix='fa')).add_to(m)
        map_height = 400 if not is_mobile else 300
        st_folium(m, width=None, height=map_height, returned_objects=[])

        with st.expander("📋 推荐列表（按推荐指数排序）", expanded=True):
            cols_per_row = 3
            rows = [nearby_sorted.iloc[i:i + cols_per_row] for i in range(0, len(nearby_sorted), cols_per_row)]
            for row_group in rows:
                cols = st.columns(cols_per_row)
                for col, (_, row) in zip(cols, row_group.iterrows()):
                    with col:
                        bar_color = "#EF4444" if row['utilization'] > 0.7 else ("#10B981" if row['utilization'] < 0.3 else "#F59E0B")
                        st.markdown(f"""
                        <div class="charger-card">
                            <div class="card-title">
                                <span>{row['name']}</span>
                                <span class="card-type">{row['type']}</span>
                            </div>
                            <div class="card-stats">
                                <span>📊 {row['utilization']:.0%}</span>
                                <span>💰 {row['price']}元/度</span>
                                <span>🔌 空闲{row['available_slots']}</span>
                                <span>📏 {row['distance_km']:.1f}km</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {row['utilization'] * 100}%; background-color: {bar_color};"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        # 一键导航
        st.subheader("🚀 一键导航")
        selected_name = st.selectbox("选择充电站", nearby_sorted['name'].tolist(), key="nav_select")
        selected_row = nearby_sorted[nearby_sorted['name'] == selected_name].iloc[0]
        lat, lon = selected_row['lat'], selected_row['lon']
        amap_nav_url = f"https://uri.amap.com/navigation?to={lon},{lat},{selected_name}&mode=car&policy=1"
        st.markdown(f'<a href="{amap_nav_url}" target="_blank" style="display: inline-block; background-color: #4285F4; color: white; padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none;">🚗 使用高德地图APP导航</a>', unsafe_allow_html=True)
        baidu_nav_url = f"https://map.baidu.com/?newmap=1&ie=utf-8&s=s%26wd%3D{selected_name}%26c%3D131&from=alamap"
        st.markdown(f'<a href="{baidu_nav_url}" target="_blank" style="display: inline-block; background-color: #4CAF50; color: white; padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; margin-top: 5px;">🗺️ 使用百度地图查看</a>', unsafe_allow_html=True)

        # 排队和费用估算
        if is_mobile:
            with st.expander("⏳ 排队时长预测 & 💰 费用估算", expanded=False):
                st.markdown("#### 排队时长预测")
                queue_station = st.selectbox("选择要预测排队的充电站", nearby_sorted['name'].tolist(), key="queue_select_mobile")
                queue_row = nearby_sorted[nearby_sorted['name'] == queue_station].iloc[0]
                util = queue_row['utilization']
                free_slots = queue_row['available_slots']
                total_slots = free_slots + int(util * 10) or 4
                if free_slots > 0:
                    wait_minutes = 0
                else:
                    queue_vehicles = max(0, int(util * 8) - free_slots)
                    wait_minutes = queue_vehicles * (45 / max(1, total_slots))
                st.info(f"🔮 预测当前排队时间：**{max(0, int(wait_minutes))} 分钟**")

                st.markdown("#### 充电费用估算")
                kwh = st.number_input("预计充电度数 (kWh)", min_value=1.0, max_value=100.0, value=30.0, step=5.0, key="cost_kwh_mobile")
                cost_station = st.selectbox("选择充电站", nearby_sorted['name'].tolist(), key="cost_select_mobile")
                cost_row = nearby_sorted[nearby_sorted['name'] == cost_station].iloc[0]
                st.metric("预估费用", f"¥{kwh * cost_row['price']:.2f}", delta=f"单价 {cost_row['price']} 元/度")
                cheapest = nearby_sorted.loc[nearby_sorted['price'].idxmin()]
                expensive = nearby_sorted.loc[nearby_sorted['price'].idxmax()]
                st.caption(f"💰 当前区域最便宜：{cheapest['name']} ¥{cheapest['price']}/度 → 总价 ¥{kwh * cheapest['price']:.2f}")
                st.caption(f"💸 最贵：{expensive['name']} ¥{expensive['price']}/度 → 总价 ¥{kwh * expensive['price']:.2f}")
        else:
            col_q, col_c = st.columns(2)
            with col_q:
                st.subheader("⏳ 排队时长预测")
                queue_station = st.selectbox("选择要预测排队的充电站", nearby_sorted['name'].tolist(), key="queue_select")
                queue_row = nearby_sorted[nearby_sorted['name'] == queue_station].iloc[0]
                util = queue_row['utilization']
                free_slots = queue_row['available_slots']
                total_slots = free_slots + int(util * 10) or 4
                if free_slots > 0:
                    wait_minutes = 0
                else:
                    queue_vehicles = max(0, int(util * 8) - free_slots)
                    wait_minutes = queue_vehicles * (45 / max(1, total_slots))
                st.info(f"🔮 预测当前排队时间：**{max(0, int(wait_minutes))} 分钟**")
            with col_c:
                st.subheader("💰 充电费用估算")
                kwh = st.number_input("预计充电度数 (kWh)", min_value=1.0, max_value=100.0, value=30.0, step=5.0, key="cost_kwh")
                cost_station = st.selectbox("选择充电站", nearby_sorted['name'].tolist(), key="cost_select")
                cost_row = nearby_sorted[nearby_sorted['name'] == cost_station].iloc[0]
                st.metric("预估费用", f"¥{kwh * cost_row['price']:.2f}", delta=f"单价 {cost_row['price']} 元/度")
                cheapest = nearby_sorted.loc[nearby_sorted['price'].idxmin()]
                expensive = nearby_sorted.loc[nearby_sorted['price'].idxmax()]
                st.caption(f"💰 当前区域最便宜：{cheapest['name']} ¥{cheapest['price']}/度 → 总价 ¥{kwh * cheapest['price']:.2f}")
                st.caption(f"💸 最贵：{expensive['name']} ¥{expensive['price']}/度 → 总价 ¥{kwh * expensive['price']:.2f}")
    else:
        st.warning("⚠️ 当前范围内没有充电桩，请扩大搜索半径或移动位置。")
        tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        m = folium.Map(location=[user_lat, user_lon], zoom_start=12, tiles=tiles, attr='高德地图')
        folium.Marker([user_lat, user_lon], popup="我的位置", icon=folium.Icon(color='blue')).add_to(m)
        st_folium(m, width=None, height=400, returned_objects=[])

with tab2:
    st.subheader("📅 预约充电")
    current_user = st.session_state.username if st.session_state.logged_in else None
    if not nearby_sorted.empty:
        st.markdown("### 新建预约")
        if st.session_state.logged_in:
            with st.form("appointment_form"):
                station = st.selectbox("选择充电站", nearby_sorted['name'].tolist())
                app_date = st.date_input("预约日期", min_value=datetime.today().date())
                app_time = st.time_input("预约时间")
                if st.form_submit_button("提交预约"):
                    date_str = app_date.strftime("%Y-%m-%d")
                    time_str = app_time.strftime("%H:%M")
                    success, msg = insert_appointment(current_user, station, date_str, time_str)
                    if success:
                        load_user_data_from_db(current_user)
                        st.success(f"已预约 {station} 于 {date_str} {time_str}，请按时到达。")
                        st.rerun()
                    else:
                        st.error(f"预约失败：{msg}")
        else:
            st.warning("请先登录后再预约充电")
    else:
        st.info("当前无充电桩可预约")

    st.markdown("### 📋 我的预约")
    if not st.session_state.logged_in:
        st.info("登录后可查看和管理您的预约记录")
    else:
        user_apps = st.session_state.user_appointments.get(current_user, [])
        if not user_apps:
            st.info("暂无预约记录，请新建预约")
        else:
            apps_df = pd.DataFrame(user_apps)
            display_df = apps_df[['station_name', 'date', 'time', 'status']].copy()
            display_df.columns = ['充电站', '日期', '时间', '状态']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.markdown("#### 取消预约")
            cancel_options = [f"{app['station_name']} - {app['date']} {app['time']}" for app in user_apps]
            if cancel_options:
                selected_idx = st.selectbox("选择要取消的预约", range(len(cancel_options)), format_func=lambda i: cancel_options[i])
                if st.button("❌ 取消所选预约", use_container_width=True):
                    if cancel_appointment(user_apps[selected_idx]['id']):
                        load_user_data_from_db(current_user)
                        st.success("已取消预约")
                        st.rerun()
                    else:
                        st.error("取消失败")

with tab3:
    st.subheader("💰 未来价格趋势预测")
    dates = [(datetime.today() + timedelta(days=i)).strftime('%m-%d') for i in range(7)]
    x = np.linspace(0, 2 * np.pi, 7)
    prices = np.clip(1.3 + 0.4 * np.sin(x) + np.random.uniform(-0.1, 0.1, 7), 0.8, 2.0).round(2)
    price_df = pd.DataFrame({"日期": dates, "价格 (元/度)": prices})
    st.dataframe(price_df, use_container_width=True, hide_index=True)
    import plotly.express as px
    fig_price = px.line(x=dates, y=prices, title="未来7天价格趋势预测", markers=True)
    fig_price.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="black")
    st.plotly_chart(fig_price, use_container_width=True)
    st.info(f"📈 预测最高价：{max(prices)} 元/度，最低价：{min(prices)} 元/度，建议在低价日充电。")

with tab4:
    st.subheader("👤 个人中心")
    if st.session_state.logged_in:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("用户名", st.session_state.username)
        with col2:
            history_count = len(st.session_state.user_history)
            st.metric("累计充电次数", history_count)
        with col3:
            st.metric("节省碳排放", f"约 {history_count * 3} kg")
        with st.expander("📜 历史充电记录", expanded=True):
            if st.session_state.user_history.empty:
                st.info("暂无充电记录，完成一次充电后会自动记录")
                if st.button("➕ 模拟完成一次充电（测试用）"):
                    if not nearby_sorted.empty:
                        test_station = nearby_sorted.iloc[0]['name']
                        test_cost = round(np.random.uniform(20, 80), 2)
                        today_str = datetime.today().strftime("%Y-%m-%d")
                        new_row = pd.DataFrame({
                            "日期": [today_str],
                            "充电站": [test_station],
                            "费用": [test_cost]
                        })
                        st.session_state.user_history = pd.concat(
                            [st.session_state.user_history, new_row], ignore_index=True
                        )
                        st.success(f"模拟充电成功！在 {test_station} 消费 {test_cost} 元")
                        try:
                            insert_charging_history(
                                st.session_state.username,
                                test_station,
                                today_str,
                                test_cost
                            )
                        except Exception as e:
                            print(f"数据库写入失败（模拟充电不保存）: {e}")
                        st.rerun()
                    else:
                        st.error("当前无充电桩数据，无法模拟")
            else:
                st.dataframe(st.session_state.user_history, use_container_width=True, hide_index=True)
    else:
        st.info("登录后可查看个人充电记录、碳减排等专属信息")
        with st.container():
            st.markdown('<div style="background-color: #F3F4F6; border-radius: 16px; padding: 20px; margin: 20px 0; text-align: center;">', unsafe_allow_html=True)
            st.subheader("🔐 登录个人中心")
            with st.form("login_for_personal"):
                login_user = st.text_input("用户名", key="personal_login_user")
                login_pwd = st.text_input("密码", type="password", key="personal_login_pwd")
                if st.form_submit_button("登录"):
                    success, msg = check_login(login_user, login_pwd)
                    if success:
                        login(login_user)
                        st.rerun()
                    else:
                        st.error(msg)
            st.markdown("还没有账号？请使用侧边栏的「注册」功能。")
            st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.subheader("📢 用户反馈（助力充电网络优化）")
    with st.form("feedback_form"):
        feedback_type = st.selectbox("反馈类型", ["建议新增充电站", "现有站点问题", "价格异常", "其他"])
        location = st.text_input("位置描述（如：朝阳区国贸附近）")
        message = st.text_area("详细说明", height=100)
        if st.form_submit_button("提交反馈"):
            username = st.session_state.username if st.session_state.logged_in else "匿名"
            success, msg = insert_feedback(username, feedback_type, location, message)
            if success:
                load_user_data_from_db(st.session_state.username if st.session_state.logged_in else "")
                st.success("感谢您的反馈！我们会纳入规划考虑。")
                st.rerun()
            else:
                st.error(f"提交失败：{msg}")
    if st.session_state.feedback_list:
        st.markdown("### 📋 历史反馈记录")
        feedback_df = pd.DataFrame(st.session_state.feedback_list)
        if not feedback_df.empty:
            display_df = feedback_df[['type', 'location', 'message', 'created_at']].copy()
            display_df.columns = ['类型', '位置', '内容', '提交时间']
            if 'created_at' in display_df.columns:
                display_df['提交时间'] = pd.to_datetime(display_df['提交时间']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无反馈，欢迎提出宝贵意见。")
    else:
        st.info("暂无反馈，欢迎提出宝贵意见。")

st.markdown("---")
st.caption("数据说明：充电桩基础数据来源于高德地图API，利用率及空闲插口为基于真实分布的模拟值，仅供参考。地图底图使用高德地图瓦片服务。")