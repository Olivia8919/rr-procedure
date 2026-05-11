# 飞书多维表格 — 新建表 Schema

## 通用说明

- 所有表创建在同一个多维表格应用（Bitable App）下
- 字段类型使用飞书多维表格支持的标准类型
- 表之间通过 `round_id` 和 `feishu_open_id` 进行关联

---

## 表 1：Rounds（轮次管理）

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| round_id | 文本 | 是 | 轮次唯一 ID（UUID 前 8 位） |
| title | 文本 | 否 | 轮次名称，如 "2026 Q2 评优" |
| status | 单选 | 是 | 选项：draft / active / closed |
| start_date | 日期 | 否 | 开始日期 |
| end_date | 日期 | 否 | 结束日期 |

> status 字段必须先创建单选选项：draft、active、closed

---

## 表 2：Coin Balances（Coin 账户，按轮次）

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| round_id | 文本 | 是 | 关联轮次 |
| feishu_open_id | 文本 | 是 | 员工飞书标识 |
| coins_allocated | 数字 | 是 | 系统分配数（自动计算） |
| coins_given | 数字 | 是 | 已转出数（初始 0） |
| coins_received | 数字 | 是 | 已收到数（初始 0，匿名汇总） |

> 每轮每位员工一行记录，由系统在「发起轮次」时自动创建

---

## 表 3：Star Wall（明星墙）

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| round_id | 文本 | 是 | 关联轮次 |
| department | 文本 | 是 | 部门名称 |
| winner_name | 文本 | 是 | 部门优胜者姓名 |
| coins_received | 数字 | 是 | 获得 Coin 总数 |

> 轮次关闭时由系统自动填充，每部门一行

---

## 现有表：Employees（员工花名册，已存在）

系统假定员工花名册中有以下字段（如字段名不同，需在 settings.py 中修改或调整 `get_employee_map()` 映射）：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| feishu_open_id | 文本 | 是 | 员工在飞书的唯一标识 |
| name | 文本 | 是 | 员工姓名 |
| department | 文本/单选 | 是 | 所属部门 |
| tenure_months | 数字 | 是 | 入职月份数（用于计算 Coin 分配） |

> 如果实际字段名与此不同，需要修改代码中 `parse_bitable_fields` 调用处的字段名
