import os
import sys
import streamlit
import PyInstaller.__main__

def build():
    # 1. 获取当前 Streamlit 库的安装路径
    st_path = os.path.dirname(streamlit.__file__)
    print(f"📍 Streamlit 安装路径: {st_path}")

    # 2. 构造资源路径映射
    sep = ';' if os.name == 'nt' else ':'
    
    # 强制包含 static 文件夹 (网页资源) 和 runtime
    add_data_static = f"{os.path.join(st_path, 'static')}{sep}streamlit/static"
    add_data_runtime = f"{os.path.join(st_path, 'runtime')}{sep}streamlit/runtime"
    
    # 包含主程序 app.py
    add_data_app = f"app.py{sep}."

    # 3. 定义 PyInstaller 参数
    args = [
        'run.py',                       # 入口脚本
        '--onefile',                    # 打包成单文件
        '--clean',                      # 清理缓存
        '--name=GuessNumberGame',       # EXE 的名字
        f'--add-data={add_data_static}',   # 注入 Streamlit 静态资源
        f'--add-data={add_data_runtime}',  # 注入 Runtime
        f'--add-data={add_data_app}',      # 注入源代码
        
        # 强制导入依赖
        '--hidden-import=streamlit',
        '--hidden-import=streamlit.web.cli',
        '--hidden-import=streamlit.runtime.scriptrunner.magic_funcs',
        '--hidden-import=streamlit.runtime.scriptrunner.script_runner',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=requests',
        
        # 复制元数据 (只保留必须的，删除了报错的 tqdm)
        '--copy-metadata=streamlit',
        '--copy-metadata=requests',
        '--copy-metadata=packaging',
    ]

    # 4. 执行打包
    print("🚀 开始打包，请稍候...")
    
    # 设置递归深度
    sys.setrecursionlimit(5000)
    
    PyInstaller.__main__.run(args)
    print("✅ 打包完成！请查看 dist 文件夹。")

if __name__ == "__main__":
    build()