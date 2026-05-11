---
name: project-overview
description: RR Procedure 项目完整状态，包含已完成和待办事项
type: project
originSessionId: 71328002-1815-4153-911e-3fad763cd149
---
# RR Procedure — Recognition & Reward

企业内匿名 Coin 认可系统，嵌入飞书自建应用（H5）。

## 技术架构

- FastAPI + Jinja2 + HTMX + Alpine.js（纯 Python SSR）
- Pico CSS（classless 语义化）
- 飞书多维表格（业务数据）+ 本地 SQLite（私有交易日志）
- 飞书 h5-js-sdk 1.5.23（JSSDK 鉴权 + 通讯录选人）

## 文件清单

| 文件 | 职责 |
|------|------|
| main.py | FastAPI 入口、OAuth 回调、JSSDK 签名接口、auth 中间件、lifespan |
| settings.py | 全部配置项（飞书、SQLite、权限、规则参数） |
| auth.py | Session 创建/读取、超管判断、公开路径白名单 |
| database.py | SQLite 连接管理、transactions 表 |
| utils.py | Bitable 字段解析 |
| models/feishu.py | 飞书 API：token/ticket/签名、bitable CRUD、用户查询、通讯录 |
| models/rules.py | Coin 分配公式 + 转赠校验 |
| models/transaction.py | 交易记录 CRUD（SQLite） |
| routes/home.py | 员工首页 Dashboard |
| routes/transfer.py | 转赠页面 + POST 处理 |
| routes/starwall.py | 明星墙展示 |
| routes/admin.py | 管理面板、发起/关闭轮次、交易明细 |
| templates/base.html | 基模板（Pico CSS + HTMX + Alpine.js + h5-js-sdk） |
| templates/home.html | 首页 |
| templates/transfer.html | 转赠页（含联系人选择器 Alpine 组件） |
| templates/starwall.html | 明星墙 |
| templates/admin.html | 管理面板 |
| templates/transactions.html | 交易明细 |
| setup_bitable.py | 一键创建多维表格 4 张表（仅在首次配置时运行） |
| .env | 飞书应用凭证、多维表格 ID、DB 路径等 |

## 已完成功能

1. **飞书 OAuth 免登** — auth 中间件自动拦截未认证请求，重定向飞书授权页，回调后写 session cookie
2. **JSSDK 鉴权完整链路** — token → ticket → SHA1 签名，`/api/jsapi-config` 接口返回 config 参数
3. **通讯录选人组件** — `tt.chooseContact()` 在 transfer.html 中集成，选人后填充隐藏字段
4. **多维表格 CRUD** — `get_bitable_records`（分页）、`add_bitable_records`（批量）、`update_bitable_records`（逐条）
5. **4 张多维表格** — 员工花名册、轮次、余额、明星墙（通过 setup_bitable.py 创建）
6. **4 个页面全部 SSR 渲染** — Home / Transfer / Starwall / Admin 均返回 200
7. **Coin 业务规则** — 司龄→Coin、单人单对象上限 3、禁止自赠、仅 active 轮次可转

## 飞书多维表格 ID

| 表 | ID |
|----|-----|
| 员工花名册 | tblRdThpr7S4C8Gu |
| 轮次 | tblDEc6YncuOkYOE |
| 余额 | tblRV6ciQMJr8xjp |
| 明星墙 | tblyQiHJJe7Xxlxm |

## JSSDK 关键细节（容易踩坑）

- CDN: `h5-js-sdk-1.5.23.js`（非 lark-jssdk，后者是 Lark 国际版）
- config 方法: `h5sdk.config({appId, timestamp, nonceStr, signature, jsApiList, onSuccess, onFail})`
- 签名参数名: `noncestr`（全小写），config 参数名: `nonceStr`（驼峰）
- timestamp 是**毫秒**级，非秒级
- 签名串: `jsapi_ticket=xxx&noncestr=xxx&timestamp=xxx&url=xxx`（按字母排序后用 SHA1）

## 待办

1. **用户需在飞书客户端中测试** — 本地 localhost 无法使用 JSSDK（需配置可信域名）
2. **导入真实员工数据** — 需将员工花名册数据导入多维表格
3. **配置 SUPER_ADMINS** — 将自己的飞书 open_id 填入 settings.py
4. **飞书开放平台配置** — H5 可信域名、应用主页 URL
5. **HR 操作员角色** — 仅实现了超管，操作员权限分级未做
6. **关闭轮次防重复** — admin.py 缺少幂等逻辑
7. **聚合数据看板** — admin 面板缺少统计图表
8. **交易明细权限** — 需确保仅超管可查 transactions
