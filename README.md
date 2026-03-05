# 校园二手书交易与智能定价系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3+-green?style=flat-square" alt="Flask">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple?style=flat-square" alt="Bootstrap">
  <img src="https://img.shields.io/badge/MySQL-8.0-orange?style=flat-square" alt="MySQL">
</p>

> 基于 Flask 的校园二手书交易平台，包含智能定价功能

## 📚 项目简介

本系统是一个面向校园的二手书交易平台，支持用户注册登录、书籍发布与检索、智能定价、交易撮合、订单管理、评价反馈等功能。

### 核心特性

- 🏫 **校园专属** - 针对校园场景设计，学生身份验证
- 🤖 **智能定价** - 基于书籍信息自动推荐合理价格
- 📱 **移动优先** - 响应式设计，手机电脑都能用
- 🔒 **用户信用** - 信用分系统，保障交易安全

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 后端 | Python 3.9+ / Flask 2.3+ |
| 前端 | HTML5 / JavaScript / Bootstrap 5 |
| 数据库 | MySQL 8.0 |
| AI 定价 | 阿里百炼 API (DashScope) |
| 服务器 | Gunicorn / Nginx |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Qi-Cao/campus-book-trading.git
cd campus-book-trading
```

### 2. 配置环境

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置数据库

```bash
# 复制配置示例文件
cp .env.example .env

# 编辑 .env 文件，填入以下配置：
# DB_HOST=localhost
# DB_PORT=3306
# DB_NAME=campus_books
# DB_USER=root
# DB_PASSWORD=your_password
# DASHSCOPE_API_KEY=your_api_key
```

### 4. 初始化数据库

```bash
# 首次初始化
python init_db.py

# 或者重置数据库（清除所有数据）
python reset_db.py
```

### 5. 启动服务

```bash
# 开发模式
python run.py

# 生产模式
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

访问 http://localhost:5000 即可使用！

---

## 📖 功能模块

### 1. 用户系统

| 功能 | 说明 |
|------|------|
| 用户注册 | 支持邮箱验证 |
| 用户登录 | Session 登录 |
| 个人资料 | 修改头像、联系方式 |
| 信用分 | 根据交易行为自动计算 |

### 2. 书籍管理

| 功能 | 说明 |
|------|------|
| 发布书籍 | 填写 ISBN、定价、描述、上传图片 |
| 智能识别 | AI 自动识别书籍信息 |
| 智能定价 | 基于市场数据推荐价格 |
| 搜索筛选 | 按分类、价格、状态筛选 |
| 书籍详情 | 展示完整信息和卖家信息 |

### 3. 交易系统

| 功能 | 说明 |
|------|------|
| 在线购买 | 一键下单 |
| 订单管理 | 待确认/待发货/待收货/已完成 |
| 手动确认 | 收货后确认完成 |
| 取消订单 | 未发货时可取消 |

### 4. 评价系统

| 功能 | 说明 |
|------|------|
| 交易评价 | 交易完成后互评 |
| 信用分 | 根据评价计算 |
| 评价展示 | 店铺评分展示 |

---

## 📁 项目结构

```
campus-book-trading/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── models/
│   │   └── models.py        # 数据库模型
│   ├── routes/
│   │   ├── auth.py          # 认证路由
│   │   ├── books.py         # 书籍路由
│   │   ├── orders.py        # 订单路由
│   │   ├── main.py          # 主页路由
│   │   └── api.py           # API 路由
│   ├── utils/
│   │   ├── dashscope_helper.py  # 阿里百炼 API
│   │   └── smart_pricing.py     # 智能定价
│   └── templates/           # Jinja2 模板
│       ├── base.html        # 基础模板
│       ├── auth/            # 认证相关
│       ├── books/           # 书籍相关
│       ├── orders/          # 订单相关
│       └── index.html      # 首页
├── static/                 # 静态文件
├── run.py                  # 启动入口
├── config.py               # 配置文件
├── init_db.py              # 数据库初始化
├── reset_db.py             # 数据库重置
├── upgrade_db.py           # 数据库升级
└── requirements.txt        # Python 依赖
```

---

## 👤 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | testuser | test123 |

---

## 🔧 常用命令

```bash
# 初始化数据库
python init_db.py

# 重置数据库（清除所有数据）
python reset_db.py

# 启动开发服务器
python run.py

# 生产环境部署
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# 查看日志
tail -f logs/app.log
```

---

## 📦 API 接口

### 书籍相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/books | 获取书籍列表 |
| GET | /api/books/<id> | 获取书籍详情 |
| POST | /api/books | 发布书籍 |
| PUT | /api/books/<id> | 更新书籍 |
| DELETE | /api/books/<id> | 删除书籍 |

### 订单相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/orders | 获取订单列表 |
| POST | /api/orders | 创建订单 |
| PUT | /api/orders/<id> | 更新订单状态 |

---

## 🐛 常见问题

### Q: 数据库连接失败

A: 检查 `.env` 中的数据库配置是否正确，确保 MySQL 服务已启动。

### Q: 智能定价不工作

A: 检查是否配置了有效的百炼 API Key。

### Q: 图片上传失败

A: 检查 `static/uploads` 目录是否有写入权限。

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 👨‍💻 作者

- GitHub: [@Qi-Cao](https://github.com/Qi-Cao)

---

<p align="center">Made with ❤️ for campus book trading</p>
