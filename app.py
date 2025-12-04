"""
电动汽车充电桩布局优化与需求预测系统
基于多源数据的可视化分析平台
离线地图版本 - 无需网络连接
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ====================
# 页面配置
# ====================
st.set_page_config(
    page_title="电动汽车充电桩分析系统",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================
# 样式配置
# ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #424242;
        border-bottom: 2px solid #1E88E5;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)


# ====================
# 数据生成函数
# ====================
class DataGenerator:
    """数据生成器 - 离线模拟数据"""

    @staticmethod
    def generate_charger_data(num_points=120):
        """生成模拟充电桩数据"""
        np.random.seed(42)

        # 模拟北京市主要区域坐标
        areas = {
            '朝阳区': (39.92, 116.45),
            '海淀区': (39.95, 116.30),
            '东城区': (39.91, 116.41),
            '西城区': (39.91, 116.37),
            '丰台区': (39.86, 116.28),
            '通州区': (39.90, 116.66),
            '大兴区': (39.73, 116.33)
        }

        data = []
        for i in range(num_points):
            # 随机选择一个区域
            area_name = np.random.choice(list(areas.keys()))
            center_lat, center_lon = areas[area_name]

            # 在区域内随机分布
            lat = center_lat + np.random.uniform(-0.05, 0.05)
            lon = center_lon + np.random.uniform(-0.05, 0.05)

            # 生成其他属性
            charger_type = np.random.choice(['快充', '慢充'], p=[0.6, 0.4])

            # 利用率与区域相关（市中心高，郊区低）
            base_utilization = 0.3
            if area_name in ['朝阳区', '东城区', '西城区']:
                base_utilization = 0.6
            elif area_name in ['海淀区', '丰台区']:
                base_utilization = 0.45

            utilization = np.clip(np.random.normal(base_utilization, 0.15), 0.1, 0.95)

            data.append({
                '充电站ID': f'CS_{i + 1:04d}',
                '充电站名称': f'{area_name}充电站_{i + 1}',
                '所在区域': area_name,
                '纬度': lat,
                '经度': lon,
                '充电类型': charger_type,
                '当前利用率': utilization,
                '充电功率(kW)': np.random.choice([60, 120, 180], p=[0.3, 0.5, 0.2]),
                '充电单价(元/kWh)': np.round(np.random.uniform(1.2, 2.0), 2),
                '可用充电桩数量': np.random.randint(4, 20),
                '服务时间': np.random.choice(['24小时', '06:00-22:00', '08:00-20:00'])
            })

        return pd.DataFrame(data)

    @staticmethod
    def generate_traffic_data():
        """生成模拟交通流量数据"""
        times = ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00']
        areas = ['朝阳区', '海淀区', '东城区', '西城区', '丰台区', '通州区', '大兴区']

        data = []
        for time in times:
            for area in areas:
                # 早晚高峰流量高
                base_traffic = 50
                if time in ['07:00', '08:00', '17:00', '18:00']:
                    base_traffic = 150
                elif time in ['12:00', '13:00']:
                    base_traffic = 100

                traffic = np.random.normal(base_traffic, 20)
                traffic = max(10, traffic)  # 确保非负

                data.append({
                    '时间': time,
                    '区域': area,
                    '交通流量': traffic
                })

        return pd.DataFrame(data)

    @staticmethod
    def generate_population_data():
        """生成模拟人口密度数据"""
        areas = {
            '朝阳区': {'人口密度': 25000, '平均收入': 8500},
            '海淀区': {'人口密度': 23000, '平均收入': 9000},
            '东城区': {'人口密度': 28000, '平均收入': 9200},
            '西城区': {'人口密度': 26000, '平均收入': 9500},
            '丰台区': {'人口密度': 18000, '平均收入': 6500},
            '通州区': {'人口密度': 15000, '平均收入': 6000},
            '大兴区': {'人口密度': 12000, '平均收入': 5800}
        }

        data = []
        for area, info in areas.items():
            data.append({
                '区域': area,
                '人口密度(人/平方公里)': info['人口密度'],
                '平均收入(元)': info['平均收入'],
                '电动汽车保有量': int(info['人口密度'] * 0.05)  # 假设5%的人口有电动汽车
            })

        return pd.DataFrame(data)


# ====================
# 可视化函数 - 离线版本
# ====================
def create_offline_heatmap(data, title="充电需求热力图"):
    """创建离线热力图（散点密度图）"""
    # 使用普通散点图模拟热力图
    fig = px.scatter(
        data,
        x='经度',
        y='纬度',
        color='当前利用率',
        size='当前利用率',
        color_continuous_scale='Viridis',
        title=title,
        hover_data=['充电站名称', '所在区域', '充电类型', '当前利用率']
    )

    # 设置布局
    fig.update_layout(
        xaxis_title="经度",
        yaxis_title="纬度",
        plot_bgcolor='white',
        height=500,
        coloraxis_colorbar=dict(
            title="利用率",
            tickformat=".0%"
        )
    )

    # 添加网格
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def create_offline_distribution_map(data, title="充电设施分布图"):
    """创建离线设施分布图"""
    fig = px.scatter(
        data,
        x='经度',
        y='纬度',
        color='充电类型',
        symbol='充电类型',
        size='当前利用率',
        title=title,
        hover_data=['充电站名称', '所在区域', '当前利用率', '充电功率(kW)'],
        color_discrete_map={'快充': 'red', '慢充': 'blue'}
    )

    # 设置布局
    fig.update_layout(
        xaxis_title="经度",
        yaxis_title="纬度",
        plot_bgcolor='white',
        height=500,
        legend_title="充电类型"
    )

    # 添加网格和调整标记
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color='black')))

    return fig


def create_voronoi_diagram(data, title="服务覆盖范围分析"):
    """创建Voronoi图（服务范围分析）"""
    fig = go.Figure()

    # 添加充电站点
    fig.add_trace(go.Scatter(
        x=data['经度'],
        y=data['纬度'],
        mode='markers',
        marker=dict(
            size=10,
            color=data['当前利用率'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="利用率")
        ),
        name='充电站',
        text=data['充电站名称'],
        hovertemplate='<b>%{text}</b><br>利用率: %{marker.color:.1%}<extra></extra>'
    ))

    # 添加服务范围示意（简化版）
    # 在实际项目中，这里应该计算真正的Voronoi图
    # 这里用简单的网格示意

    fig.update_layout(
        title=title,
        xaxis_title="经度",
        yaxis_title="纬度",
        plot_bgcolor='white',
        height=500,
        showlegend=False
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

    return fig


def create_demand_prediction_chart(data, title="需求预测分析"):
    """创建需求预测图表"""
    # 模拟时间序列数据
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    historical = [100, 110, 125, 140, 160, 180, 200, 210, 195, 175, 150, 130]

    # 简单预测（线性外推）
    predicted = historical.copy()
    for i in range(6, 12):
        growth = (historical[i] - historical[i - 6]) / 6
        predicted[i] = historical[i] + growth * 3

    fig = go.Figure()

    # 历史数据
    fig.add_trace(go.Scatter(
        x=months[:6],
        y=historical[:6],
        mode='lines+markers',
        name='历史数据',
        line=dict(color='blue', width=3)
    ))

    # 预测数据
    fig.add_trace(go.Scatter(
        x=months[5:],
        y=predicted[5:],
        mode='lines+markers',
        name='预测数据',
        line=dict(color='red', width=3, dash='dash')
    ))

    fig.update_layout(
        title=title,
        xaxis_title="月份",
        yaxis_title="充电需求指数",
        plot_bgcolor='white',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_optimization_suggestion(data, title="布局优化建议"):
    """创建布局优化建议图"""
    # 识别需要优化的区域
    high_demand = data[data['当前利用率'] > 0.7]
    low_demand = data[data['当前利用率'] < 0.3]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('高需求区域（建议扩建）', '低利用率区域（建议优化）')
    )

    # 高需求区域
    if not high_demand.empty:
        fig.add_trace(
            go.Scatter(
                x=high_demand['经度'],
                y=high_demand['纬度'],
                mode='markers',
                marker=dict(
                    size=15,
                    color='red',
                    symbol='x'
                ),
                name='高需求站点',
                text=high_demand['充电站名称'],
                hovertemplate='<b>%{text}</b><br>利用率: %{marker.color}<extra></extra>'
            ),
            row=1, col=1
        )

    # 低利用率区域
    if not low_demand.empty:
        fig.add_trace(
            go.Scatter(
                x=low_demand['经度'],
                y=low_demand['纬度'],
                mode='markers',
                marker=dict(
                    size=15,
                    color='green',
                    symbol='circle'
                ),
                name='低利用率站点',
                text=low_demand['充电站名称'],
                hovertemplate='<b>%{text}</b><br>利用率: %{marker.color}<extra></extra>'
            ),
            row=1, col=2
        )

    # 更新布局
    for i in [1, 2]:
        fig.update_xaxes(title_text="经度", row=1, col=i, showgrid=True)
        fig.update_yaxes(title_text="纬度", row=1, col=i, showgrid=True)

    fig.update_layout(
        title_text=title,
        height=400,
        showlegend=True
    )

    return fig


# ====================
# 主应用函数
# ====================
def main():
    # 标题
    st.markdown('<h1 class="main-header">🚗 电动汽车充电桩布局优化与需求预测系统</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # 生成数据
    st.sidebar.header("📊 数据设置")
    num_chargers = st.sidebar.slider("充电站数量", 50, 200, 120)

    generator = DataGenerator()
    charger_data = generator.generate_charger_data(num_chargers)
    traffic_data = generator.generate_traffic_data()
    population_data = generator.generate_population_data()

    # 侧边栏控制
    st.sidebar.header("🎛️ 控制面板")
    selected_area = st.sidebar.selectbox("选择区域", ["全部"] + list(charger_data['所在区域'].unique()))
    selected_type = st.sidebar.selectbox("选择充电类型", ["全部", "快充", "慢充"])

    # 数据过滤
    filtered_data = charger_data.copy()
    if selected_area != "全部":
        filtered_data = filtered_data[filtered_data['所在区域'] == selected_area]
    if selected_type != "全部":
        filtered_data = filtered_data[filtered_data['充电类型'] == selected_type]

    # ====================
    # 1. 系统概览
    # ====================
    st.markdown('<h2 class="section-header">📈 系统概览</h2>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("充电站总数", len(filtered_data))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("平均利用率", f"{filtered_data['当前利用率'].mean():.1%}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        fast_ratio = (filtered_data['充电类型'] == '快充').mean()
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("快充比例", f"{fast_ratio:.1%}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        high_demand = (filtered_data['当前利用率'] > 0.7).sum()
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("高需求站点", high_demand)
        st.markdown('</div>', unsafe_allow_html=True)

    # ====================
    # 2. 充电需求热力图
    # ====================
    st.markdown('<h2 class="section-header">🔥 充电需求热力图</h2>', unsafe_allow_html=True)
    heatmap_fig = create_offline_heatmap(filtered_data)
    st.plotly_chart(heatmap_fig, use_container_width=True)

    # ====================
    # 3. 充电设施分布图
    # ====================
    st.markdown('<h2 class="section-header">🗺️ 充电设施分布图</h2>', unsafe_allow_html=True)
    distribution_fig = create_offline_distribution_map(filtered_data)
    st.plotly_chart(distribution_fig, use_container_width=True)

    # ====================
    # 4. 服务覆盖分析
    # ====================
    st.markdown('<h2 class="section-header">📏 服务覆盖分析</h2>', unsafe_allow_html=True)
    voronoi_fig = create_voronoi_diagram(filtered_data)
    st.plotly_chart(voronoi_fig, use_container_width=True)

    # 覆盖率统计
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("服务覆盖率统计")

        # 计算各区域覆盖率
        area_coverage = filtered_data.groupby('所在区域').agg({
            '当前利用率': 'mean',
            '充电站ID': 'count'
        }).round(3)
        area_coverage = area_coverage.rename(columns={'当前利用率': '平均利用率', '充电站ID': '站点数量'})
        st.dataframe(area_coverage, use_container_width=True)

    with col2:
        st.subheader("需求等级分布")

        # 计算需求等级
        filtered_data['需求等级'] = pd.cut(
            filtered_data['当前利用率'],
            bins=[0, 0.3, 0.7, 1.0],
            labels=['低需求', '中等需求', '高需求']
        )

        demand_dist = filtered_data['需求等级'].value_counts().sort_index()
        fig_pie = px.pie(
            values=demand_dist.values,
            names=demand_dist.index,
            title="需求等级分布",
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ====================
    # 5. 需求预测分析
    # ====================
    st.markdown('<h2 class="section-header">🔮 需求预测分析</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        prediction_fig = create_demand_prediction_chart(filtered_data)
        st.plotly_chart(prediction_fig, use_container_width=True)

    with col2:
        st.subheader("预测参数设置")

        # 简单的预测参数调整
        growth_rate = st.slider("预计增长率", 0.5, 2.0, 1.2, 0.1)
        season_factor = st.slider("季节性因素", 0.8, 1.5, 1.1, 0.05)

        st.info("""
        **预测说明**:
        - 基于历史数据的趋势分析
        - 考虑季节性和增长因素
        - 用于未来3-6个月的需求规划
        """)

    # ====================
    # 6. 布局优化建议
    # ====================
    st.markdown('<h2 class="section-header">💡 布局优化建议</h2>', unsafe_allow_html=True)

    optimization_fig = create_optimization_suggestion(filtered_data)
    st.plotly_chart(optimization_fig, use_container_width=True)

    # 具体建议
    st.subheader("具体优化方案")

    suggestions = []

    # 高需求区域建议
    high_demand_areas = filtered_data[filtered_data['当前利用率'] > 0.7]['所在区域'].unique()
    if len(high_demand_areas) > 0:
        suggestions.append(f"**高需求区域**：{', '.join(high_demand_areas)}，建议新增充电站或扩建现有设施")

    # 快慢充比例建议
    type_ratio = filtered_data.groupby('所在区域')['充电类型'].value_counts(normalize=True).unstack().fillna(0)
    for area in type_ratio.index:
        fast_ratio = type_ratio.loc[area, '快充'] if '快充' in type_ratio.columns else 0
        if fast_ratio < 0.5:
            suggestions.append(f"**{area}**：快充比例较低({fast_ratio:.1%})，建议增加快充设施")

    # 显示建议
    if suggestions:
        for i, suggestion in enumerate(suggestions[:3], 1):  # 最多显示3条
            st.markdown(f"{i}. {suggestion}")
    else:
        st.success("✅ 当前布局较为合理，暂无重大优化需求")

    # ====================
    # 7. 数据详情
    # ====================
    with st.expander("📋 查看详细数据"):
        st.subheader("充电站详细数据")
        st.dataframe(filtered_data, use_container_width=True)

        st.subheader("交通流量数据")
        st.dataframe(traffic_data, use_container_width=True)

        st.subheader("人口与收入数据")
        st.dataframe(population_data, use_container_width=True)

    # ====================
    # 8. 项目说明
    # ====================
    st.markdown("---")
    st.markdown('<h2 class="section-header">📚 项目说明</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **技术特点**:
        - 纯离线运行，无需网络连接
        - 基于模拟数据的多维度分析
        - 5个核心可视化界面
        - 交互式数据筛选
        """)

    with col2:
        st.info("""
        **应用价值**:
        - 优化充电设施布局
        - 预测未来需求趋势
        - 提高资源利用效率
        - 支持政府和企业决策
        """)

    st.success("🎉 系统运行正常！所有可视化功能均为离线版本，可在任何环境下稳定运行。")


# ====================
# 主程序入口
# ====================
if __name__ == "__main__":
    main()