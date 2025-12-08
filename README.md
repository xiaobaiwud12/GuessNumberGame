# 🎮 Liquid Glass Guess Number (液态玻璃猜数字游戏)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-ff4b4b?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square)

一个基于 **Streamlit** 构建的现代化猜数字游戏，拥有极具美感的 **iOS 风格液态玻璃 (Liquid Glass)** UI 设计。支持用户登录、排行榜、动态背景获取以及一键打包为 EXE 可执行文件。

---

## ✨ 项目亮点

### 🎨 极致 UI 设计
- **液态玻璃拟态**：全透视磨砂玻璃卡片，配合流光渐变背景
- **沉浸式输入**：深度定制的输入框，移除原生边框，聚焦时呈现高可读性灰度遮罩
- **动态交互反馈**：
  - 📉 **猜小了**：红色液态玻璃提示框
  - 📈 **猜大了**：蓝色液态玻璃提示框
  - 🎉 **猜对了**：绿色液态玻璃提示框

### 🛠️ 核心功能
- **账号系统**：轻量级本地数据存储 (`users.json`)，支持注册与登录
- **排行榜**：自动记录并展示所有玩家的最佳成绩（最少猜测次数）
- **动态背景**：
  - 启动时自动从 API 获取高清二次元横屏壁纸
  - 智能反代节点切换，下载失败自动回退至深色流光渐变背景
  - 可以由用户自行从`Lolicon_api`获取新的背景（`bg.jpg`）

### 📦 部署与运行优化
- **单文件 EXE**：基于 PyInstaller 打包，内置 Python 环境，无需配置即可运行
- **静默运行**：打包后无黑色控制台窗口，纯净体验
- **智能进程管理**：程序启动时自动在同级目录生成 `双击关闭程序.bat`，解决无终端模式下难以彻底关闭后台进程的问题

---

## 🚀 快速开始

### 方式一：直接运行 EXE (用户模式)
1. 下载 Release 中的 `GuessNumberGame.exe`
2. 双击运行，等待浏览器自动打开
3. 程序会自动下载背景图 (`bg.jpg`) 并生成数据文件 (`users.json`)
4. **如何退出**：由于隐藏了终端窗口，请双击目录下的 **`双击关闭程序.bat`** 来彻底结束游戏进程

### 方式二：源码运行 (开发者模式)

1. **克隆仓库**
   ```bash
   git clone https://github.com/xiaobaiwud12/GuessNumberGame
   cd GuessNumberGame
   ```

2. **安装依赖**
   ```bash
   pip install streamlit requests pyinstaller
   ```

3. **运行应用**
   ```bash
   streamlit run app.py
   ```

---

## 🔨 编译构建

本项目提供了专用的构建脚本 `build_exe.py`，解决了 Streamlit 静态资源丢失和依赖打包的问题。

### 准备环境
确保已安装所有依赖，并删除旧的 `build`、`dist` 文件夹及 `.spec` 文件。

### 运行构建脚本
```bash
python build_exe.py
```

脚本会自动处理 hidden imports、HTML/JS 资源注入以及配置无控制台模式。

### 获取产物
编译完成后，在 `dist/` 目录下找到 `GuessNumberGame.exe`。

---

## 📂 项目结构

```
GuessNumberGame/
├── app.py              # 核心代码：UI 渲染、CSS 注入、游戏逻辑
├── run.py              # 启动脚本：通过 Streamlit CLI 运行主程序`app.py`
├── build_exe.py        # 编译脚本：PyInstaller 自动化打包配置
├── users.json          # 数据文件：存储用户信息 (自动生成，同时记录用户最佳成绩)
├── bg.jpg              # 资源文件：背景图片 (自动下载,也可以通过重命名jepg格式图片来自定义)
└── README.md           # 项目文档
```
## `users.json` 格式说明文档

### JSON 结构说明

- **根对象**：包含所有用户数据的 JSON 对象
- **键（Key）**：用户名（字符串）
- **值（Value）**：用户详细信息对象

---

## 🔑 字段详解

### 1. 用户名（Key）

- **类型**：`string`
- **说明**：用户的唯一标识符
- **限制**：
  - 不能为空
  - 不能重复
  - 区分大小写
- **示例**：`"无锡佳佳惠"`, `"管城"`, `"mayin"`

### 2. password（密码哈希）

- **类型**：`string`
- **说明**：用户密码的 SHA-256 哈希值
- **格式**：64 位十六进制字符串
- **加密算法**：SHA-256
- **示例**：
  ```json
  "password": "bbb59da3af939f7af5f360f2ceb80a496e3bae1cd87dde426db0ae40677e1c2c"
  ```

**安全说明：**
- ✅ 密码以哈希形式存储，不可逆
- ✅ 即使数据泄露，原始密码也无法被还原
- ⚠️ 相同密码会产生相同哈希值

### 3. best_score（最好成绩）

- **类型**：`integer` 或 `null`
- **说明**：用户在游戏中猜对数字所用的最少次数
- **取值范围**：正整数（1 ~ ∞）
- **初始值**：`null`（新用户尚未完成游戏）
- **更新规则**：仅当新成绩优于旧成绩时更新

**示例：**
```json
"best_score": 5      // 最少用 5 次猜对
"best_score": 1      // 最佳成绩：第一次就猜对！
"best_score": null   // 尚未完成游戏
```

### 4. created_at（创建时间）

- **类型**：`string`
- **格式**：ISO 8601 格式的 UTC 时间戳
- **说明**：用户账户创建的时间
- **时区**：UTC（协调世界时）
- **精度**：微秒级

**格式说明：**
```
YYYY-MM-DDTHH:MM:SS.ffffff
│    │  │ │  │  │  └─ 微秒（6位）
│    │  │ │  │  └─ 秒（00-59）
│    │  │ │  └─ 分钟（00-59）
│    │  │ └─ 小时（00-23）
│    │  └─ 日（01-31）
│    └─ 月（01-12）
└─ 年（4位）
```

---

## 📄 许可证

本项目采用 **MIT 许可证** 进行授权。这是一个非常宽松的许可证，允许你在保留署名的前提下自由使用、修改和分发代码（包括商业用途）。

```text
MIT License

Copyright (c) 2023 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

**享受游戏的乐趣！** 🎯✨
