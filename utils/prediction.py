import numpy as np
import pandas as pd


def generate_trend_prediction():
    """生成趋势预测数据"""
    months = ['1月', '2月', '3月', '4月', '5月', '6月']
    historical = [100, 120, 150, 180, 210, 240]
    predicted = [240, 270, 300, 330, 360, 390]

    return months, historical, predicted


def calculate_coverage_metrics(data, utilization_col='utilization'):
    """计算覆盖指标"""
    metrics = {
        "高覆盖率(>70%)": (data[utilization_col] > 0.7).sum(),
        "中等覆盖率(30%-70%)": ((data[utilization_col] >= 0.3) & (data[utilization_col] <= 0.7)).sum(),
        "低覆盖率(<30%)": (data[utilization_col] < 0.3).sum()
    }
    return metrics