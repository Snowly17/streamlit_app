# user_app/app_user.py
import sys
import os

# 将项目根目录添加到 sys.path
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
import sqlite3

# ------------------ 独立用户数据库操作（不依赖DataProcessor）------------------
USER_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_data.db")

def init_user_db():
    """初始化用户数据库表"""
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    # 充电历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS charging_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            station_name TEXT,
            date TEXT,
            cost REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 预约记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            station_name TEXT,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT '有效',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 用户反馈表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            type TEXT,
            location TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 用户表（新增）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password):
    """注册新用户，返回 (success, message)"""
    if not username or not password:
        return False, "用户名和密码不能为空"
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "用户名已存在"
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True, "注册成功"
    except Exception as e:
        print(f"注册失败: {e}")
        return False, "注册失败，请稍后重试"

def check_login(username, password):
    """验证登录，返回 (success, message)"""
    if not username or not password:
        return False, "用户名和密码不能为空"
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] == password:
            return True, "登录成功"
        else:
            return False, "用户名或密码错误"
    except Exception as e:
        print(f"登录验证失败: {e}")
        return False, "系统错误，请稍后重试"

def insert_charging_history(username, station_name, date, cost):
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO charging_history (username, station_name, date, cost) VALUES (?, ?, ?, ?)",
            (username, station_name, date, cost)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"插入充电历史失败: {e}")
        return False

def get_charging_history(username):
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        query = "SELECT date, station_name, cost FROM charging_history WHERE username = ? ORDER BY date DESC"
        df = pd.read_sql_query(query, conn, params=(username,))
        conn.close()
        return df
    except Exception as e:
        print(f"读取充电历史失败: {e}")
        return pd.DataFrame()

def insert_appointment(username, station_name, date, time):
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO appointments (username, station_name, date, time) VALUES (?, ?, ?, ?)",
            (username, station_name, date, time)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"插入预约失败: {e}")
        return False

def get_appointments(username, status='有效'):
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        query = "SELECT id, station_name, date, time, status FROM appointments WHERE username = ? AND status = ? ORDER BY date, time"
        df = pd.read_sql_query(query, conn, params=(username, status))
        conn.close()
        return df
    except Exception as e:
        print(f"读取预约失败: {e}")
        return pd.DataFrame()

def cancel_appointment(appointment_id):
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE appointments SET status = '已取消' WHERE id = ?", (appointment_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"取消预约失败: {e}")
        return False

def insert_feedback(username, fb_type, location, message):
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedbacks (username, type, location, message) VALUES (?, ?, ?, ?)",
            (username, fb_type, location, message)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"插入反馈失败: {e}")
        return False

def get_feedbacks(limit=20):
    try:
        conn = sqlite3.connect(USER_DB_PATH)
        query = "SELECT username, type, location, message, created_at FROM feedbacks ORDER BY created_at DESC LIMIT ?"
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    except Exception as e:
        print(f"读取反馈失败: {e}")
        return pd.DataFrame()

# 初始化数据库表
init_user_db()

# ------------------ 页面配置 ------------------
st.set_page_config(
    page_title="智能充电导航",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_popup_html(row):
    """返回横向卡片样式的 HTML 弹窗内容"""
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
    """根据中心点生成模拟充电桩数据"""
    name_templates = ["星星充电站", "特来电超充站", "国家电网快充站", "小桔充电", "云快充", "万马爱充", "蔚来换电站",
                      "小鹏超充站"]
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
            "name": f"{random.choice(name_templates)}{i + 1}",
            "lat": new_lat,
            "lon": new_lon,
            "type": charger_type,
            "utilization": utilization,
            "price": price,
            "available_slots": available,
            "power": power,
            "distance": None
        })
    return pd.DataFrame(chargers)


# ------------------ 响应式布局样式 ------------------
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 280px;
        width: 300px;
    }
    @media (max-width: 768px) {
        .stDataFrame, .stPlotlyChart {
            border-radius: 16px;
            margin: 8px 0;
        }
        .stButton button {
            min-height: 48px;
        }
    }
    .feedback-card {
        background-color: #F9FAFB;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 4px solid #10B981;
    }
    .login-card {
        background-color: #F3F4F6;
        border-radius: 16px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }
