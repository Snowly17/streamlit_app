# run_app.py
import streamlit.web.cli as stcli
import os
import sys

if __name__ == "__main__":
    # 判断是否在打包后的环境中
    if getattr(sys, 'frozen', False):
        # 如果是打包后的 exe，基础路径在 sys._MEIPASS
        base_path = sys._MEIPASS
    else:
        # 如果是开发环境，使用当前文件所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_path, "app.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())