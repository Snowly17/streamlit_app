import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import time
import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from common.data_processor import DataProcessor
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

# ================== 深色主题 + UI 全局样式 ==================
st.set_page_config(page_title="政府端 - 充电桩运营监管平台", layout="wide")

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

st.markdown("""
<style>
    /* 全局主背景 #191D27 */
    .stApp {
        background: #191D27;
        color: #eef2ff;
    }
    .main .block-container {
        background: transparent;
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* 卡片：内部颜色改为 #2D3241，边框使用 #272B39 */
    .stMetric, .stDataFrame, .stMarkdown, .stAlert, 
    .stSuccess, .stInfo, .stWarning, .stError, .stException,
    .stButton button, .stSelectbox > div, .stSlider > div {
        background: #2D3241;
        border-radius: 24px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1rem;
        border: 1px solid #272B39;
        box-shadow: none;
        transition: none;
    }

    /* 专门为 Plotly 图表去掉父容器样式 */
    .stPlotlyChart {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin-bottom: 1rem;
        box-shadow: none !important;
    }
    .stMetric:hover, .stDataFrame:hover, .stPlotlyChart:hover {
        border-color: #3A3F51;
        box-shadow: none;
        transform: none;
    }

    /* 侧边栏背景与主背景一致 */
    .css-1d391kg, .stSidebar {
        background: #191D27;
        border-right: 1px solid #272B39;
        backdrop-filter: none;
    }

    /* 侧边栏所有文字强制白色 */
    .stSidebar, .stSidebar *,
    .stSidebar .stMarkdown, .stSidebar .stSelectbox, .stSidebar .stSlider, 
    .stSidebar .stCheckbox, .stSidebar .stRadio, .stSidebar .stTextInput,
    .stSidebar label, .stSidebar .stButton button,
    .stSidebar .stSelectbox label, .stSidebar .stSlider label,
    .stSidebar .stCheckbox label, .stSidebar .stRadio label {
        color: #ffffff !important;
    }

    .stButton button {
        background: linear-gradient(90deg, #1E6BB0, #0D4A7A);
        color: white;
        border: 1px solid #2A8BCC;
        border-radius: 40px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        transition: 0.1s;
        box-shadow: none;
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #2A8BCC, #1E6BB0);
        transform: none;
        box-shadow: none;
    }

    /* 标题白色渐变 */
    h1, h2, h3, h4, h5, h6 {
        background: linear-gradient(135deg, #ffffff, #dddddd);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-weight: 700;
        letter-spacing: -0.3px;
        text-shadow: none;
        margin-bottom: 0.5rem;
    }

    /* 指标卡片数字亮灰色 */
    .stMetric .stMetric-value {
        color: #d0d0ff !important;
        font-size: 2rem;
        font-weight: 800;
        text-shadow: none;
    }
    .stMetric label {
        color: #bbbbdd !important;
        font-weight: 500;
    }

    /* ========== 表格全局增强（深色主题高对比） ========== */
    /* 自定义 HTML 表格样式（深色主题） */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #1A1D27;
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    .custom-table th {
        background-color: #272B39;
        color: #ffffff;
        font-weight: 700;
        padding: 10px 12px;
        text-align: center;
        border: 1px solid #3A3F51;
    }
    .custom-table td {
        background-color: #1A1D27;
        color: #f0f0f0;
        padding: 8px 12px;
        text-align: center;
        border: 1px solid #3A3F51;
    }
    .custom-table tr:hover td {
        background-color: #2C2F3A;
    }

    /* Streamlit 原生表格样式增强 */
    div[data-testid="stDataFrame"],
    .stDataFrame,
    .stDataFrame table,
    .stDataFrame tbody,
    .stDataFrame tr,
    .stDataFrame td,
    div[data-testid="stDataFrame"] table,
    div[data-testid="stDataFrame"] tbody,
    div[data-testid="stDataFrame"] tr,
    div[data-testid="stDataFrame"] td {
        background-color: #1A1D27 !important;
    }

    .stDataFrame,
    div[data-testid="stDataFrame"] {
        border-radius: 16px !important;
        border: 1px solid #3A3F51 !important;
        overflow: auto !important;
    }

    .stDataFrame th,
    div[data-testid="stDataFrame"] th {
        background: #272B39 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        text-align: center !important;
        border-bottom: 2px solid #3A3F51 !important;
        padding: 0.6rem 0.8rem !important;
    }

    .stDataFrame td,
    div[data-testid="stDataFrame"] td {
        color: #f0f0f0 !important;
        font-weight: 500 !important;
        border-bottom: 1px solid #3A3F51 !important;
        background-color: #1A1D27 !important;
        padding: 0.5rem 0.8rem !important;
    }

    .stDataFrame tr:hover td,
    div[data-testid="stDataFrame"] tr:hover td {
        background-color: #2C2F3A !important;
        transition: background-color 0.1s ease;
    }

    .stDataFrame *,
    div[data-testid="stDataFrame"] * {
        color: #f0f0f0 !important;
    }

    /* 图表文字强制亮色 */
    .js-plotly-plot .main-svg text {
        fill: #eef2ff !important;
    }

    /* 滑块样式 */
    .stSlider .stSlider-track {
        background: #2C2F3A;
    }
    .stSlider .stSlider-thumb {
        background: #9a9ac0;
        box-shadow: none;
    }

    /* 复选框 */
    .stCheckbox .stCheckbox-label {
        color: #ffffff;
    }
    .stCheckbox input:checked + .stCheckbox-checkmark {
        background: #6c6c9e;
    }

    /* 统一所有信息框为卡片风格 */
    .stAlert, .stInfo, .stSuccess, .stWarning, .stError, .stException,
    div[data-testid="stAlert"], div[role="alert"] {
        background: #2D3241 !important;
        color: #eef2ff !important;
        border: 1px solid #272B39 !important;
        border-left: 4px solid #272B39 !important;
        border-radius: 16px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1rem;
        box-shadow: none !important;
    }

    /* 滚动条 */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #1a1c28;
    }
    ::-webkit-scrollbar-thumb {
        background: #3A3F51;
        border-radius: 4px;
    }

    /* 备选方案：顶部栏背景与主背景一致，Deploy 按钮半透明/灰色，不隐藏 */
    header[data-testid="stHeader"] {
        background-color: #191D27 !important;
        border-bottom: 1px solid #272B39;
    }

    header[data-testid="stHeader"] [data-testid="stToolbar"] {
        background: transparent !important;
    }

    .stDeployButton,
    .stDeployButton button {
        background-color: transparent !important;
        color: #aaaaaa !important;
        border: none !important;
        box-shadow: none !important;
    }

    .stDeployButton:hover button {
        color: #ffffff !important;
    }

    /* Folium 地图容器自适应 */
    .folium-map {
        width: 100% !important;
        overflow: hidden !important;
    }
    /* 下载数据库文件按钮样式 */
    .stDownloadButton button {
        background: linear-gradient(90deg, #2C2F3A, #1E202C) !important;
        color: white !important;
        border: 1px solid #272B39 !important;
        border-radius: 40px !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 600 !important;
        transition: 0.1s !important;
        box-shadow: none !important;
    }
    .stDownloadButton button:hover {
        background: linear-gradient(90deg, #3A3F51, #2C2F3A) !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* 充电类型选项框样式 */
    .stSelectbox > div {
        background: linear-gradient(90deg, #2C2F3A, #1E202C) !important;
        border-radius: 40px !important;
        border: 1px solid #272B39 !important;
        padding: 0.2rem 1rem !important;
        color: white !important;
    }
    .stSelectbox div[data-baseweb="select"] {
        background: transparent !important;
        color: white !important;
    }
    .stSelectbox svg {
        fill: white !important;
    }   
    .stSelectbox label {
        color: white !important;
    }
    div[data-baseweb="popover"] ul {
        background: #2D3241 !important;
        color: white !important;
    }

    /* 隐藏样式容器的占位 */
    div.stMarkdown:has(style) {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
    }

    /* 侧边栏折叠按钮（汉堡图标）强制白色 */
    button[data-testid="baseButton-headerNoPadding"] svg,
    div[data-testid="stSidebarCollapsedControl"] svg,
    button[aria-label="Menu"] svg,
    .stSidebar .stSidebarCollapseControl svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    /* 固定侧边栏展开时的宽度 */
    section[data-testid="stSidebar"] {
        width: 260px !important;
        flex-shrink: 0 !important;
    }

    /* 主内容区域自适应 */
    section[data-testid="stSidebar"] + div {
        width: calc(100% - 320px) !important;
        flex: 1 !important;
    }

    /* 控制侧边栏中下载数据库文件按钮的大小 */
    .stDownloadButton button {
        width: 205.32px !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 0.85rem !important;
    }

</style>
""", unsafe_allow_html=True)

# ================== 通用弹出信息样式（用于 Folium 弹窗）==================
def get_popup_html(row):
    # 根据状态设置不同背景颜色
    if row['status'] == '在线':
        status_color = "#00cc44"      # 绿色
    elif row['status'] == '离线':
        status_color = "#ff3333"      # 红色
    else:  # 维护中
        status_color = "#ffaa00"      # 橙色

    return f"""
    <div style="font-size:12px; min-width:240px;">
        <b>{row['name']}</b><br>
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:5px;">
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">类型: {row['type']}</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">利用率: {row['utilization']:.1%}</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">价格: {row['price']}元/度</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">空闲: {row['available_slots']}</span>
            <span style="background:#f0f0f0; padding:2px 6px; border-radius:4px;">功率: {row['power']}kW</span>
            <span style="background:{status_color}; padding:2px 6px; border-radius:4px; color:white;">状态: {row['status']}</span>
        </div>
    </div>
    """

