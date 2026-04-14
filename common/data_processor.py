import requests
import pandas as pd
import numpy as np
import sqlite3
import time
import os
import hashlib
from datetime import datetime, timedelta
import math

class DataProcessor:
    def __init__(self, use_real_data=False):
        # 高德 API 配置（请替换为自己的 Key）
        self.api_key = "a8c1a81e1c5f5f6ca9e024f59a69bf5e"
        self.secret_key = "1387378e512c6aacd3ffd79f40f656c7"
        self.cache_db = "charger_cache.db"
        self.db_path = self.cache_db
        self.cache_hours = 24
        self.use_real_data = use_real_data
        self._init_db()

    # ------------------ 数据库初始化 ------------------
    def _init_db(self):
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS charger_cache (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    address TEXT,
                    lat REAL,
                    lon REAL,
                    type TEXT,
                    power INTEGER,
                    utilization REAL,
                    price REAL,
                    available_slots INTEGER,
                    distance REAL,
                    adcode TEXT,
                    city TEXT,
                    brand TEXT,
                    cache_lat REAL,
                    cache_lon REAL,
                    cache_radius REAL,
                    cache_time TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"数据库初始化失败: {e}")

    # ------------------ 高德 API 请求 ------------------
    def _generate_sig(self, params):
        """生成高德 API 数字签名"""
        sorted_keys = sorted([k for k in params.keys() if k not in ('sig', 'key')])
        sign_str = ''
        for k in sorted_keys:
            sign_str += k + str(params[k])
        sign_str += self.secret_key
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def _haversine(self, lat1, lon1, lat2, lon2):
        """计算两点间距离（公里）"""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _extract_price(self, business):
        """从高德返回的 business 字段中提取电价"""
        try:
            if isinstance(business, dict) and 'charge_fee' in business:
                price_str = business['charge_fee']
                import re
                nums = re.findall(r'\d+\.?\d*', price_str)
                if nums:
                    return float(nums[0])
        except:
            pass
        return np.random.uniform(0.8, 2.2)

    def _simulate_utilization(self, distance, poi):
        """模拟充电桩利用率（基于距离和名称）"""
        base = max(0.1, 1 - distance / 20)
        noise = np.random.normal(0, 0.15)
        if '快充' in poi.get('name', ''):
            base += 0.1
        return min(0.95, max(0.1, base + noise))

    def _fetch_from_amap(self, user_lat, user_lon, radius_km):
        """调用高德周边搜索 API 获取充电桩数据"""
        if not self.api_key or self.api_key == "你的高德API Key":
            print("API Key 未配置，跳过API请求")
            return pd.DataFrame()

        url = "https://restapi.amap.com/v3/place/around"
        params = {
            'key': self.api_key,
            'location': f"{user_lon},{user_lat}",
            'keywords': '充电站',
            'types': '150900',
            'radius': radius_km * 1000,
            'offset': 25,
            'page': 1,
            'extensions': 'all'
        }
        params['sig'] = self._generate_sig(params)

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get('status') != '1':
                print(f"API返回错误: {data.get('info')}")
                return pd.DataFrame()

            pois = data.get('pois', [])
            if not pois:
                print("附近没有充电站")
                return pd.DataFrame()

            stations = []
            for poi in pois:
                loc = poi.get('location', '').split(',')
                if len(loc) != 2:
                    continue
                lon, lat = float(loc[0]), float(loc[1])
                distance = self._haversine(user_lat, user_lon, lat, lon)
                if distance > radius_km:
                    continue

                name = poi.get('name', '')
                charger_type = '快充' if ('快充' in name or '超充' in name) else '慢充'
                power = np.random.choice([120, 180]) if charger_type == '快充' else np.random.choice([60, 80])
                price = self._extract_price(poi.get('business', {}))
                utilization = self._simulate_utilization(distance, poi)
                available = np.random.randint(0, 8)

                stations.append({
                    'id': poi.get('id', ''),
                    'name': name,
                    'address': poi.get('address', ''),
                    'lat': lat,
                    'lon': lon,
                    'type': charger_type,
                    'power': power,
                    'utilization': round(utilization, 2),
                    'price': round(price, 2),
                    'available_slots': available,
                    'distance': round(distance, 2),
                    'adcode': poi.get('adcode', ''),
                    'city': poi.get('cityname', ''),
                    'brand': poi.get('brand', '')
                })
            return pd.DataFrame(stations)
        except Exception as e:
            print(f"API请求异常: {e}")
            return pd.DataFrame()

    # ------------------ 缓存操作 ------------------
    def _save_to_cache(self, df, cache_lat, cache_lon, cache_radius):
        if df.empty:
            return
        try:
            conn = sqlite3.connect(self.cache_db)
            df_copy = df.copy()
            df_copy['cache_lat'] = cache_lat
            df_copy['cache_lon'] = cache_lon
            df_copy['cache_radius'] = cache_radius
            df_copy['cache_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df_copy.to_sql('charger_cache', conn, if_exists='append', index=False)
            conn.close()
        except Exception as e:
            print(f"缓存写入失败: {e}")

    def _get_cached_data(self, user_lat, user_lon, radius_km):
        try:
            conn = sqlite3.connect(self.cache_db)
            cutoff = (datetime.now() - timedelta(hours=self.cache_hours)).strftime('%Y-%m-%d %H:%M:%S')
            query = f"SELECT * FROM charger_cache WHERE cache_time > '{cutoff}' ORDER BY cache_time DESC"
            df = pd.read_sql_query(query, conn)
            conn.close()
            if df.empty:
                return None
            df['distance'] = df.apply(
                lambda r: self._haversine(user_lat, user_lon, r['lat'], r['lon']),
                axis=1
            )
            df = df[df['distance'] <= radius_km].sort_values('distance')
            return df.head(50)
        except Exception as e:
            print(f"缓存读取失败: {e}")
            return None

    def get_db_update_time(self):
        try:
            conn = sqlite3.connect(self.cache_db)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(cache_time) FROM charger_cache")
            result = cursor.fetchone()
            conn.close()
            if result and result[0]:
                return result[0]
            return None
        except Exception as e:
            print(f"获取更新时间失败: {e}")
            return None

    # ------------------ 用户端：获取周边充电桩 ------------------
    def get_nearby_chargers(self, user_lat, user_lon, radius_km=5):
        """用户端调用：优先真实API，失败则模拟"""
        if not self.use_real_data:
            return self.generate_simulated_at_location(user_lat, user_lon, max(10, int(radius_km * 2)))

        cached = self._get_cached_data(user_lat, user_lon, radius_km)
        if cached is not None and not cached.empty:
            return cached

        df = self._fetch_from_amap(user_lat, user_lon, radius_km)
        if df.empty:
            df = self.generate_simulated_at_location(user_lat, user_lon, max(10, int(radius_km * 2)))
        else:
            self._save_to_cache(df, user_lat, user_lon, radius_km)
        return df

    # ------------------ 模拟数据生成（基于位置） ------------------
    def generate_simulated_at_location(self, lat, lon, n_points=15):
        """以用户位置为中心生成周边模拟充电桩（用于用户端）"""
        np.random.seed(int(time.time()) % 1000)
        lats = lat + 0.02 * np.random.randn(n_points)
        lons = lon + 0.03 * np.random.randn(n_points)

        districts = ['东城区', '西城区', '朝阳区', '海淀区', '丰台区', '石景山区',
                     '通州区', '大兴区', '房山区', '门头沟区', '昌平区', '顺义区',
                     '密云区', '怀柔区', '平谷区', '延庆区']

        stations = []
        for i in range(n_points):
            dist = self._haversine(lat, lon, lats[i], lons[i])
            district = np.random.choice(districts)
            road = f"{np.random.choice(['路', '大街', '东路', '西路', '南路', '北路'])}"
            number = np.random.randint(1, 200)
            address = f"北京市{district}{road}{number}号"
            name = f"{district}充电站_{i:03d}"

            stations.append({
                'id': f'sim_{i}',
                'name': name,
                'address': address,
                'lat': lats[i],
                'lon': lons[i],
                'type': np.random.choice(['快充', '慢充'], p=[0.6, 0.4]),
                'power': np.random.choice([60, 120, 180]),
                'utilization': round(np.random.uniform(0.1, 0.9), 2),
                'price': round(np.random.uniform(0.9, 2.0), 2),
                'available_slots': np.random.randint(0, 6),
                'distance': round(dist, 2)
            })
        return pd.DataFrame(stations)

    # ------------------ 政府端：生成全城模拟数据（基于行政区热点） ------------------
    def generate_simulated_data(self, center_lat=39.9, center_lon=116.4, n_points=150):
        """生成符合真实分布特征的模拟数据（政府端使用）"""
        np.random.seed(42)

        districts_info = {
            '朝阳区': {'weight': 1.2, 'centers': [(39.92, 116.46), (39.99, 116.48), (40.08, 116.48)]},
            '海淀区': {'weight': 1.1, 'centers': [(39.98, 116.31), (39.91, 116.23), (40.02, 116.27)]},
            '东城区': {'weight': 0.9, 'centers': [(39.90, 116.41), (39.93, 116.42)]},
            '西城区': {'weight': 0.9, 'centers': [(39.90, 116.37), (39.94, 116.36)]},
            '丰台区': {'weight': 0.8, 'centers': [(39.86, 116.29), (39.85, 116.35)]},
            '石景山区': {'weight': 0.6, 'centers': [(39.91, 116.22)]},
            '通州区': {'weight': 0.7, 'centers': [(39.90, 116.66)]},
            '大兴区': {'weight': 0.6, 'centers': [(39.73, 116.33)]},
            '房山区': {'weight': 0.5, 'centers': [(39.75, 116.14)]},
            '门头沟区': {'weight': 0.4, 'centers': [(39.94, 116.10)]},
            '昌平区': {'weight': 0.5, 'centers': [(40.22, 116.23)]},
            '顺义区': {'weight': 0.5, 'centers': [(40.13, 116.65)]},
            '密云区': {'weight': 0.3, 'centers': [(40.38, 116.85)]},
            '怀柔区': {'weight': 0.3, 'centers': [(40.32, 116.63)]},
            '平谷区': {'weight': 0.2, 'centers': [(40.14, 117.12)]},
            '延庆区': {'weight': 0.2, 'centers': [(40.46, 115.97)]},
        }

        all_lats, all_lons, all_districts = [], [], []
        all_addresses, all_names = [], []
        all_types, all_powers, all_utilizations, all_prices, all_available = [], [], [], [], []

        total_weights = sum(info['weight'] for info in districts_info.values())
        expected_counts = {district: max(5, int(n_points * info['weight'] / total_weights)) for district, info in districts_info.items()}

        for district, info in districts_info.items():
            expected_count = expected_counts[district]
            centers = info['centers']
            district_lats, district_lons = [], []
            n_centers = len(centers)
            points_per_center = expected_count // n_centers
            remainder = expected_count % n_centers

            for i, (c_lat, c_lon) in enumerate(centers):
                points_to_gen = points_per_center + (1 if i < remainder else 0)
                if points_to_gen <= 0:
                    continue
                lats = np.random.normal(c_lat, 0.03, points_to_gen)
                lons = np.random.normal(c_lon, 0.03, points_to_gen)
                district_lats.extend(lats)
                district_lons.extend(lons)

            all_lats.extend(district_lats)
            all_lons.extend(district_lons)
            all_districts.extend([district] * len(district_lats))

            for _ in range(len(district_lats)):
                charger_type = np.random.choice(['快充', '慢充'], p=[0.65, 0.35])
                power = np.random.choice([120, 150, 180, 240]) if charger_type == '快充' else np.random.choice([60, 80, 100])
                base_util = np.random.uniform(0.35, 0.85) if info['weight'] > 0.9 else np.random.uniform(0.2, 0.7)
                utilization = min(0.95, base_util + np.random.uniform(-0.15, 0.15))
                base_price = 1.2 if charger_type == '快充' else 0.9
                if info['weight'] > 0.9:
                    base_price += 0.15
                price = base_price + np.random.uniform(-0.2, 0.2)
                price = round(price, 2)

                if utilization > 0.7:
                    available = np.random.randint(0, 3)
                elif utilization > 0.4:
                    available = np.random.randint(2, 6)
                else:
                    available = np.random.randint(4, 10)

                all_types.append(charger_type)
                all_powers.append(power)
                all_utilizations.append(round(utilization, 2))
                all_prices.append(price)
                all_available.append(available)

                road = f"{np.random.choice(['路', '大街', '东路', '西路', '南路', '北路'])}"
                number = np.random.randint(1, 200)
                all_addresses.append(f"北京市{district}{road}{number}号")
                all_names.append(f"{district}充电站_{np.random.randint(100, 999)}")

        df = pd.DataFrame({
            'id': [f'sim_{i}' for i in range(len(all_lats))],
            'name': all_names,
            'address': all_addresses,
            'lat': all_lats,
            'lon': all_lons,
            'type': all_types,
            'power': all_powers,
            'utilization': all_utilizations,
            'price': all_prices,
            'available_slots': all_available,
            'distance': 0
        })

        # 计算到市中心（天安门）的距离
        def haversine(lon1, lat1, lon2, lat2):
            R = 6371
            lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c

        df['distance'] = df.apply(lambda r: haversine(116.397128, 39.916527, r['lon'], r['lat']), axis=1)
        return df.sort_values('distance')

    # ------------------ 政府端：加载数据（主入口） ------------------
    def load_charger_data(self, use_cache=True, cache_hours=24):
        """政府端加载数据，优先使用真实数据（若 use_real_data=True）"""
        if self.use_real_data:
            print("政府端尝试使用真实数据")
            df = self._fetch_from_amap(39.9, 116.4, 10)
            if not df.empty:
                return df
            else:
                print("真实数据获取失败，回退到模拟数据")
                return self.generate_simulated_data(39.9, 116.4, 150)
        else:
            return self.generate_simulated_data(39.9, 116.4, 150)

    # ------------------ 工具方法 ------------------
    def filter_data(self, data, selected_type):
        if selected_type in ['快充', '慢充']:
            return data[data['type'] == selected_type]
        return data

    def simple_demand_prediction(self, data):
        """简单需求预测（基于距市中心距离）"""
        if data.empty:
            return []
        center_lat, center_lon = 39.9, 116.4
        preds = []
        for _, row in data.iterrows():
            d = self._haversine(center_lat, center_lon, row['lat'], row['lon'])
            factor = max(0.1, 1 - d / 10)
            pred = row['utilization'] * 0.6 + factor * 0.4
            preds.append(min(0.95, pred))
        return preds