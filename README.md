# StudyTask · 个人学习任务管理系统

《软件工程》实验一交付物。单用户、本地运行的学习任务管理 Web 应用，用于记录课程作业、实验、考试准备等事项。

- 技术栈：Python 3.13 + Flask 3.1 + SQLite（原生 HTML/CSS/JS，无前端框架）
- 运行方式：本机启动服务，浏览器访问 `http://127.0.0.1:5000`
- 数据存储：项目根目录下的 `studytask.db`（SQLite 文件）

## 功能清单

| 需求编号 | 功能 | 说明 |
|---|---|---|
| FR-01 | 新建任务 | 校验名称、课程、截止日期；名称 1–100 字、课程 1–60 字 |
| FR-02 | 任务列表与详情 | 列表显示名称/课程/截止日期/状态/优先级，可进入详情页 |
| FR-03 | 编辑任务 | 修改后列表与详情一致，更新时间同步 |
| FR-04 | 删除任务 | 前端 `confirm` 二次确认，`POST` 后才真正删除 |
| FR-05 | 状态调整 | 待完成 / 进行中 / 已完成 任意切换 |
| FR-06 | 组合筛选 | 课程 + 状态 + 优先级，条件可叠加 |
| FR-07 | 逾期提醒 | 未完成且截止日期早于今天 → 「逾期」；未来 3 天内到期 → 「即将到期」；已完成不提醒 |
| FR-08 | 统计 | 任务总数、已完成数、完成率；总数为 0 时显示 0% |
| FR-09 | 持久化 | 数据写入 SQLite 文件，重启后不变 |
| FR-10 | 中文界面 | 全部中文，输入非法时有明确错误提示，不崩溃 |

## 目录结构

```
软件工程实验一/
├── app.py                 # Flask 应用与路由
├── db.py                  # 数据层：建表、校验、CRUD、统计、逾期计算
├── requirements.txt       # 依赖清单
├── pytest.ini             # 测试配置
├── templates/             # 页面模板
│   ├── base.html          # 公共布局
│   ├── index.html         # 列表 + 统计 + 筛选
│   ├── form.html          # 新建 / 编辑表单
│   ├── detail.html        # 详情 + 状态切换
│   └── 404.html
├── static/style.css       # 样式
├── tests/test_acceptance.py  # T1~T10 自动化验收测试
├── docs/
│   ├── AI_DEV_LOG.md      # AI 开发过程记录
│   └── 验收记录表.md       # 手工验收证据表
└── studytask.db           # 运行时自动生成（不入库）
```

## 环境准备

需要 Python 3.10 及以上。

```powershell
cd "C:\Users\muke\Desktop\软件工程实验一"

# 1. 创建虚拟环境（仓库里已有 .venv 可跳过）
python -m venv .venv

# 2. 激活
.\.venv\Scripts\Activate.ps1

# 3. 安装依赖
pip install -r requirements.txt
```

> **网络提示**：本机全局 pip 源（清华镜像）对 pip 请求返回 403，`pypi.org` 直连会超时。
> 虚拟环境内已通过 `.venv\pip.ini` 指向阿里云镜像。若重建虚拟环境导致安装失败，请用：
> `pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`

## 运行

```powershell
python app.py
```

浏览器打开 <http://127.0.0.1:5000>。首次启动会自动创建 `studytask.db` 和表结构。

## 测试

```powershell
pytest -v
```

预期：`15 passed`。测试覆盖 T1~T10 全部验收用例，另含非法日期、404、列表排序等回归用例。

| 用例 | 对应测试函数 |
|---|---|
| T1 | `test_t1_create_task_and_show_in_list` |
| T2 | `test_t2_empty_name_rejected` |
| T3 | `test_t3_edit_persists` |
| T4 | `test_t4_status_progress` |
| T5 | `test_t5_filters` |
| T6 | `test_t6_overdue` |
| T7 | `test_t7_due_soon` |
| T8 | `test_t8_statistics` |
| T9 | `test_t9_delete_requires_post` |
| T10 | `test_t10_data_survives_restart` |

## 数据与重置

- 数据文件：`studytask.db`（已被 `.gitignore` 忽略）
- 清空数据：停止服务后删除 `studytask.db`，再次启动会自动重建空表

## 设计说明

- **逾期/即将到期不落库**：`db.decorate()` 按“当前日期”实时计算，避免日期推移后数据库里的标记过期。
- **删除必须 POST**：GET 请求删除返回 405，配合前端 `confirm` 实现“取消不删、确认才删”。
- **校验集中在数据层**：`db.validate_task()` 同时被新建和编辑复用，路由层不重复写规则。
- **列表排序**：按截止日期升序，同日期按 id 升序，最紧急的排在最前。

## 已知限制

- 单用户本地使用，无登录与权限控制（符合 A.5 范围外约定）。
- 未做分页，任务量很大时列表会变长（200 条规模内操作正常）。
- 使用 Flask 开发服务器，仅适合本机演示。
