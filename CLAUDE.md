# RR Procedure — Recognition & Reward

## 核心定位
企业内部的匿名认可与奖励机制，嵌入飞书自建应用。员工将按司龄分配的 DS Coins 匿名转赠给同事，按部门排名，优胜者登上「咸蛋超人」明星墙。

## 技术栈
- **纯 Python 全栈**：FastAPI + Jinja2 + HTMX + Alpine.js（少量）
- **CSS**：Pico CSS（classless 语义化）
- **数据**：飞书多维表格（业务数据）+ 本地 SQLite（私有交易日志）
- **飞书 SDK**：lark-oapi（官方 Python SDK）
- **部署**：企业内网 Uvicorn 单进程

## 铁律
- 交易明细表不暴露给普通用户和 HR 操作员，仅 HR 超级管理员可查询
- 超级管理员通过 settings.py 的 SUPER_ADMINS 硬编码配置
- 不引入 ORM，直接用 aiosqlite 写原生 SQL
- 不做前后端分离，全部 SSR

## 业务规则
- 司龄 → Coin：每 1 个月司龄 = 1 Coin，上限 20
- 单人单对象赠予上限 3 个 Coin，总对象数不限
- 禁止自赠，必须全部转出
- 仅在 round.status = active 时可转赠

## 权限分级
| 角色 | 权限 |
|------|------|
| 普通员工 | 自己的余额/转出/收到/排名 |
| HR 操作员 | 聚合数据、发起/关闭轮次 |
| HR 超管 | 以上全部 + 交易明细 |

## 飞书对接
- 员工花名册：对接现有飞书多维表格（表结构待确认）
- 应用类型：自建应用（H5），嵌入飞书工作台
- 认证：飞书 OAuth → session cookie，不另建登录系统
