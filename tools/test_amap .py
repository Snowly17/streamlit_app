import hashlib
import requests

API_KEY = "a8c1a81e1c5f5f6ca9e024f59a69bf5e"
SECRET = "1387378e512c6aacd3ffd79f40f656c7"  # 请确认是否正确

def generate_sig(params, secret):
    sorted_keys = sorted([k for k in params.keys() if k not in ('sig', 'key')])
    sign_str = ''
    for k in sorted_keys:
        sign_str += k + str(params[k])
    sign_str += secret
    print("签名原串:", repr(sign_str))  # 打印原始字符串（便于核对）
    sig = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    return sig

params = {
    'key': API_KEY,
    'location': '116.4,39.9',
    'keywords': '充电站',
    'types': '150900',
    'radius': 10000,
    'offset': 25,
    'page': 1,
    'extensions': 'all'
}

params['sig'] = generate_sig(params, SECRET)

url = "https://restapi.amap.com/v3/place/around"
try:
    resp = requests.get(url, params=params, timeout=10)
    print("HTTP状态码:", resp.status_code)
    print("返回内容:", resp.text)
except Exception as e:
    print("请求失败:", e)