# ================== 地图生成函数（统一使用 Folium + 高德卫星图 style=8）==================
def create_heatmap_fig(data):
    center_lat, center_lon = data['lat'].mean(), data['lon'].mean()
    tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=tiles, attr='高德地图')
    heat_data = [[row['lat'], row['lon'], row['utilization']] for _, row in data.iterrows()]
    HeatMap(heat_data, radius=15, blur=10).add_to(m)
    return m

def create_distribution_fig(data):
    center_lat, center_lon = data['lat'].mean(), data['lon'].mean()
    tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=tiles, attr='高德地图')
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in data.iterrows():
        icon_color = 'red' if row['type'] == '快充' else 'blue'
        folium.Marker(
            [row['lat'], row['lon']],
            popup=get_popup_html(row),
            icon=folium.Icon(color=icon_color, icon='bolt', prefix='fa')
        ).add_to(marker_cluster)
    return m


def create_coverage_map_fig(data):
    center_lat, center_lon = data['lat'].mean(), data['lon'].mean()
    tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=tiles, attr='高德地图')

    # 状态与颜色的映射
    status_color = {
        '在线': 'green',
        '离线': 'red',
        '维护中': 'orange'
    }

    for _, row in data.iterrows():
        color = status_color.get(row['status'], 'gray')
        radius = max(5, min(20, row['power'] / 10))
        folium.CircleMarker(
            [row['lat'], row['lon']],
            radius=radius,
            popup=get_popup_html(row),  # 悬浮窗仍显示完整信息（含利用率）
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6
        ).add_to(m)
    return m

# ================== 导出报告函数 ==================
def export_report(view_mode, filtered_data, display_data, predictions=None):
    """根据当前视图生成 Excel 报告"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 基础站点数据（全量）
        base_df = filtered_data[['name', 'type', 'district', 'utilization', 'price', 'available_slots', 'power', 'status']].copy()
        base_df['utilization'] = base_df['utilization'].apply(lambda x: f"{x:.1%}")
        base_df.to_excel(writer, sheet_name='全量站点数据', index=False)

        # 统计摘要
        summary = pd.DataFrame({
            '指标': ['总站点数', '快充站数', '慢充站数', '平均利用率', '在线站点数', '离线站点数', '维护中站点数'],
            '数值': [
                len(filtered_data),
                len(filtered_data[filtered_data['type']=='快充']),
                len(filtered_data[filtered_data['type']=='慢充']),
                f"{filtered_data['utilization'].mean():.1%}",
                len(filtered_data[filtered_data['status']=='在线']),
                len(filtered_data[filtered_data['status']=='离线']),
                len(filtered_data[filtered_data['status']=='维护中'])
            ]
        })
        summary.to_excel(writer, sheet_name='统计摘要', index=False)

        # 根据视图添加额外数据
        if view_mode == "🔥 热力图":
            high_demand = filtered_data[filtered_data['utilization'] > 0.7].nlargest(10, 'utilization')[['name', 'district', 'utilization']]
            high_demand['utilization'] = high_demand['utilization'].apply(lambda x: f"{x:.1%}")
            high_demand.to_excel(writer, sheet_name='高需求站点', index=False)

        elif view_mode == "🗺️ 分布图":
            type_stats = filtered_data.groupby('type').agg({
                'name': 'count',
                'utilization': 'mean'
            }).rename(columns={'name': '数量', 'utilization': '平均利用率'})
            type_stats['平均利用率'] = type_stats['平均利用率'].apply(lambda x: f"{x:.1%}")
            type_stats.to_excel(writer, sheet_name='类型统计')

        elif view_mode == "📊 覆盖分析":
            status_stats = filtered_data['status'].value_counts().reset_index()
            status_stats.columns = ['状态', '站点数']
            status_stats.to_excel(writer, sheet_name='状态统计', index=False)

        elif view_mode == "🔮 预测分析" and predictions is not None:
            # 当前与预测对比
            filtered_data_with_pred = filtered_data.copy()
            filtered_data_with_pred['预测利用率'] = predictions
            filtered_data_with_pred['利用率差异'] = filtered_data_with_pred['预测利用率'] - filtered_data_with_pred['utilization']
            pred_df = filtered_data_with_pred[['name', 'district', 'type', 'utilization', '预测利用率', '利用率差异']].copy()
            pred_df['utilization'] = pred_df['utilization'].apply(lambda x: f"{x:.1%}")
            pred_df['预测利用率'] = pred_df['预测利用率'].apply(lambda x: f"{x:.1%}")
            pred_df['利用率差异'] = pred_df['利用率差异'].apply(lambda x: f"{x:+.1%}")
            pred_df.to_excel(writer, sheet_name='当前vs预测', index=False)

        elif view_mode == "💡 优化建议":
            high_demand = filtered_data[filtered_data['utilization'] > 0.7].nlargest(10, 'utilization')[['name', 'district', 'utilization']]
            low_util = filtered_data[filtered_data['utilization'] < 0.3].nsmallest(10, 'utilization')[['name', 'district', 'utilization']]
            high_demand['utilization'] = high_demand['utilization'].apply(lambda x: f"{x:.1%}")
            low_util['utilization'] = low_util['utilization'].apply(lambda x: f"{x:.1%}")
            high_demand.to_excel(writer, sheet_name='高需求站点（扩容）', index=False)
            low_util.to_excel(writer, sheet_name='低利用率站点（优化）', index=False)

        elif view_mode == "💼 招商引资":
            region_invest = filtered_data.groupby('district').agg({
                'utilization': 'mean',
                'name': 'count'
            }).rename(columns={'name': '站点数', 'utilization': '平均利用率'}).reset_index()
            region_invest['平均利用率'] = region_invest['平均利用率'].apply(lambda x: f"{x:.1%}")
            region_invest = region_invest.sort_values('平均利用率', ascending=False)
            region_invest.to_excel(writer, sheet_name='区域投资潜力', index=False)

        elif view_mode == "😊 满意度分析":
            # 计算满意度
            max_price = filtered_data['price'].max()
            if max_price == 0:
                max_price = 1
            sat_data = filtered_data.copy()
            sat_data['price_coef'] = sat_data['price'] / max_price
            sat_data['satisfaction'] = (1 - sat_data['utilization'] * 0.3 - sat_data['price_coef'] * 0.4 + (sat_data['available_slots'] / 10) * 0.3).clip(0, 1) * 100
            sat_data[['name', 'district', 'type', 'utilization', 'price', 'satisfaction']].to_excel(writer, sheet_name='满意度分析', index=False)

    output.seek(0)
    return output

# ================== 侧边栏 ==================
with st.sidebar:
    st.header("🎛️ 控制面板")
    use_real = st.checkbox("使用真实数据（高德API）", value=False)
    processor = DataProcessor(use_real_data=use_real)
    processor.db_path = os.path.join(base_dir, "data", "charger_data.db")

    view_mode = st.radio(
        "选择分析视图",
        ["🔥 热力图", "🗺️ 分布图", "📊 覆盖分析", "😊 满意度分析", "🔮 预测分析", "💡 优化建议", "💼 招商引资", "📈 政策模拟器"],
        index=0
    )
    selected_type = st.radio(
        "充电类型",
        ["全部", "快充", "慢充"],
        horizontal=True,
        index=0
    )

    max_display = st.slider(
        "最大显示充电桩数",
        min_value=50,
        max_value=150,  # 改为150
        value=150,  # 默认值也改为150
        step=25,  # 步长改为25，更精细
        help="减少显示数量可大幅提升地图渲染性能（统计指标仍基于全量数据）"
    )

    st.subheader("📺 大屏轮播模式")
    enable_carousel = st.checkbox("开启自动轮播", value=False)
    if enable_carousel:
        auto_play_speed = st.slider("轮播间隔（秒）", 2, 10, 5)
    else:
        auto_play_speed = 5

    st.subheader("🗄️ 数据库管理")
    last_time = processor.get_db_update_time()
    if last_time:
        st.info(f"数据最后更新: {last_time}")
    else:
        st.info("暂无数据记录")

    if st.button("🔄 刷新数据（从API）"):
        with st.spinner("正在从高德API获取最新数据..."):
            processor.load_charger_data(use_cache=False)
            st.cache_data.clear()
            st.rerun()

    if os.path.exists(processor.db_path):
        with open(processor.db_path, "rb") as f:
            st.download_button(
                label="⬇️ 下载数据库文件",
                data=f,
                file_name="charger_data.db",
                mime="application/octet-stream"
            )
    else:
        st.warning("数据库文件不存在，请先加载数据")

# ---------- 数据缓存 ----------
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_charger_data(use_real):
    temp_processor = DataProcessor(use_real_data=use_real)
    return temp_processor.load_charger_data(use_cache=True, cache_hours=24)

with st.spinner("正在加载充电桩数据..."):
    charger_data = get_cached_charger_data(use_real)

def extract_district(address):
    # 北京全部行政区列表
    districts = [
        '东城区', '西城区', '朝阳区', '海淀区', '丰台区', '石景山区',
        '通州区', '大兴区', '房山区', '门头沟区', '昌平区', '顺义区',
        '密云区', '怀柔区', '平谷区', '延庆区'
    ]
    for d in districts:
        if d in address:
            return d
    # 处理简称或模糊匹配
    if '东城' in address: return '东城区'
    if '西城' in address: return '西城区'
    if '朝阳' in address: return '朝阳区'
    if '海淀' in address: return '海淀区'
    if '丰台' in address: return '丰台区'
    if '石景山' in address: return '石景山区'
    if '通州' in address: return '通州区'
    if '大兴' in address: return '大兴区'
    if '房山' in address: return '房山区'
    if '门头沟' in address: return '门头沟区'
    if '昌平' in address: return '昌平区'
    if '顺义' in address: return '顺义区'
    if '密云' in address: return '密云区'
    if '怀柔' in address: return '怀柔区'
    if '平谷' in address: return '平谷区'
    if '延庆' in address: return '延庆区'
    return '其他区域'  # 保底

charger_data['district'] = charger_data['address'].apply(extract_district)
# 增加站点状态模拟（在线/离线/维护中）
np.random.seed(42)  # 固定随机种子，保证每次运行一致
charger_data['status'] = np.random.choice(
    ['在线', '离线', '维护中'],
    size=len(charger_data),
    p=[0.85, 0.10, 0.05]  # 85%在线，10%离线，5%维护中
)

# 二次修正：对 district 为“其他区域”的行，尝试从 address 和 name 中再次提取
def refine_district_global(row):
    if row['district'] != '其他区域':
        return row['district']
    text = str(row.get('address', '')) + str(row.get('name', ''))
    return extract_district(text)

# 只对“其他区域”的行应用修正
mask = charger_data['district'] == '其他区域'
charger_data.loc[mask, 'district'] = charger_data[mask].apply(refine_district_global, axis=1)

@st.cache_data(ttl=3600, show_spinner=False)
def get_filtered_data(data, selected_type):
    if selected_type == "全部":
        return data
    return data[data['type'] == selected_type]

filtered_data = get_filtered_data(charger_data, selected_type)

# 生成抽样数据
if len(filtered_data) > max_display:
    display_data = filtered_data.sample(n=max_display, random_state=42)
else:
    display_data = filtered_data

# 预测缓存
@st.cache_data(ttl=3600, show_spinner=False)
def get_predictions(data):
    temp_processor = DataProcessor(use_real_data=use_real)
    return temp_processor.simple_demand_prediction(data)

predictions = get_predictions(filtered_data) if view_mode in ["🔮 预测分析", "💼 招商引资"] else None

# ================== 视图渲染函数（供单视图和轮播复用）==================
def render_heatmap():
    st.subheader("🔥 充电需求热力图")
    m_heat = create_heatmap_fig(display_data)
    st_folium(m_heat, width='100%', height=500)

    # 数据指标卡片
    avg_util = display_data['utilization'].mean()
    high_demand_count = len(display_data[display_data['utilization'] > 0.7])
    low_demand_count = len(display_data[display_data['utilization'] < 0.3])
    top_stations = display_data.nlargest(3, 'utilization')[['name', 'utilization']]

    col1, col2, col3 = st.columns(3)
    col1.metric("平均利用率", f"{avg_util:.1%}")
    col2.metric("高需求站点 (>70%)", high_demand_count)
    col3.metric("低需求站点 (<30%)", low_demand_count)

    if not top_stations.empty:
        st.write("**利用率 TOP3 站点**")
        # 转换为自定义 HTML 表格
        top_stations['utilization'] = top_stations['utilization'].map(lambda x: f"{x:.1%}")
        html_table = top_stations.to_html(index=False, classes='custom-table', escape=False)
        st.markdown(html_table, unsafe_allow_html=True)

    # 利用率分布直方图
    fig_hist = px.histogram(display_data, x='utilization', nbins=20, title="充电站利用率分布",
                            labels={'utilization': '利用率', 'count': '站点数'})
    fig_hist.update_layout(bargap=0.1)
    st.plotly_chart(fig_hist, use_container_width=True)

def render_distribution():
    st.subheader("🗺️ 充电设施分布图")
    m_dist = create_distribution_fig(display_data)
    st_folium(m_dist, width='100%', height=500)
    with st.container():
        st.markdown("""
        <div style="display: flex; justify-content: center; gap: 30px; 
                    padding: 4px 0 4px 0;
                    margin-bottom: 20px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #FF4136; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: white;">快充站</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #0074D9; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: white;">慢充站</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="color: white;">气泡大小 = 利用率</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    fast_count = len(display_data[display_data['type'] == '快充'])
    slow_count = len(display_data[display_data['type'] == '慢充'])
    fast_avg_util = display_data[display_data['type'] == '快充']['utilization'].mean() if fast_count > 0 else 0
    slow_avg_util = display_data[display_data['type'] == '慢充']['utilization'].mean() if slow_count > 0 else 0

    col1, col2 = st.columns(2)
    col1.metric("快充站数量", fast_count, delta=f"{fast_avg_util:.1%} 平均利用率")
    col2.metric("慢充站数量", slow_count, delta=f"{slow_avg_util:.1%} 平均利用率")

    # 快充/慢充利用率对比柱状图
    comp_df = pd.DataFrame({
        '类型': ['快充', '慢充'],
        '平均利用率': [fast_avg_util, slow_avg_util]
    })
    fig_bar = px.bar(comp_df, x='类型', y='平均利用率', color='类型',
                     color_discrete_map={'快充': '#FF4136', '慢充': '#0074D9'},
                     title="快充 vs 慢充 平均利用率对比", text_auto='.1%')
    st.plotly_chart(fig_bar, use_container_width=True)


