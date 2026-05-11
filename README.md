# RR Procedure — Recognition & Reward

企业内网匿名认可与奖励系统，嵌入飞书自建应用（H5）。员工将按司龄分配的 DS Coin 匿名转赠给同事，按部门排名，优胜者登上明星墙。

## 技术栈

| 层级 | 选型 |
|------|------|
| Web 框架 | FastAPI（异步） |
| 模板引擎 | Jinja2（SSR，前后端不分离） |
| CSS | Pico CSS（classless 语义化） |
| 前端交互 | HTMX + Alpine.js |
| 飞书 SDK | h5-js-sdk 1.5.23（JSSDK 鉴权 + 通讯录选人） |
| 业务数据 | 飞书多维表格（Bitable） |
| 交易日志 | 本地 SQLite（aiosqlite） |
| 认证 | 飞书 OAuth 免登 → Session Cookie |

## 项目结构

```
.
├── main.py                  # FastAPI 入口、OAuth 回调、JSSDK 签名接口、auth 中间件
├── settings.py              # 全部配置项（飞书、SQLite、权限、业务规则）
├── auth.py                  # Session 创建/校验、超管判断
├── database.py              # SQLite 连接管理、建表
├── utils.py                 # Bitable 字段解析工具
├── setup_bitable.py         # 一键创建多维表格（首次配置）
├── models/
│   ├── feishu.py            # 飞书 API：token/ticket/签名/bitable CRUD/通讯录
│   ├── rules.py             # Coin 分配公式 + 转赠校验
│   └── transaction.py       # 交易记录 CRUD（SQLite）
├── routes/
│   ├── home.py              # 员工首页 Dashboard
│   ├── transfer.py          # 转赠页面 + POST 处理
│   ├── starwall.py          # 明星墙展示
│   └── admin.py             # 管理面板、发起/关闭轮次、交易明细
├── templates/
│   ├── base.html            # 基模板（Pico CSS + HTMX + Alpine.js + JSSDK）
│   ├── home.html            # 首页
│   ├── transfer.html        # 转赠（含联系人选择器）
│   ├── starwall.html        # 明星墙
│   ├── admin.html           # 管理后台
│   └── transactions.html    # 交易明细
├── docs/
│   ├── bitable-schema.md    # 多维表格 Schema
│   └── verification-plan.md # 测试用例
├── project-memory/          # Claude Code 项目记忆备份
├── static/                  # 静态资源
├── requirements.txt
├── .env.example             # 环境变量模板
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入飞书应用凭证和多维表格 ID：

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
BITABLE_APP_TOKEN=xxxxxxxxxxxx
EMPLOYEES_TABLE_ID=tblxxxxxxxx
ROUNDS_TABLE_ID=tblxxxxxxxx
BALANCES_TABLE_ID=tblxxxxxxxx
STARWALL_TABLE_ID=tblxxxxxxxx
SESSION_SECRET=<随机字符串>   # 生产环境务必修改
```

### 3. 创建多维表格（首次）

```bash
python setup_bitable.py
```

此脚本自动在飞书中创建 4 张业务表：员工花名册、轮次、余额、明星墙。运行后将 table_id 填入 `.env`。

### 4. 配置飞书开放平台

在飞书开放平台中：
- **添加应用能力** → 开启「网页应用」
- **H5 可信域名** → 添加部署服务器的域名
- **应用主页** → 设置为 `https://<你的域名>/`

### 5. 配置超级管理员

编辑 `settings.py`，将管理员的飞书 `open_id` 填入 `SUPER_ADMINS` 列表。

### 6. 启动

```bash
python main.py
```

服务运行在 `http://localhost:8000`。从飞书工作台打开应用即可使用。

## 业务规则

| 规则 | 说明 |
|------|------|
| Coin 分配 | 每 1 个月司龄 = 1 Coin，上限 20 |
| 转赠上限 | 单人给同一对象最多 3 Coin |
| 禁止自赠 | 不能给自己转 Coin |
| 全部转出 | 必须在轮次内用完所有 Coin |
| 轮次限制 | 仅在 `status=active` 的轮次中可转赠 |
| 匿名性 | 接收方看不到赠予者身份 |

## 权限分级

| 角色 | 权限范围 |
|------|----------|
| 普通员工 | 查看自己余额/转赠/收到数/排名 |
| HR 超管 | 以上全部 + 聚合数据 + 发起/关闭轮次 + 交易明细 |

## API 接口

| 路径 | 说明 |
|------|------|
| `GET /` | 员工首页 Dashboard |
| `GET /transfer` | 转赠页面 |
| `POST /transfer` | 提交转赠 |
| `GET /starwall` | 明星墙 |
| `GET /admin` | 管理面板 |
| `GET /admin/transactions` | 交易明细 |
| `GET /api/jsapi-config?url=...` | JSSDK 签名配置 |
| `GET /auth/callback` | OAuth 回调 |

## License

Internal use — all rights reserved.
