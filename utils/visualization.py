import plotly.express as px
import plotly.graph_objects as go

def create_heatmap(data, lat_col='lat', lon_col='lon', value_col='utilization'):
    """创建热力图"""
    fig = px.density_mapbox(
        data,
        lat=lat_col,
        lon=lon_col,
        z=value_col,
        radius=20,
        zoom=10,
        mapbox_style="open-street-map",
        color_continuous_scale="Viridis"
    )
    return fig

def create_distribution_map(data, lat_col='lat', lon_col='lon', color_col='type', size_col='utilization'):
    """创建设施分布地图"""
    fig = px.scatter_mapbox(
        data,
        lat=lat_col,
        lon=lon_col,
        color=color_col,
        size=size_col,
        hover_name="name",
        color_discrete_map={"快充": "red", "慢充": "blue"},
        zoom=10,
        height=500
    )
    fig.update_layout(mapbox_style="open-street-map")
    return fig

def create_pie_chart(data, values, names, title):
    """创建饼图"""
    fig = px.pie(
        data,
        values=values,
        names=names,
        title=title
    )
    return fig

def create_histogram(data, x_col, title, nbins=20):
    """创建直方图"""
    fig = px.histogram(
        data,
        x=x_col,
        title=title,
        nbins=nbins
    )
    return fig