def render_coverage():
    st.subheader("📊 服务覆盖范围分析")
    m_cov = create_coverage_map_fig(display_data)
    st_folium(m_cov, width='100%', height=500)

    with st.container():
        st.markdown("""
        <div style="display: flex; justify-content: center; gap: 30px; 
                    padding: 4px 0 4px 0;
                    margin-bottom: 20px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #00cc44; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: white;"> 在线</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #ff3333; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: white;"> 离线</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #ffa500; border-radius: 50%; margin-right: 8px;"></div>
                <span style="color: white;"> 维护中</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="color: white;">⚪ 气泡大小 = 功率</span>
            </div>
            <div style="display: flex; align-items: center;">
                <span style="color: white;">🔍 悬停查看利用率等详情</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 指标卡片
    status_counts = filtered_data['status'].value_counts()
    st.subheader("📊 充电桩实时运行状态统计")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("在线", status_counts.get('在线', 0))
    col_s2.metric("离线", status_counts.get('离线', 0))
    col_s3.metric("维护中", status_counts.get('维护中', 0))

    # 饼图
    fig_pie = px.pie(values=status_counts.values, names=status_counts.index, title="运行状态占比")
    st.plotly_chart(fig_pie, use_container_width=True)

    # 需关注站点表格（自定义HTML）
    problem_stations = filtered_data[filtered_data['status'].isin(['离线', '维护中'])]
    if not problem_stations.empty:
        st.write("⚠️ **需关注站点（离线/维护中）**")
        df_problem = problem_stations[['name', 'district', 'status', 'utilization', 'type']].reset_index(drop=True)
        df_problem['utilization'] = df_problem['utilization'].apply(lambda x: f"{x:.1%}")
        st.markdown(df_problem.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)

def render_prediction():
    st.subheader("⚙️ 预测参数设置")
    col_param1, col_param2 = st.columns(2)
    with col_param1:
        growth_rate = st.slider("基准增长率", 0.8, 2.0, 1.2, 0.05)
    with col_param2:
        seasonal_factor = st.slider("季节性因子（冬季）", 0.8, 1.5, 1.1, 0.05)
    pred_full = get_predictions(filtered_data)
    display_indices = display_data.index
    pred_display = [pred_full[i] for i in range(len(filtered_data)) if filtered_data.index[i] in display_indices]
    # 加入随机波动，使散点图不再呈现平滑线性关系
    import random
    random.seed(42)  # 固定种子，保证每次运行结果一致
    adjusted_pred_display = []
    for i, p in enumerate(pred_display):
        base_pred = p * growth_rate * (seasonal_factor if i % 3 == 0 else 1.0)
        fluctuation = random.uniform(-0.1, 0.15) * (1 - base_pred * 0.5)
        pred_val = base_pred + fluctuation
        adjusted_pred_display.append(min(0.95, max(0.05, pred_val)))
    data_pred_display = display_data.copy()
    data_pred_display['predicted'] = adjusted_pred_display

    col1, col2 = st.columns(2)
    with col1:
        fig_scatter = px.scatter(
            data_pred_display, x='utilization', y='predicted',
            color='type', size='power', opacity=0.6,
            color_discrete_map={"快充": "#FF4136", "慢充": "#0074D9"},
            trendline="ols",
            title="当前 vs 预测需求（抽样数据）",
            labels={'utilization': '当前利用率', 'predicted': '预测利用率'}
        )
        fig_scatter.update_layout(
            autosize=True,
            margin=dict(l=60, r=60, t=40, b=20),
            legend=dict(
                title=dict(text='充电类型', font=dict(color='white', size=14)),
                font=dict(color='white', size=14),
                bgcolor='rgba(0,0,0,0.6)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
            yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'))
        )
        st.plotly_chart(fig_scatter, use_container_width=True, config={'responsive': True})

    with col2:
        months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
        hist_demand = [100, 120, 150, 180, 210, 240]  # 历史6个月

        # 基础预测值（无波动）
        base_pred = [240, 270, 300, 330, 360, 390]
        # 应用增长率和季节性因子
        base_pred = [int(v * growth_rate) for v in base_pred]
        # 对第4、6个月应用季节性因子（冬季）
        base_pred[0] = int(base_pred[0] * seasonal_factor)  # 7月（冬季）
        base_pred[4] = int(base_pred[4] * seasonal_factor)  # 11月（冬季）

        # 加入随机波动（±8%），使趋势线有起伏
        import random
        random.seed(123)  # 固定种子，保证每次运行结果一致
        pred_demand = []
        for v in base_pred:
            fluctuation = random.uniform(0.92, 1.08)
            pred_demand.append(int(v * fluctuation))

        all_months = months[:6] + months[6:]
        all_demand = hist_demand + pred_demand
        colors = ['#2ECC40'] * 6 + ['#FF4136'] * 6

        fig_combo = go.Figure()
        fig_combo.add_trace(go.Bar(
            x=all_months, y=all_demand,
            marker_color=colors,
            text=all_demand,
            textposition='outside'
        ))
        fig_combo.add_trace(go.Scatter(
            x=months[5:],  # 从6月开始，连接历史最后一点和预测各点
            y=[hist_demand[-1]] + pred_demand,
            mode='lines+markers',
            name='趋势线',
            line=dict(color='black', width=2, dash='dash')
        ))
        fig_combo.update_layout(
            title="月度需求预测",
            xaxis_title="月份",
            yaxis_title="充电需求量 (相对值)",
            autosize=True,
            margin=dict(l=60, r=60, t=40, b=20),
            legend=dict(
                font=dict(color='white', size=14),
                bgcolor='rgba(0,0,0,0.6)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
            yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'))
        )
        st.plotly_chart(fig_combo, use_container_width=True, config={'responsive': True})

    st.subheader("📊 各区域需求对比预测")
    # 获取所有实际存在的区域，过滤掉 '其他区域'
    existing_districts = [d for d in filtered_data['district'].unique() if d != '其他区域']
    # 如果实际区域少于8个，补充常见行政区（确保柱子数量）
    all_common_districts = ['东城区', '西城区', '朝阳区', '海淀区', '丰台区', '石景山区',
                            '通州区', '大兴区', '昌平区', '顺义区', '房山区', '门头沟区']
    if len(existing_districts) < 8:
        districts = list(set(existing_districts + all_common_districts))
    else:
        districts = existing_districts

    region_pred = {}
    import random
    for d in districts:
        sub_data = filtered_data[filtered_data['district'] == d]
        if len(sub_data) > 0:
            avg_util = sub_data['utilization'].mean()
        else:
            # 无真实数据时，基于区域名生成一个基准值（0.3~0.8）
            avg_util = 0.3 + (hash(d) % 50) / 100
            avg_util = min(0.85, avg_util)

        # 区域系数：中心区增速慢，郊区增速快
        core_districts = ['东城区', '西城区', '朝阳区', '海淀区']
        suburban_districts = ['通州区', '大兴区', '昌平区', '顺义区', '房山区', '门头沟区', '密云区', '怀柔区',
                              '平谷区', '延庆区']
        if d in core_districts:
            region_factor = 0.85
        elif d in suburban_districts:
            region_factor = 1.25
        else:
            region_factor = 1.0

        # 随机波动（基于区域名哈希，保证每次运行结果一致）
        random.seed(hash(d) % 10000)
        fluctuation = 0.85 + random.random() * 0.3  # 0.85 ~ 1.15

        pred_val = avg_util * growth_rate * region_factor * fluctuation
        pred_val = min(0.95, pred_val)
        region_pred[d] = pred_val

    pred_df = pd.DataFrame(list(region_pred.items()), columns=['区域', '预测利用率'])
    pred_df = pred_df.sort_values('预测利用率', ascending=False)
    fig_reg = px.bar(pred_df, x='区域', y='预测利用率', color='预测利用率',
                     color_continuous_scale='RdYlGn_r',
                     title="各区域未来需求预测对比",
                     text_auto='.1%')
    fig_reg.update_layout(
        autosize=True,
        margin=dict(l=60, r=60, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'), tickangle=-45),
        yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
        coloraxis_colorbar=dict(
            title=dict(text='预测利用率', font=dict(color='white', size=14)),
            tickfont=dict(color='white', size=12),
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='white'
        )
    )
    st.plotly_chart(fig_reg, use_container_width=True, config={'responsive': True})

    # 用指标卡片代替文字结论
    col_g1, col_g2 = st.columns(2)
    col_g1.metric("预期需求增长率", f"{int((growth_rate - 1) * 100)}%")
    col_g2.metric("冬季需求高峰因子", f"{seasonal_factor}")

def render_optimization():
    st.subheader("💡 布局优化建议")
    high_demand_full = filtered_data[filtered_data['utilization'] > 0.7]
    low_util_full = filtered_data[filtered_data['utilization'] < 0.3]

    col1, col2 = st.columns([2, 1])
    with col1:
        high_demand_disp = display_data[display_data['utilization'] > 0.7]
        low_util_disp = display_data[display_data['utilization'] < 0.3]
        center_lat = display_data['lat'].mean()
        center_lon = display_data['lon'].mean()
        tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=tiles, attr='高德地图')
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in high_demand_disp.iterrows():
            folium.Marker(
                [row['lat'], row['lon']],
                popup=get_popup_html(row),
                icon=folium.Icon(color='red', icon='bolt', prefix='fa')
            ).add_to(marker_cluster)

        for _, row in low_util_disp.iterrows():
            folium.Marker(
                [row['lat'], row['lon']],
                popup=get_popup_html(row),
                icon=folium.Icon(color='green', icon='bolt', prefix='fa')
            ).add_to(marker_cluster)

        top_demand = display_data.nlargest(10, 'utilization')
        recommended_locations = []
        for _, row in top_demand.iterrows():
            offsets = [(0.001, 0.001), (0.001, -0.001), (-0.001, 0.001), (-0.001, -0.001), (0.002, 0)]
            for dx, dy in offsets:
                new_lat = row['lat'] + dx
                new_lon = row['lon'] + dy
                if not any(abs(new_lat - r[0]) < 0.0005 and abs(new_lon - r[1]) < 0.0005 for r in recommended_locations):
                    recommended_locations.append((new_lat, new_lon, row['name']))
                    if len(recommended_locations) >= 8:
                        break
            if len(recommended_locations) >= 8:
                break

        for lat, lon, near_station in recommended_locations:
            popup_html = f"""
            <div style="font-size:12px; min-width:180px;">
                <b>🚀 推荐新建充电桩</b><br>
                靠近：{near_station}<br>
                理由：高需求区域，现有站点利用率过高
            </div>
            """
            folium.Marker(
                [lat, lon],
                popup=popup_html,
                icon=folium.Icon(color='purple', icon='star', prefix='fa')
            ).add_to(m)

        st_folium(m, width='100%', height=500)

    with col2:
        st.metric("高需求站点（建议扩容）", len(high_demand_full))
        st.metric("低利用率站点（建议优化）", len(low_util_full))
        st.metric("推荐新建点位", len(recommended_locations))

    # ========== 新增：充电桩利用率排名与对比 ==========
    st.subheader("📊 充电桩利用率排名与对比")

    col_rank1, col_rank2 = st.columns(2)
    with col_rank1:
        st.write("**🔥 利用率最高 TOP10**")
        top10 = filtered_data.nlargest(10, 'utilization')[['name', 'district', 'type', 'utilization', 'power']].copy()
        top10['utilization'] = top10['utilization'].map(lambda x: f"{x:.1%}")
        # 自定义 HTML 表格
        st.markdown(top10.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)

    with col_rank2:
        st.write("**❄️ 利用率最低 BOTTOM10**")
        bottom10 = filtered_data.nsmallest(10, 'utilization')[['name', 'district', 'type', 'utilization', 'power']].copy()
        bottom10['utilization'] = bottom10['utilization'].map(lambda x: f"{x:.1%}")
        st.markdown(bottom10.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)

    # 区域对比柱状图
    region_avg = filtered_data.groupby('district')['utilization'].mean().reset_index()
    region_avg = region_avg.sort_values('utilization', ascending=False)
    fig_region = px.bar(region_avg, x='district', y='utilization',
                         title="各区域平均利用率对比",
                         labels={'utilization': '平均利用率', 'district': '区域'},
                         text_auto='.1%',
                         color='utilization', color_continuous_scale='RdYlGn_r')
    fig_region.update_layout(
        autosize=True,
        margin=dict(l=60, r=60, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'), tickangle=-45),
        yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'))
    )
    st.plotly_chart(fig_region, use_container_width=True)

    # 类型对比箱线图
    fig_type = px.box(filtered_data, x='type', y='utilization',
                       title="快充 vs 慢充 利用率分布",
                       labels={'type': '充电类型', 'utilization': '利用率'},
                       color='type', color_discrete_map={"快充": "#FF4136", "慢充": "#0074D9"})
    fig_type.update_layout(
        autosize=True,
        margin=dict(l=60, r=60, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
        yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
        legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0.6)')
    )
    st.plotly_chart(fig_type, use_container_width=True)

    # ========== 原有优化建议表格（优先扩容/改造站点） ==========
    st.subheader("📋 具体优化方案")
    if not high_demand_full.empty:
        high_demand_filtered = high_demand_full[high_demand_full['district'] != '其他区域']
        if not high_demand_filtered.empty:
            st.markdown("**优先扩容区域**")
            df_top5 = high_demand_filtered.nlargest(5, 'utilization')[['name', 'district', 'utilization']]
            df_top5['utilization'] = df_top5['utilization'].map(lambda x: f"{x:.1%}")
            st.markdown(df_top5.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)

    if not low_util_full.empty:
        st.markdown("**优先改造站点**")
        df_bottom5 = low_util_full.nsmallest(5, 'utilization')[['name', 'district', 'utilization']]
        df_bottom5['utilization'] = df_bottom5['utilization'].map(lambda x: f"{x:.1%}")
        st.markdown(df_bottom5.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)

    st.subheader("📊 多方案投资回报对比")
    scenarios = pd.DataFrame({
        "方案": ["方案A: 新建5个快充站", "方案B: 改造10个慢充站", "方案C: 混合策略"],
        "投资额(万元)": [800, 300, 1000],
        "预期利用率提升": ["15%", "20%", "25%"],
        "回收期(年)": [3, 2.5, 3.2]
    })
    st.markdown(scenarios.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)

    # 模拟推荐选择（用指标卡片显示推荐理由）
    reason_map = {
        "方案A: 新建5个快充站": "投资额较高（800万元），预期利用率提升15%，回收期3年，适合长期战略布局。",
        "方案B: 改造10个慢充站": "投资额最低（300万元），预期利用率提升20%，回收期仅2.5年，**性价比最高**。",
        "方案C: 混合策略": "投资额最大（1000万元），预期利用率提升25%最高，但回收期较长（3.2年），适合资金充裕的快速扩张。"
    }
    selected_scenario = st.radio(
        "推荐方案选择",
        options=scenarios['方案'].tolist(),
        index=1,
        format_func=lambda x: x
    )
    st.info(f"**方案详情**：{reason_map[selected_scenario]}")

    # 将建议文本改为列表形式（仍可保留少量文字，但用项目符号代替大段描述）
    st.markdown("**📌 核心行动项**")
    st.markdown("- 在国贸、望京等5个高需求盲区新建快充站（预计覆盖率提升8%）")
    st.markdown("- 将10个低效慢充站改为快充站（预计利用率提升20%）")
    st.markdown("- 对利用率<30%的站点实施分时优惠（引导用户分流）")


def render_optimization_simple():
    """大屏轮播模式下的优化建议（含地图，精简版）"""
    st.subheader("💡 布局优化建议（精简版）")

    high_demand_full = filtered_data[filtered_data['utilization'] > 0.7]
    low_util_full = filtered_data[filtered_data['utilization'] < 0.3]

    # 推荐新建点位（基于高需求站点）
    recommended_count = min(len(high_demand_full), 8)

    # 使用 display_data 绘制地图（避免全量数据过慢）
    high_demand_disp = display_data[display_data['utilization'] > 0.7]
    low_util_disp = display_data[display_data['utilization'] < 0.3]

    # 生成推荐点位（简单策略：在高需求站点附近偏移）
    top_demand = display_data.nlargest(10, 'utilization')
    recommended_locations = []
    for _, row in top_demand.iterrows():
        offsets = [(0.001, 0.001), (0.001, -0.001), (-0.001, 0.001), (-0.001, -0.001)]
        for dx, dy in offsets:
            new_lat = row['lat'] + dx
            new_lon = row['lon'] + dy
            if not any(abs(new_lat - r[0]) < 0.0005 and abs(new_lon - r[1]) < 0.0005 for r in recommended_locations):
                recommended_locations.append((new_lat, new_lon, row['name']))
                if len(recommended_locations) >= 8:
                    break
        if len(recommended_locations) >= 8:
            break

    # 构建地图
    center_lat = display_data['lat'].mean()
    center_lon = display_data['lon'].mean()
    tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=tiles, attr='高德地图')
    marker_cluster = MarkerCluster().add_to(m)

    # 高需求站点（红色）
    for _, row in high_demand_disp.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=get_popup_html(row),
            icon=folium.Icon(color='red', icon='bolt', prefix='fa')
        ).add_to(marker_cluster)

    # 低利用率站点（绿色）
    for _, row in low_util_disp.iterrows():
        folium.Marker(
            [row['lat'], row['lon']],
            popup=get_popup_html(row),
            icon=folium.Icon(color='green', icon='bolt', prefix='fa')
        ).add_to(marker_cluster)

    # 推荐新建点位（紫色星星）
    for lat, lon, near_station in recommended_locations:
        popup_html = f"""
        <div style="font-size:12px; min-width:180px;">
            <b>🚀 推荐新建充电桩</b><br>
            靠近：{near_station}<br>
            理由：高需求区域，现有站点利用率过高
        </div>
        """
        folium.Marker(
            [lat, lon],
            popup=popup_html,
            icon=folium.Icon(color='purple', icon='star', prefix='fa')
        ).add_to(m)

    st_folium(m, width='100%', height=500)

    # 指标卡片
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("高需求站点（建议扩容）", len(high_demand_full))
    with col2:
        st.metric("低利用率站点（建议优化）", len(low_util_full))
    with col3:
        st.metric("推荐新建点位", len(recommended_locations))

    st.markdown("**📌 核心建议**")
    st.markdown("- 优先在利用率 >70% 的区域新建快充站（地图红色标记）")
    st.markdown("- 对利用率 <30% 的站点实施价格引导或迁移（地图绿色标记）")
    st.markdown("- 紫色星星为推荐新建点位")

def render_satisfaction():
    """独立的满意度分析视图"""
    st.subheader("😊 用户投诉与满意度分析")

    # 计算满意度
    max_price = filtered_data['price'].max()
    if max_price == 0:
        max_price = 1
    filtered_data_local = filtered_data.copy()
    filtered_data_local['price_coef'] = filtered_data_local['price'] / max_price
    filtered_data_local['satisfaction'] = (1 - filtered_data_local['utilization'] * 0.3
                                            - filtered_data_local['price_coef'] * 0.4
                                            + (filtered_data_local['available_slots'] / 10) * 0.3)
    filtered_data_local['satisfaction'] = filtered_data_local['satisfaction'].clip(0, 1) * 100

    avg_satisfaction = filtered_data_local['satisfaction'].mean()
    high_sat_count = len(filtered_data_local[filtered_data_local['satisfaction'] > 80])
    low_sat_count = len(filtered_data_local[filtered_data_local['satisfaction'] < 60])

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("综合满意度", f"{avg_satisfaction:.1f} 分")
    col_s2.metric("高满意度站点 (>80分)", high_sat_count)
    col_s3.metric("低满意度站点 (<60分)", low_sat_count)

    # 满意度分布地图
    st.write("**各站点用户满意度分布（颜色越绿满意度越高）**")
    center_lat_sat = display_data['lat'].mean()
    center_lon_sat = display_data['lon'].mean()
    tiles_sat = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m_sat = folium.Map(location=[center_lat_sat, center_lon_sat], zoom_start=11, tiles=tiles_sat, attr='高德地图')

    display_data_with_sat = display_data.copy()
    sat_dict = filtered_data_local.set_index(display_data.index)['satisfaction'].to_dict()
    display_data_with_sat['satisfaction'] = display_data_with_sat.index.map(lambda idx: sat_dict.get(idx, 50))

    for _, row in display_data_with_sat.iterrows():
        sat_score = row['satisfaction']
        if sat_score >= 80:
            color = 'green'
        elif sat_score >= 60:
            color = 'orange'
        else:
            color = 'red'
        folium.CircleMarker(
            [row['lat'], row['lon']],
            radius=8,
            popup=get_popup_html(row),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            tooltip=f"{row['name']}: {sat_score:.1f}分"
        ).add_to(m_sat)

    st_folium(m_sat, width='100%', height=500)

    # 低满意度站点列表（自定义 HTML）
    low_satisfaction = filtered_data_local[filtered_data_local['satisfaction'] < 60].nlargest(10, 'satisfaction')
    if not low_satisfaction.empty:
        st.write("⚠️ **需重点改进的站点（满意度低于60分）**")
        df_low_sat = low_satisfaction[['name', 'district', 'type', 'satisfaction', 'utilization', 'price']].copy()
        df_low_sat['satisfaction'] = df_low_sat['satisfaction'].round(1)
        df_low_sat['utilization'] = df_low_sat['utilization'].map(lambda x: f"{x:.1%}")
        st.markdown(df_low_sat.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)
    else:
        st.success("所有站点满意度均在60分以上")

    # 满意度与利用率关系散点图
    st.subheader("📈 满意度 vs 利用率分析")
    fig_scatter_sat = px.scatter(
        filtered_data_local, x='utilization', y='satisfaction',
        color='type', size='power', hover_name='name',
        title="满意度与利用率关系",
        labels={'utilization': '利用率', 'satisfaction': '满意度（分）'},
        color_discrete_map={"快充": "#FF4136", "慢充": "#0074D9"}
    )
    fig_scatter_sat.update_layout(
        autosize=True,
        margin=dict(l=60, r=60, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
        yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
        legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0.6)')
    )
    st.plotly_chart(fig_scatter_sat, use_container_width=True)

    # 用指标卡片展示满意度占比
    sat_ratio = high_sat_count / len(filtered_data_local)
    st.metric("高满意度站点占比", f"{sat_ratio:.1%}")

def render_investment():
    st.subheader("💼 招商引资 - 投资潜力与政策")

    # 第一行：地图 + 投资回报表格（比例 2:1）
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        m_potential = create_heatmap_fig(display_data)
        st_folium(m_potential, width='100%', height=500)

    with row1_col2:
        st.markdown("<h3 style='margin-top:0; margin-bottom:0.5rem;'>📈 投资回报测算（示例）</h3>", unsafe_allow_html=True)
        invest_data = pd.DataFrame({
            "区域": ["国贸商圈", "中关村", "望京", "亦庄"],
            "预计投资(万元)": [500, 400, 450, 300],
            "年收益(万元)": [200, 150, 180, 120],
            "回收期(年)": [2.5, 2.7, 2.5, 2.5]
        })
        st.markdown(invest_data.to_html(index=False, classes='custom-table', escape=False), unsafe_allow_html=True)

    # 第二行：合作意向登记 + 优惠政策
    row2_col1, row2_col2 = st.columns([2, 1])

    with row2_col1:
        st.markdown("<h3 style='margin-top:0rem; margin-bottom:0.5rem;'>📝 合作意向登记</h3>", unsafe_allow_html=True)
        with st.form("investment_form"):
            name = st.text_input("企业名称", placeholder="请输入企业名称")
            contact = st.text_input("联系人", placeholder="请输入联系人姓名")
            submitted = st.form_submit_button("提交意向")
            if submitted:
                if not name.strip():
                    st.error("请填写企业名称")
                elif not contact.strip():
                    st.error("请填写联系人")
                else:
                    st.success(f"已收到 {name} 的合作意向，我们将尽快与您联系。")
    with row2_col2:
        st.markdown("<h3 style='margin-top:0rem; margin-bottom:0.5rem;'>🏛️ 优惠政策</h3>", unsafe_allow_html=True)
        st.info("""
        - **土地优惠**：提供充电站建设用地优先审批
        - **电价补贴**：前三年充电服务费减免20%
        - **税收减免**：企业所得税三免三减半
        """)

    # 推荐投资区域
    st.subheader("🏆 推荐投资区域")
    region_df = filtered_data[['district', 'utilization', 'address', 'name']].copy()

    def refine_district_for_region(row):
        if row['district'] not in ['其他', '其他区域']:
            return row['district']
        text = str(row.get('address', '')) + str(row.get('name', ''))
        districts_keywords = [
            ('东城', '东城区'), ('西城', '西城区'), ('朝阳', '朝阳区'),
            ('海淀', '海淀区'), ('丰台', '丰台区'), ('石景山', '石景山区'),
            ('通州', '通州区'), ('大兴', '大兴区'), ('房山', '房山区'),
            ('门头沟', '门头沟区'), ('昌平', '昌平区'), ('顺义', '顺义区'),
            ('密云', '密云区'), ('怀柔', '怀柔区'), ('平谷', '平谷区'),
            ('延庆', '延庆区')
        ]
        for kw, full_name in districts_keywords:
            if kw in text:
                return full_name
        return '其他区域（待细化）'

    region_df['district'] = region_df.apply(refine_district_for_region, axis=1)
    top_regions = region_df.groupby('district')['utilization'].mean().reset_index()
    top_regions = top_regions.sort_values('utilization', ascending=False).head(5)
    top_regions['utilization'] = top_regions['utilization'].map(lambda x: f"{x:.1%}")
    top_regions = top_regions[top_regions['district'] != '其他区域（待细化）']
    st.markdown(top_regions.to_html(index=False, columns=["district", "utilization"],
                                    header=["区域", "平均利用率"], classes='custom-table', escape=False),
                unsafe_allow_html=True)

    # 投资回报柱状图
    st.subheader("📊 区域投资回报潜力")
    fig_roi = px.bar(top_regions, x='district', y='utilization', color='utilization',
                     title="高潜力区域平均利用率", labels={'utilization': '平均利用率'})
    st.plotly_chart(fig_roi, use_container_width=True)

def render_policy_simulator():
    st.subheader("📈 政策模拟器 · 参数调整与效果预测")

    st.markdown("""
    **说明**：调整下方政策参数，系统将基于当前数据模拟对充电桩利用率的影响。
    下方**利用率变化地图**直观展示每个站点利用率的升降（红色↑上升，蓝色↓下降），圆圈越大变化幅度越大。
    """)

    # 当前基准数据
    base_data = filtered_data.copy()
    total_stations = len(base_data)
    avg_util_base = base_data['utilization'].mean()
    high_demand_ratio_base = len(base_data[base_data['utilization'] > 0.7]) / total_stations

    # 碳减排基准
    total_power_base = (base_data['utilization'] * base_data['power'] * 24 * 365 * 0.5).sum() / 1000
    co2_reduction_base = total_power_base * 0.6

    # 参数控件
    col_param1, col_param2 = st.columns(2)
    with col_param1:
        new_fast_stations = st.slider(
            "🚀 新建快充站数量",
            min_value=0, max_value=30, value=5, step=1,
            help="在现有高需求区域周边新增快充站"
        )
    with col_param2:
        subsidy_rate = st.slider(
            "💰 电价补贴比例（降低价格）",
            min_value=0, max_value=50, value=20, step=5,
            help="补贴后价格 = 原价 × (1 - 补贴比例/100)"
        ) / 100.0

    # 模拟模型
    sim_data = base_data.copy()
    sim_util = sim_data['utilization'].values.copy()

    if new_fast_stations > 0:
        high_util_indices = sim_data.nlargest(new_fast_stations, 'utilization').index
        for idx in high_util_indices:
            sim_util[sim_data.index == idx] *= 0.85
            district = sim_data.loc[idx, 'district']
            district_mask = (sim_data['district'] == district) & (sim_data.index != idx)
            sim_util[district_mask] *= 0.95

    if subsidy_rate > 0:
        low_mask = sim_util < 0.4
        increase_factor = 1 + subsidy_rate * 0.3
        sim_util[low_mask] = np.minimum(0.9, sim_util[low_mask] * increase_factor)

    sim_util = np.minimum(0.95, sim_util)

    # 计算变化量
    util_change = sim_util - base_data['utilization'].values

    # 模拟后指标
    avg_util_sim = np.mean(sim_util)
    high_demand_ratio_sim = np.sum(sim_util > 0.7) / total_stations
    low_util_count_sim = np.sum(sim_util < 0.3)
    sim_power = (sim_util * sim_data['power'].values * 24 * 365 * 0.5).sum() / 1000
    co2_reduction_sim = sim_power * 0.6

    # 指标卡片
    st.subheader("📊 政策效果对比")
    col1, col2, col3 = st.columns(3)
    col1.metric("平均利用率", f"{avg_util_sim:.1%}", delta=f"{avg_util_sim - avg_util_base:+.1%}", delta_color="inverse")
    col2.metric("高需求站点占比", f"{high_demand_ratio_sim:.1%}", delta=f"{(high_demand_ratio_sim - high_demand_ratio_base):+.1%}", delta_color="inverse")
    col3.metric("年碳减排量", f"{co2_reduction_sim:.0f} 吨", delta=f"{co2_reduction_sim - co2_reduction_base:+.0f} 吨")
    st.metric("低利用率站点 (<30%)", f"{low_util_count_sim} 个", delta=f"{low_util_count_sim - np.sum(sim_data['utilization'] < 0.3):+d} 个", delta_color="inverse")

    # ========== 直接展示利用率变化地图 ==========
    st.subheader("🗺️ 利用率变化地图（红色↑上升，蓝色↓下降）")

    # 构建变化地图
    change_display = display_data.copy()
    # 为 display_data 的每个站点计算变化量（通过索引匹配）
    change_series = pd.Series(util_change, index=sim_data.index)
    change_display['change'] = change_display.index.map(lambda idx: change_series.get(idx, 0))
    change_display['change'] = change_display['change'].fillna(0)

    # 创建 folium 地图
    center_lat = change_display['lat'].mean()
    center_lon = change_display['lon'].mean()
    tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m_change = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=tiles, attr='高德地图')

    for _, row in change_display.iterrows():
        change_val = row['change']
        if change_val > 0.01:
            color = '#ff4d4d'  # 红色
            fill_color = '#ff4d4d'
        elif change_val < -0.01:
            color = '#4d4dff'  # 蓝色
            fill_color = '#4d4dff'
        else:
            color = '#aaaaaa'
            fill_color = '#aaaaaa'
        radius = max(5, min(25, abs(change_val) * 50))
        # 获取模拟后的利用率（当前 + 变化）
        new_util = row['utilization'] + change_val
        popup_text = f"""
        <b>{row['name']}</b><br>
        当前利用率: {row['utilization']:.1%}<br>
        模拟后利用率: {new_util:.1%}<br>
        变化: {change_val:+.1%}
        """
        folium.CircleMarker(
            [row['lat'], row['lon']],
            radius=radius,
            popup=popup_text,
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.7
        ).add_to(m_change)

    st_folium(m_change, width='100%', height=500)

    # 利用率分布直方图
    st.subheader("📊 利用率分布变化")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=sim_data['utilization'], name='当前', opacity=0.7, nbinsx=20))
    fig_hist.add_trace(go.Histogram(x=sim_util, name='模拟后', opacity=0.7, nbinsx=20))
    fig_hist.update_layout(barmode='overlay', title="利用率分布对比", xaxis_title="利用率", yaxis_title="站点数量")
    st.plotly_chart(fig_hist, use_container_width=True)

    st.caption("💡 模型基于简化假设：新建快充站分流高需求区域 15% 需求，电价补贴提升低利用率站点需求 0.3×补贴比例。")


def render_satisfaction_simple():
    """大屏轮播模式下的满意度分析精简版（仅地图+核心指标）"""
    st.subheader("😊 用户满意度分析")

    # 计算满意度（与完整版相同）
    max_price = filtered_data['price'].max()
    if max_price == 0:
        max_price = 1
    filtered_data_local = filtered_data.copy()
    filtered_data_local['price_coef'] = filtered_data_local['price'] / max_price
    filtered_data_local['satisfaction'] = (1 - filtered_data_local['utilization'] * 0.3
                                            - filtered_data_local['price_coef'] * 0.4
                                            + (filtered_data_local['available_slots'] / 10) * 0.3)
    filtered_data_local['satisfaction'] = filtered_data_local['satisfaction'].clip(0, 1) * 100

    avg_satisfaction = filtered_data_local['satisfaction'].mean()
    high_sat_count = len(filtered_data_local[filtered_data_local['satisfaction'] > 80])
    low_sat_count = len(filtered_data_local[filtered_data_local['satisfaction'] < 60])

    # 三指标卡片
    col1, col2, col3 = st.columns(3)
    col1.metric("综合满意度", f"{avg_satisfaction:.1f} 分")
    col2.metric("高满意度站点 (>80分)", high_sat_count)
    col3.metric("低满意度站点 (<60分)", low_sat_count)

    # 满意度分布地图（仅展示，不带表格和散点图）
    center_lat_sat = display_data['lat'].mean()
    center_lon_sat = display_data['lon'].mean()
    tiles_sat = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m_sat = folium.Map(location=[center_lat_sat, center_lon_sat], zoom_start=11, tiles=tiles_sat, attr='高德地图')

    display_data_with_sat = display_data.copy()
    sat_dict = filtered_data_local.set_index(display_data.index)['satisfaction'].to_dict()
    display_data_with_sat['satisfaction'] = display_data_with_sat.index.map(lambda idx: sat_dict.get(idx, 50))

    for _, row in display_data_with_sat.iterrows():
        sat_score = row['satisfaction']
        if sat_score >= 80:
            color = 'green'
        elif sat_score >= 60:
            color = 'orange'
        else:
            color = 'red'
        folium.CircleMarker(
            [row['lat'], row['lon']],
            radius=8,
            popup=get_popup_html(row),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            tooltip=f"{row['name']}: {sat_score:.1f}分"
        ).add_to(m_sat)

    st_folium(m_sat, width='100%', height=500)
    st.caption("绿色=高满意度，红色=低满意度。悬停查看详情。")


def render_policy_simulator_simple():
    """大屏轮播模式下的政策模拟器精简版（保留地图+滑动条+指标卡）"""
    st.subheader("📈 政策模拟器 · 参数调整与效果预测")

    st.markdown("调整下方参数，系统将模拟政策对充电桩利用率的影响。")

    # 当前基准数据（用于模拟计算）
    base_data = filtered_data.copy()
    avg_util_base = base_data['utilization'].mean()
    total_power_base = (base_data['utilization'] * base_data['power'] * 24 * 365 * 0.5).sum() / 1000
    co2_base = total_power_base * 0.6

    # 参数控件（滑动条）
    col_param1, col_param2 = st.columns(2)
    with col_param1:
        new_fast_stations = st.slider(
            "🚀 新建快充站数量",
            min_value=0, max_value=30, value=5, step=1,
            key="policy_slider_simple"
        )
    with col_param2:
        subsidy_rate = st.slider(
            "💰 电价补贴比例",
            min_value=0, max_value=50, value=20, step=5,
            key="subsidy_slider_simple"
        ) / 100.0

    # 模拟计算（与完整版一致）
    sim_util = base_data['utilization'].values.copy()
    if new_fast_stations > 0:
        high_indices = base_data.nlargest(new_fast_stations, 'utilization').index
        for idx in high_indices:
            sim_util[base_data.index == idx] *= 0.85
            district = base_data.loc[idx, 'district']
            district_mask = (base_data['district'] == district) & (base_data.index != idx)
            sim_util[district_mask] *= 0.95
    if subsidy_rate > 0:
        low_mask = sim_util < 0.4
        sim_util[low_mask] = np.minimum(0.9, sim_util[low_mask] * (1 + subsidy_rate * 0.3))
    sim_util = np.minimum(0.95, sim_util)

    avg_util_sim = np.mean(sim_util)
    sim_power = (sim_util * base_data['power'].values * 24 * 365 * 0.5).sum() / 1000
    co2_sim = sim_power * 0.6

    # ========== 利用率变化地图（保留） ==========
    st.subheader("🗺️ 利用率变化地图（红色↑上升，蓝色↓下降）")

    # 计算变化量
    util_change = sim_util - base_data['utilization'].values

    # 构建变化地图（使用 display_data 加速）
    change_display = display_data.copy()
    change_series = pd.Series(util_change, index=base_data.index)
    change_display['change'] = change_display.index.map(lambda idx: change_series.get(idx, 0))
    change_display['change'] = change_display['change'].fillna(0)

    center_lat = change_display['lat'].mean()
    center_lon = change_display['lon'].mean()
    tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}'
    m_change = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=tiles, attr='高德地图')

    for _, row in change_display.iterrows():
        change_val = row['change']
        if change_val > 0.01:
            color = '#ff4d4d'
            fill_color = '#ff4d4d'
        elif change_val < -0.01:
            color = '#4d4dff'
            fill_color = '#4d4dff'
        else:
            color = '#aaaaaa'
            fill_color = '#aaaaaa'
        radius = max(5, min(25, abs(change_val) * 50))
        new_util = row['utilization'] + change_val
        popup_text = f"""
        <b>{row['name']}</b><br>
        当前利用率: {row['utilization']:.1%}<br>
        模拟后利用率: {new_util:.1%}<br>
        变化: {change_val:+.1%}
        """
        folium.CircleMarker(
            [row['lat'], row['lon']],
            radius=radius,
            popup=popup_text,
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.7
        ).add_to(m_change)

    st_folium(m_change, width='100%', height=500)

    # ========== 简洁指标卡片 ==========
    st.subheader("📈 模拟分析结论")
    util_change_abs = avg_util_sim - avg_util_base
    co2_change = co2_sim - co2_base
    col_a, col_b = st.columns(2)
    col_a.metric("平均利用率变化", f"{util_change_abs:+.1%}")
    col_b.metric("碳减排量变化", f"{co2_change:+.0f} 吨")
    st.caption("💡 模型假设：新建快充站分流高需求区域15%需求，电价补贴提升低利用率站点需求30%×补贴比例。")


def render_emission_simple():
    """大屏轮播模式下的碳排放估算（当前数据）"""
    st.subheader("🌿 碳排放减排估算")
    # 计算当前年充电量和碳减排
    total_power = (filtered_data['utilization'] * filtered_data['power'] * 24 * 365 * 0.5).sum() / 1000  # 万度
    co2_reduction = total_power * 0.6  # 吨
    tree_equivalent = co2_reduction / 21.77

    col1, col2, col3 = st.columns(3)
    col1.metric("年充电量", f"{total_power:.1f} 万度")
    col2.metric("年碳减排", f"{co2_reduction:.0f} 吨 CO₂")
    col3.metric("相当于植树", f"{tree_equivalent:.0f} 棵")

    # 各区域碳减排柱状图
    region_emission = filtered_data.groupby('district').apply(
        lambda g: (g['utilization'] * g['power'] * 24 * 365 * 0.5).sum() / 1000 * 0.6
    ).reset_index(name='碳减排(吨)')
    region_emission = region_emission[region_emission['district'] != '其他区域']
    region_emission = region_emission.sort_values('碳减排(吨)', ascending=False)
    fig_co2 = px.bar(region_emission, x='district', y='碳减排(吨)',
                     title="各区域年碳减排量", color='碳减排(吨)',
                     color_continuous_scale='Greens')
    fig_co2.update_layout(
        autosize=True,
        margin=dict(l=60, r=60, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'), tickangle=-45),
        yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'))
    )
    st.plotly_chart(fig_co2, use_container_width=True)
    st.caption("💡 碳减排计算依据：每度电替代燃油减排0.6 kg CO₂，每棵树年吸收21.77 kg CO₂。")


# ================== 在侧边栏末尾添加导出按钮（确保数据已加载） ==================
with st.sidebar:
    st.subheader("📄 导出报告")
    # 直接使用 st.download_button，点击后立即生成并下载
    st.download_button(
        label="📊 导出当前视图报告 (Excel)",
        data=export_report(view_mode, filtered_data, display_data, predictions),
        file_name=f"report_{view_mode.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# ================== 主内容 ==================
if enable_carousel:
    # 初始化轮播状态
    if 'carousel_index' not in st.session_state:
        st.session_state.carousel_index = 0
    if 'last_switch_time' not in st.session_state:
        st.session_state.last_switch_time = time.time()
    if 'pause_carousel' not in st.session_state:
        st.session_state.pause_carousel = False

    views = ["🔥 热力图", "🗺️ 分布图", "📊 覆盖分析", "😊 满意度分析", "🔮 预测分析", "🌿 碳排放估算", "💡 优化建议",
             "💼 招商引资", "📈 政策模拟器"]
    current_view = views[st.session_state.carousel_index]

    # 自动切换逻辑
    current_time = time.time()
    if not st.session_state.pause_carousel and current_time - st.session_state.last_switch_time >= auto_play_speed:
        st.session_state.carousel_index = (st.session_state.carousel_index + 1) % len(views)
        st.session_state.last_switch_time = current_time
        st.rerun()

    # 显示标题（只保留主标题，不显示当前视图）
    st.title("🏛️ 政府/运营商端 · 充电桩智能监管与规划系统")

    # ========== 根据当前视图渲染主要内容 ==========
    if current_view == "🔥 热力图":
        st.subheader("🔥 充电需求热力图")
        m_heat = create_heatmap_fig(display_data)
        st_folium(m_heat, width='100%', height=500)
        avg_util = display_data['utilization'].mean()
        high_count = len(display_data[display_data['utilization'] > 0.7])
        low_count = len(display_data[display_data['utilization'] < 0.3])
        col1, col2, col3 = st.columns(3)
        col1.metric("平均利用率", f"{avg_util:.1%}")
        col2.metric("高需求站点", high_count)
        col3.metric("低需求站点", low_count)

    elif current_view == "🗺️ 分布图":
        st.subheader("🗺️ 充电设施分布图")
        m_dist = create_distribution_fig(display_data)
        st_folium(m_dist, width='100%', height=500)
        # 图例
        with st.container():
            st.markdown("""
            <div style="display: flex; justify-content: center; gap: 30px; 
                        padding: 4px 0 4px 0;
                        margin-bottom: 20px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: #FF4136; border-radius: 50%; margin-right: 8px;"></div>
                    <span style="color: white;">快充站</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: #0074D9; border-radius: 50%; margin-right: 8px;"></div>
                    <span style="color: white;">慢充站</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="color: white;">⚡ 图标大小 = 利用率</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 快充/慢充站点数量 + 平均利用率（与单视图一致）
        fast_count = len(display_data[display_data['type'] == '快充'])
        slow_count = len(display_data[display_data['type'] == '慢充'])
        fast_avg_util = display_data[display_data['type'] == '快充']['utilization'].mean() if fast_count > 0 else 0
        slow_avg_util = display_data[display_data['type'] == '慢充']['utilization'].mean() if slow_count > 0 else 0

        col1, col2 = st.columns(2)
        col1.metric("快充站数量", fast_count, delta=f"{fast_avg_util:.1%} 平均利用率")
        col2.metric("慢充站数量", slow_count, delta=f"{slow_avg_util:.1%} 平均利用率")

    elif current_view == "📊 覆盖分析":
        st.subheader("📊 服务覆盖范围分析")
        m_cov = create_coverage_map_fig(display_data)
        st_folium(m_cov, width='100%', height=500)

        # 状态统计
        status_counts = filtered_data['status'].value_counts()

        # 三个指标卡片（在线/离线/维护中）
        st.subheader("📊 充电桩实时运行状态统计")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("在线", status_counts.get('在线', 0))
        col_s2.metric("离线", status_counts.get('离线', 0))
        col_s3.metric("维护中", status_counts.get('维护中', 0))

    elif current_view == "😊 满意度分析":
        render_satisfaction_simple()

    elif current_view == "🔮 预测分析":
        st.subheader("🔮 需求预测（默认参数）")
        growth_rate = 1.2
        seasonal_factor = 1.1
        months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
        hist_demand = [100, 120, 150, 180, 210, 240]
        pred_demand = [int(240 * growth_rate * seasonal_factor), int(270 * growth_rate),
                       int(300 * growth_rate), int(330 * growth_rate),
                       int(360 * growth_rate * seasonal_factor), int(390 * growth_rate)]
        all_months = months[:6] + months[6:]
        all_demand = hist_demand + pred_demand
        colors = ['#2ECC40'] * 6 + ['#FF4136'] * 6
        fig_combo = go.Figure()
        fig_combo.add_trace(go.Bar(x=all_months, y=all_demand, marker_color=colors, text=all_demand, textposition='outside'))
        fig_combo.add_trace(go.Scatter(x=months[5:], y=[hist_demand[-1]] + pred_demand, mode='lines+markers', name='趋势线', line=dict(color='black', width=2, dash='dash')))
        fig_combo.update_layout(title="月度需求预测", xaxis_title="月份", yaxis_title="充电需求量 (相对值)", autosize=True, margin=dict(l=60, r=60, t=40, b=20))
        st.plotly_chart(fig_combo, use_container_width=True, config={'responsive': True})
    elif current_view == "🌿 碳排放估算":
        render_emission_simple()

    elif current_view == "💡 优化建议":
        render_optimization_simple()  # 精简版（含地图）

    elif current_view == "💼 招商引资":
        # 轮播模式下的招商引资简化版
        st.subheader("💼 招商引资 - 投资潜力")
        col1, col2 = st.columns([2, 1])
        with col1:
            m_potential = create_heatmap_fig(display_data)
            st_folium(m_potential, width='100%', height=500)
        with col2:
            st.markdown("**推荐投资区域**")
            top_regions = filtered_data.groupby('district')['utilization'].mean().reset_index()
            top_regions = top_regions.sort_values('utilization', ascending=False).head(5)
            top_regions['utilization'] = top_regions['utilization'].map(lambda x: f"{x:.1%}")
            st.markdown(top_regions.to_html(index=False, columns=["district", "utilization"],
                                            header=["区域", "平均利用率"], classes='custom-table', escape=False),
                        unsafe_allow_html=True)

    elif current_view == "📈 政策模拟器":
        render_policy_simulator_simple()


    # ========== 轮播控制按钮（移至内容下方，数据来源上方） ==========
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.session_state.pause_carousel:
            st.markdown("⏸️ **已暂停**")
        else:
            st.markdown("▶️ **播放中**")
    with col2:
        if st.button("◀ 上一个"):
            st.session_state.carousel_index = (st.session_state.carousel_index - 1) % len(views)
            st.session_state.last_switch_time = time.time()
            st.rerun()
    with col3:
        btn_label = "▶️ 继续" if st.session_state.pause_carousel else "⏸️ 暂停"
        if st.button(btn_label):
            st.session_state.pause_carousel = not st.session_state.pause_carousel
            if not st.session_state.pause_carousel:
                st.session_state.last_switch_time = time.time()
            st.rerun()
    with col4:
        if st.button("下一个 ▶"):
            st.session_state.carousel_index = (st.session_state.carousel_index + 1) % len(views)
            st.session_state.last_switch_time = time.time()
            st.rerun()

else:
    # 单视图模式
    st.title("🏛️ 政府/运营商端 · 充电桩智能监管与规划系统")

    if view_mode == "🔥 热力图":
        render_heatmap()
    elif view_mode == "🗺️ 分布图":
        render_distribution()
    elif view_mode == "📊 覆盖分析":
        render_coverage()
    elif view_mode == "😊 满意度分析":
        render_satisfaction()
    elif view_mode == "🔮 预测分析":
        render_prediction()
        # ========== 新增：碳排放估算（融合到预测分析） ==========
        st.subheader("🌿 碳排放减排估算（基于预测需求）")

        # 计算当前年充电量（万度）和碳减排（吨）
        total_power_current = (filtered_data['utilization'] * filtered_data['power'] * 24 * 365 * 0.5).sum() / 1000  # 万度
        co2_reduction_current = total_power_current * 0.6  # 每度电减排0.6 kg CO2，单位：吨
        tree_equivalent_current = co2_reduction_current / 21.77  # 每吨CO2约需21.77棵树吸收一年

        # 基于预测利用率（pred_full）计算未来年减排量
        pred_full = get_predictions(filtered_data)
        filtered_data_with_pred = filtered_data.copy()
        filtered_data_with_pred['pred_util'] = pred_full
        total_power_future = (filtered_data_with_pred['pred_util'] * filtered_data_with_pred['power'] * 24 * 365 * 0.5).sum() / 1000
        co2_reduction_future = total_power_future * 0.6
        tree_equivalent_future = co2_reduction_future / 21.77

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("当前年充电量", f"{total_power_current:.1f} 万度")
        col_b.metric("当前年碳减排", f"{co2_reduction_current:.0f} 吨 CO₂")
        col_c.metric("相当于植树", f"{tree_equivalent_current:.0f} 棵")

        col_d, col_e, col_f = st.columns(3)
        col_d.metric("预测年充电量", f"{total_power_future:.1f} 万度", delta=f"{total_power_future - total_power_current:.1f} 万度")
        col_e.metric("预测年碳减排", f"{co2_reduction_future:.0f} 吨 CO₂", delta=f"{co2_reduction_future - co2_reduction_current:.0f} 吨")
        col_f.metric("预测相当于植树", f"{tree_equivalent_future:.0f} 棵", delta=f"{tree_equivalent_future - tree_equivalent_current:.0f} 棵")

        # 可选：各区域碳减排对比（基于当前数据）
        st.markdown("#### 📊 各区域碳减排贡献（当前）")
        region_emission = filtered_data.groupby('district').apply(
            lambda g: (g['utilization'] * g['power'] * 24 * 365 * 0.5).sum() / 1000 * 0.6
        ).reset_index(name='碳减排(吨)')
        fig_co2 = px.bar(region_emission, x='district', y='碳减排(吨)',
                         title="各区域年碳减排量", color='碳减排(吨)',
                         color_continuous_scale='Greens')
        st.plotly_chart(fig_co2, use_container_width=True)

        st.caption("💡 碳减排计算依据：每度电替代燃油减排0.6 kg CO₂，每棵树年吸收21.77 kg CO₂。预测基于需求增长模型。")
    elif view_mode == "💡 优化建议":
        render_optimization()
    elif view_mode == "💼 招商引资":
        render_investment()
    elif view_mode == "📈 政策模拟器":
        render_policy_simulator()

# 底部数据来源说明
st.caption("数据更新时间：2026-03-19 | 数据来源：高德地图API + 基于真实分布模拟（利用率、空闲插口为模拟值）")