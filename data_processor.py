import pandas as pd
import numpy as np


class DataProcessor:
    def __init__(self):
        self.charger_data = None

    def load_charger_data(self):
        """加载充电桩数据"""
        if self.charger_data is None:
            self.generate_simulated_data()
        return self.charger_data

    def generate_simulated_data(self):
        """生成模拟充电桩数据"""
        np.random.seed(42)
        n_points = 150

        # 生成基础数据
        self.charger_data = pd.DataFrame({
            'id': range(n_points),
            'name': [f'充电站_{i:03d}' for i in range(n_points)],
            'lat': 39.8 + 0.3 * np.random.rand(n_points),
            'lon': 116.2 + 0.4 * np.random.rand(n_points),
            'type': np.random.choice(['快充', '慢充'], n_points, p=[0.6, 0.4]),
            'power': np.random.choice([60, 120, 180], n_points),
            'utilization': np.random.uniform(0.1, 0.95, n_points),
            'price': np.round(np.random.uniform(1.2, 2.0, n_points), 2)
        })

        # 创建热点区域
        self._create_hotspots()

        return self.charger_data

    def _create_hotspots(self):
        """创建需求热点区域"""
        hotspots = [
            (39.9, 116.4, 0.3),  # 市中心
            (39.85, 116.35, 0.2),  # 商业区
            (39.95, 116.45, 0.25)  # 交通枢纽
        ]

        for center_lat, center_lon, bonus in hotspots:
            mask = ((self.charger_data['lat'] - center_lat) ** 2 +
                    (self.charger_data['lon'] - center_lon) ** 2) < 0.01
            self.charger_data.loc[mask, 'utilization'] = np.clip(
                self.charger_data.loc[mask, 'utilization'] + bonus, 0.1, 0.95
            )

    def filter_data(self, data, selected_type):
        """根据类型过滤数据"""
        if selected_type == "全部":
            return data
        return data[data['type'] == selected_type]

    def simple_demand_prediction(self, data):
        """简单需求预测算法"""
        center_lat, center_lon = 39.9, 116.4

        predictions = []
        for _, row in data.iterrows():
            distance = np.sqrt((row['lat'] - center_lat) ** 2 + (row['lon'] - center_lon) ** 2)
            location_factor = max(0.1, 1 - distance * 2)
            predicted = row['utilization'] * 0.6 + location_factor * 0.4
            predictions.append(min(0.95, predicted))

        return predictions

    def simple_demand_prediction(self, data):
        """简单需求预测算法"""
        center_lat, center_lon = 39.9, 116.4

        predictions = []
        for _, row in data.iterrows():
            # 基于距离市中心的位置因子
            distance = np.sqrt((row['lat'] - center_lat) ** 2 + (row['lon'] - center_lon) ** 2)
            location_factor = max(0.1, 1 - distance * 2)

            # 结合当前利用率和位置因子
            predicted = row['utilization'] * 0.6 + location_factor * 0.4
            predictions.append(min(0.95, predicted))

        return predictions

    def moving_average_predict(self, data, window=3):
        """使用移动平均进行时间序列预测"""
        if len(data) < window:
            return data

        predictions = []
        for i in range(len(data)):
            if i < window:
                predictions.append(data[i])
            else:
                avg = np.mean(data[i - window:i])
                predictions.append(avg)

        return predictions

    def seasonal_pattern_predict(self, months, seasonal_factor=1.1):
        """简单的季节性模式预测"""
        seasonal_adjustments = {
            1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.0,
            6: 1.1, 7: 1.2, 8: 1.1, 9: 1.0, 10: 1.0,
            11: 0.9, 12: 0.9
        }

        predictions = []
        for month in months:
            if month in seasonal_adjustments:
                predictions.append(seasonal_adjustments[month] * seasonal_factor)
            else:
                predictions.append(1.0 * seasonal_factor)

        return predictions