</style>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
""", unsafe_allow_html=True)

# ------------------ 初始化数据处理器（只用于充电桩数据）------------------
processor = DataProcessor()
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
processor.db_path = os.path.join(base_dir, "data", "charger_data.db")

# ------------------ 辅助函数：从数据库加载用户数据到 session_state ------------------
def load_user_data_from_db(username):
    """从数据库加载该用户的历史数据，存入 session_state"""
    if not username:
        return
    # 充电历史
    history_df = get_charging_history(username)
    if not history_df.empty:
        st.session_state.user_history = history_df.rename(columns={"date": "日期", "station_name": "充电站", "cost": "费用"})
    else:
        st.session_state.user_history = pd.DataFrame(columns=["日期", "充电站", "费用"])
    # 预约列表（有效）
    apps_df = get_appointments(username, status='有效')
    if not apps_df.empty:
        st.session_state.user_appointments[username] = apps_df.to_dict('records')
    else:
        st.session_state.user_appointments[username] = []
    # 反馈列表（全局，不按用户）
    feedbacks_df = get_feedbacks(limit=20)
    if not feedbacks_df.empty:
        st.session_state.feedback_list = feedbacks_df.to_dict('records')
    else:
        st.session_state.feedback_list = []

# ------------------ 初始化 session_state ------------------
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
    # 不清空数据，下次登录重新加载

# ------------------ 主界面 ------------------
st.title("🔋 智能充电导航")
st.markdown("根据您的当前位置，智能推荐利用率低、距离近的充电桩，助您快速充电，避开高峰。")

# ------------------ 侧边栏：定位与筛选 + 登录状态 ------------------
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
    loc_mode = st.radio(
        "定位方式",
        ["自动定位", "手动输入"],
        index=0,
        help="自动定位需要浏览器授权，如失败请切换手动输入"
    )

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
        # 手动输入模式（保留基础手动输入，如需省份选择可自行补充）
        col1, col2 = st.columns(2)
        with col1:
            user_lat = st.number_input("纬度", value=39.9042, format="%.4f")
        with col2:
            user_lon = st.number_input("经度", value=116.4074, format="%.4f")
        st.info("手动输入模式，可直接修改经纬度")

    if user_lat is None or user_lon is None:
        user_lat, user_lon = 39.9, 116.4
        st.info("使用默认模拟位置：国贸CBD (39.9, 116.4)")

    st.markdown("---")
    radius = st.slider("搜索半径（公里）", 1, 20, 5, help="扩大半径可发现更多充电桩")
    filter_type = st.selectbox("充电类型", ["全部", "快充", "慢充"], help="筛选快充/慢充桩")

    st.markdown("---")
    if st.button("🔄 刷新空闲桩数据", use_container_width=True):
        st.session_state.refresh_trigger = not st.session_state.get('refresh_trigger', False)
        st.rerun()

# ------------------ 获取周边充电桩 ------------------
with st.spinner("正在搜索周边充电桩..."):
    nearby = processor.get_nearby_chargers(user_lat, user_lon, radius)
    refresh_flag = st.session_state.get('refresh_trigger', False)
    if nearby.empty or refresh_flag:
        mock_count = max(10, int(radius * 2))
        nearby = generate_mock_chargers(user_lat, user_lon, radius, mock_count, refresh_seed=refresh_flag)
        if refresh_flag:
            st.session_state.refresh_trigger = False

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

# ==================== tab1: 充电导航 ====================
with tab1:
    if not nearby_sorted.empty:
        st.subheader("🗺️ 周边充电桩地图（高德底图）")
        tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        attr = '高德地图'
        m = folium.Map(location=[user_lat, user_lon], zoom_start=12, tiles=tiles, attr=attr)
        folium.Marker([user_lat, user_lon], popup=folium.Popup("<b>我的位置</b>", max_width=200), icon=folium.Icon(color='blue', icon='user', prefix='fa')).add_to(m)
        for _, row in nearby_sorted.iterrows():
            if row['utilization'] > 0.7:
                color = 'red'
            elif row['utilization'] < 0.3:
                color = 'green'
            else:
                color = 'orange'
            popup_html = get_popup_html(row)
            folium.Marker([row['lat'], row['lon']], popup=folium.Popup(popup_html, max_width=300), icon=folium.Icon(color=color, icon='bolt', prefix='fa')).add_to(m)
        st_folium(m, width=None, height=500, returned_objects=[])

        with st.expander("📋 推荐列表（按推荐指数排序）", expanded=True):
            def make_card(row):
                if row['utilization'] > 0.7:
                    bar_color = "#EF4444"
                elif row['utilization'] < 0.3:
                    bar_color = "#10B981"
                else:
                    bar_color = "#F59E0B"
                return f"""
                <div style="background-color: #FFFFFF; border-radius: 16px; padding: 12px 16px; margin-bottom: 12px; border: 1px solid #E5E7EB;">
                    <div style="display: flex; justify-content: space-between;">
                        <div style="font-weight: 700;">{row['name']}</div>
                        <div style="background-color: #E3F2FD; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem;">{row['type']}</div>
                    </div>
                    <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 0.85rem;">
                        <div>📊 利用率: {row['utilization']:.1%}</div>
                        <div>💰 {row['price']} 元/度</div>
                        <div>🔌 空闲: {row['available_slots']}</div>
                        <div>📏 距离: {row['distance_km']:.1f} km</div>
                    </div>
                    <div style="margin-top: 8px;"><div style="background-color: #E5E7EB; border-radius: 20px; height: 6px;"><div style="background-color: {bar_color}; width: {row['utilization']*100}%; height: 6px; border-radius: 20px;"></div></div></div>
                </div>
                """
            cards_per_row = 3
            rows = [nearby_sorted.iloc[i:i+cards_per_row] for i in range(0, len(nearby_sorted), cards_per_row)]
            for row_group in rows:
                cols = st.columns(cards_per_row)
                for col, (_, row) in zip(cols, row_group.iterrows()):
                    with col:
                        st.markdown(make_card(row), unsafe_allow_html=True)

        st.subheader("🚀 一键导航")
        selected_name = st.selectbox("选择充电站", nearby_sorted['name'].tolist(), key="nav_select")
        selected_row = nearby_sorted[nearby_sorted['name'] == selected_name].iloc[0]
        lat, lon = selected_row['lat'], selected_row['lon']
        amap_nav_url = f"https://uri.amap.com/navigation?to={lon},{lat},{selected_name}&mode=car&policy=1"
        st.markdown(f'<a href="{amap_nav_url}" target="_blank" style="display: inline-block; background-color: #4285F4; color: white; padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none;">🚗 使用高德地图APP导航</a>', unsafe_allow_html=True)
        baidu_nav_url = f"https://map.baidu.com/?newmap=1&ie=utf-8&s=s%26wd%3D{selected_name}%26c%3D131&from=alamap"
        st.markdown(f'<a href="{baidu_nav_url}" target="_blank" style="display: inline-block; background-color: #4CAF50; color: white; padding: 0.5rem 1rem; border-radius: 8px; text-decoration: none; margin-top: 5px;">🗺️ 使用百度地图查看</a>', unsafe_allow_html=True)

        # 排队时长预测
        st.subheader("⏳ 排队时长预测")
        queue_station = st.selectbox("选择要预测排队的充电站", nearby_sorted['name'].tolist(), key="queue_select")
        queue_row = nearby_sorted[nearby_sorted['name'] == queue_station].iloc[0]
        util = queue_row['utilization']
        free_slots = queue_row['available_slots']
        total_slots = free_slots + int(util * 10)
        if total_slots <= 0:
            total_slots = 4
        busy_slots = total_slots - free_slots
        if busy_slots <= 0:
            wait_minutes = 0
        else:
            avg_charge_min = 45
            queue_vehicles = max(0, int(util * 8) - free_slots)
            if free_slots > 0:
                wait_minutes = 0
            else:
                wait_minutes = queue_vehicles * (avg_charge_min / max(1, total_slots))
        wait_minutes = max(0, int(wait_minutes))
        st.info(f"🔮 预测当前排队时间：**{wait_minutes} 分钟**")

        # 充电费用估算
        st.subheader("💰 充电费用估算")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            kwh = st.number_input("预计充电度数 (kWh)", min_value=1.0, max_value=100.0, value=30.0, step=5.0, key="cost_kwh")
        with col_e2:
            cost_station = st.selectbox("选择充电站", nearby_sorted['name'].tolist(), key="cost_select")
            cost_row = nearby_sorted[nearby_sorted['name'] == cost_station].iloc[0]
            price_per_kwh = cost_row['price']
            total_cost = kwh * price_per_kwh
            st.metric("预估费用", f"¥{total_cost:.2f}", delta=f"单价 {price_per_kwh} 元/度")
        cheapest = nearby_sorted.loc[nearby_sorted['price'].idxmin()]
        expensive = nearby_sorted.loc[nearby_sorted['price'].idxmax()]
        st.caption(f"💰 当前区域最便宜：{cheapest['name']} ¥{cheapest['price']}/度 → 总价 ¥{kwh * cheapest['price']:.2f}")
        st.caption(f"💸 最贵：{expensive['name']} ¥{expensive['price']}/度 → 总价 ¥{kwh * expensive['price']:.2f}")
    else:
        st.warning("⚠️ 当前范围内没有充电桩，请扩大搜索半径或移动位置。")
        tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        attr = '高德地图'
        m = folium.Map(location=[user_lat, user_lon], zoom_start=12, tiles=tiles, attr=attr)
        folium.Marker([user_lat, user_lon], popup="我的位置", icon=folium.Icon(color='blue')).add_to(m)
        st_folium(m, width=None, height=400, returned_objects=[])

# ==================== tab2: 预约充电（数据库版） ====================
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
                submit = st.form_submit_button("提交预约")
                if submit:
                    date_str = app_date.strftime("%Y-%m-%d")
                    time_str = app_time.strftime("%H:%M")
                    success = insert_appointment(current_user, station, date_str, time_str)
                    if success:
                        load_user_data_from_db(current_user)
                        st.success(f"已预约 {station} 于 {date_str} {time_str}，请按时到达。")
                        st.rerun()
                    else:
                        st.error("预约失败，请稍后重试")
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
                    app_id = user_apps[selected_idx]['id']
                    if cancel_appointment(app_id):
                        load_user_data_from_db(current_user)
                        st.success("已取消预约")
                        st.rerun()
                    else:
                        st.error("取消失败")

# ==================== tab3: 价格预测 ====================
with tab3:
    st.subheader("💰 未来价格趋势预测")
    dates = [(datetime.today() + timedelta(days=i)).strftime('%m-%d') for i in range(7)]
    x = np.linspace(0, 2 * np.pi, 7)
    base = 1.3
    amplitude = 0.4
    prices = base + amplitude * np.sin(x) + np.random.uniform(-0.1, 0.1, 7)
    prices = np.clip(prices, 0.8, 2.0)
    prices = np.round(prices, 2)
    price_df = pd.DataFrame({"日期": dates, "价格 (元/度)": prices})
    st.dataframe(price_df, use_container_width=True, hide_index=True)
    import plotly.express as px
    fig_price = px.line(x=dates, y=prices, title="未来7天价格趋势预测", markers=True, labels={"x": "日期", "y": "价格 (元/度)"})
    fig_price.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="black")
    st.plotly_chart(fig_price, use_container_width=True)
    st.info(f"📈 预测最高价：{max(prices)} 元/度，最低价：{min(prices)} 元/度，建议在低价日充电。")

# ==================== tab4: 个人中心 ====================
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
                        insert_charging_history(st.session_state.username, test_station, datetime.today().strftime("%Y-%m-%d"), test_cost)
                        load_user_data_from_db(st.session_state.username)
                        st.rerun()
                    else:
                        st.error("当前无充电桩数据，无法模拟")
            else:
                st.dataframe(st.session_state.user_history, use_container_width=True, hide_index=True)
    else:
        st.info("登录后可查看个人充电记录、碳减排等专属信息")
        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("🔐 登录个人中心")
            with st.form("login_for_personal"):
                login_user = st.text_input("用户名", key="personal_login_user")
                login_pwd = st.text_input("密码", type="password", key="personal_login_pwd")
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
            st.markdown("还没有账号？请使用侧边栏的「注册」功能。")
            st.markdown('</div>', unsafe_allow_html=True)

# ==================== tab5: 用户反馈 ====================
with tab5:
    st.subheader("📢 用户反馈（助力充电网络优化）")
    with st.form("feedback_form"):
        feedback_type = st.selectbox("反馈类型", ["建议新增充电站", "现有站点问题", "价格异常", "其他"])
        location = st.text_input("位置描述（如：朝阳区国贸附近）")
        message = st.text_area("详细说明", height=100)
        submitted = st.form_submit_button("提交反馈")
        if submitted:
            username = st.session_state.username if st.session_state.logged_in else "匿名"
            success = insert_feedback(username, feedback_type, location, message)
            if success:
                load_user_data_from_db(st.session_state.username if st.session_state.logged_in else "")
                st.success("感谢您的反馈！我们会纳入规划考虑。")
                st.rerun()
            else:
                st.error("提交失败，请稍后重试")

    if st.session_state.feedback_list:
        st.markdown("### 历史反馈记录")
        for fb in reversed(st.session_state.feedback_list[-5:]):
            st.markdown(f"""
            <div class="feedback-card">
                <strong>{fb['type']}</strong> - {fb['location']}<br>
                {fb['message']}<br>
                <span style="font-size:0.75rem;">{fb['username']} · {fb['created_at']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("暂无反馈，欢迎提出宝贵意见。")

st.markdown("---")
st.caption("数据说明：充电桩基础数据来源于高德地图API，利用率及空闲插口为基于真实分布的模拟值，仅供参考。地图底图使用高德地图瓦片服务。")