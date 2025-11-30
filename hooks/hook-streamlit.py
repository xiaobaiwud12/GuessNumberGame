from PyInstaller.utils.hooks import copy_metadata

# 强制复制 streamlit 的元数据
datas = copy_metadata('streamlit')