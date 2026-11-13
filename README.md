# StudyTask · 个人学习任务管理系统

《软件工程》实验一交付物。单用户、本地运行的学习任务管理 Web 应用，用于记录课程作业、实验、考试准备等事项。

- 技术栈：Python 3.13 + Flask 3.1 + SQLite（原生 HTML/CSS/JS，无前端框架）
- 运行方式：本机启动服务，浏览器访问 `http://127.0.0.1:5000`
- 数据存储：项目根目录下的 `studytask.db`（SQLite 文件）
- 代码仓库：<https://github.com/muke112320/StudyTask>
- 在线访问：<http://120.76.59.189>

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

## 部署到云服务器

### 服务器配置

- 系统：Ubuntu 22.04 / 24.04 LTS
- 规格：1 核 2G 起步即可（本项目为单用户演示）
- 安全组放行：`22`（SSH）、`80`（HTTP）

### 部署步骤

**1. 本机打包（排除虚拟环境与数据库）**

```powershell
cd "C:\Users\muke\Desktop\软件工程实验一"
tar -czf studytask.tar.gz --exclude=.venv --exclude=.git --exclude=studytask.db --exclude=.pytest_cache --exclude=__pycache__ .
scp studytask.tar.gz admin@<服务器公网IP>:/tmp/
```

**2. 服务器上解压**

```bash
sudo mkdir -p /opt/studytask
sudo tar -xzf /tmp/studytask.tar.gz -C /opt/studytask
```

**3. 一键部署**

```bash
sudo bash deploy/setup.sh
```

脚本会依次完成：安装 python3-venv 与 nginx → 创建 `studytask` 运行用户 → 建虚拟环境并装依赖 → 生成随机 `SECRET_KEY` → 注册并启动 systemd 服务（gunicorn，监听 127.0.0.1:8000）→ 配置 Nginx 反代 80 端口。

**4. 验证**

```bash
systemctl status studytask
curl -I http://127.0.0.1
bash deploy/smoke_test.sh http://127.0.0.1     # 建任务→重启→校验持久化→清理数据
```

浏览器访问 `http://<服务器公网IP>` 即可。

### 本次部署实况

| 项 | 值 |
|---|---|
| 访问地址 | <http://120.76.59.189> |
| 服务器 | 腾讯云轻量应用服务器，Ubuntu 24.04.2 LTS，登录用户 `admin`（sudo 免密） |
| 项目路径 | `/opt/studytask` |
| 运行方式 | `studytask.service`（systemd）→ gunicorn 2 worker → `127.0.0.1:8000` → Nginx 反代 80 |
| 数据文件 | `/opt/studytask/studytask.db` |
| 部署时间 | 2026-11-13 |

部署后自检结果：首页 200、创建返回 302、列表可见、重启服务后数据仍在（T10）、删除后清理成功。

### 常用运维命令

```bash
sudo systemctl restart studytask     # 重启应用
sudo journalctl -u studytask -f      # 查看日志
sudo systemctl stop studytask        # 停止
```

### 关于备案

- 用 **公网 IP 直接访问**（`http://1.2.3.4`）通常无需备案；
- 绑定**域名**访问中国大陆服务器，必须先完成 ICP 备案（约 7~20 个工作日）；
- 想免备案用域名：选中国香港/新加坡地域的服务器。

### 更新代码

本机重新打包上传，然后在服务器上：

```bash
sudo tar -xzf /tmp/studytask.tar.gz -C /opt/studytask
sudo chown -R studytask:studytask /opt/studytask
sudo systemctl restart studytask
```

`studytask.db` 在 `/opt/studytask` 下，不会因为更新代码被覆盖（解压包中不含该文件）。

### 数据备份

```bash
sudo cp /opt/studytask/studytask.db /opt/studytask/studytask.db.$(date +%Y%m%d)
```

## 交付材料

| 材料 | 路径 | 说明 |
|---|---|---|
| 可运行源代码 | `app.py`、`db.py`、`templates/`、`static/` | Flask + SQLite 完整实现 |
| 依赖清单 | `requirements.txt`、`requirements-prod.txt` | 开发 / 生产（含 gunicorn） |
| 测试 | `tests/test_acceptance.py` | T1~T10 + 5 条回归，15 passed |
| 需求验收表 | `docs/需求验收表.docx` | T1~T10 手工验收截图 |
| AI 过程记录 | `docs/AI_DEV_LOG.md` | 提示词、问题定位、修复过程 |
| 实验报告 | `docs/实验报告.docx` | 3 页，含设计、问题、验收、部署 |
| 演示 PPT | `docs/演示PPT.pptx` | 10 页，现场演示用 |
| 部署脚本 | `deploy/` | setup.sh、systemd、nginx、自检脚本 |

## 已知限制

- 单用户本地使用，无登录与权限控制（符合 A.5 范围外约定）。
- 未做分页，任务量很大时列表会变长（200 条规模内操作正常）。
- 使用 Flask 开发服务器，仅适合本机演示。
