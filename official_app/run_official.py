import streamlit.web.cli as stcli
import os
import sys
import webbrowser
import threading
import time
import socket


def is_port_open(port, host='localhost'):
    """检查端口是否已打开（服务器是否启动）"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except ConnectionRefusedError:
            return False


def open_browser_when_ready(port, url):
    """等待服务器启动后打开浏览器"""
    timeout = 10  # 最多等待10秒
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(port):
            webbrowser.open(url)
            break
        time.sleep(0.5)


if __name__ == "__main__":
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_path, "app_official.py")  # 政府端改为 app_official.py

    if not os.path.exists(app_path):
        print("找不到 app_user.py:", app_path)
        sys.exit(1)

    port = 8501  # 政府端用 8501
    url = f"http://localhost:{port}"

    # 启动线程等待服务器就绪后打开浏览器
    threading.Thread(target=open_browser_when_ready, args=(port, url), daemon=True).start()

    sys.argv = [
        "streamlit", "run", app_path,
        "--global.developmentMode=false",
        "--server.headless=true",  # 保持true，但我们手动打开
        "--browser.serverAddress=localhost",
        f"--server.port={port}"
    ]
    sys.exit(stcli.main())