import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # 1. 获取 app.py 的绝对路径
    # 注意：这里假设编译后 app.py 会被打包进内部
    app_path = resolve_path("app.py")
    
    # 2. 伪造命令行参数
    # 等同于在终端执行：streamlit run app.py --global.developmentMode=false
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    
    # 3. 启动 Streamlit
    sys.exit(stcli.main())