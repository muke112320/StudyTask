"""StudyTask 数据访问层：SQLite 建库、字段校验、增删改查、统计。

设计说明（本模块只关心“数据”，不关心页面）：
- 所有输入先经过 validate_task() 清洗与校验，路由层不重复写规则；
- 逾期/即将到期属于“展示派生信息”，在 decorate() 里按当前日期实时计算，
  不写入数据库，避免日期过期后数据不一致。
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import current_app, g

# ---------------------------------------------------------------- 常量

PRIORITIES = ("高", "中", "低")
STATUSES = ("待完成", "进行中", "已完成")
DONE = "已完成"
DEFAULT_PRIORITY = "中"
DEFAULT_STATUS = "待完成"

NAME_MAX = 100
COURSE_MAX = 60
DESC_MAX = 1000
SOON_DAYS = 3          # FR-07：今日起未来 3 天内到期 = 即将到期

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    course      TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    due_date    TEXT NOT NULL,                     -- YYYY-MM-DD
    priority    TEXT NOT NULL DEFAULT '中',
    status      TEXT NOT NULL DEFAULT '待完成',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_filter ON tasks (course, status, priority);
"""

# ---------------------------------------------------------------- 连接管理


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    get_db().executescript(SCHEMA)
    get_db().commit()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()


# ---------------------------------------------------------------- 工具


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def row_to_dict(row) -> dict:
    return dict(row) if row is not None else {}


def parse_date(text: str) -> date | None:
    """严格按 YYYY-MM-DD 解析，失败返回 None。"""
    if not text or not _DATE_RE.match(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


# ---------------------------------------------------------------- 校验


def validate_task(form) -> tuple[dict, dict]:
    """校验表单并返回 (清洗后的数据, 错误字典)。

    错误字典为空表示通过。错误键与表单字段同名，便于模板回填。
    """
    name = (form.get("name") or "").strip()
    course = (form.get("course") or "").strip()
    description = (form.get("description") or "").strip()
    due_text = (form.get("due_date") or "").strip()
    priority = (form.get("priority") or DEFAULT_PRIORITY).strip()
    status = (form.get("status") or DEFAULT_STATUS).strip()

    errors: dict[str, str] = {}

    if not name:
        errors["name"] = "任务名称不能为空"
    elif len(name) > NAME_MAX:
        errors["name"] = f"任务名称不能超过 {NAME_MAX} 字"

    if not course:
        errors["course"] = "所属课程不能为空"
    elif len(course) > COURSE_MAX:
        errors["course"] = f"所属课程不能超过 {COURSE_MAX} 字"

    if len(description) > DESC_MAX:
        errors["description"] = f"任务描述不能超过 {DESC_MAX} 字"

    due = parse_date(due_text)
    if not due_text:
        errors["due_date"] = "截止日期不能为空"
    elif due is None:
        errors["due_date"] = "截止日期格式应为 YYYY-MM-DD"

    if priority not in PRIORITIES:
        errors["priority"] = "优先级只能为 高 / 中 / 低"

    if status not in STATUSES:
        errors["status"] = "状态只能为 待完成 / 进行中 / 已完成"

    data = {
        "name": name,
        "course": course,
        "description": description,
        "due_date": due.isoformat() if due else due_text,
        "priority": priority,
        "status": status,
    }
    return data, errors


# ---------------------------------------------------------------- CRUD


def create_task(data: dict) -> int:
    now = _now()
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO tasks (name, course, description, due_date,
                              priority, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (data["name"], data["course"], data["description"], data["due_date"],
         data["priority"], data["status"], now, now),
    )
    conn.commit()
    return int(cur.lastrowid)


def update_task(task_id: int, data: dict) -> None:
    conn = get_db()
    conn.execute(
        """UPDATE tasks SET name = ?, course = ?, description = ?, due_date = ?,
                            priority = ?, status = ?, updated_at = ?
           WHERE id = ?""",
        (data["name"], data["course"], data["description"], data["due_date"],
         data["priority"], data["status"], _now(), task_id),
    )
    conn.commit()


def delete_task(task_id: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()


def set_status(task_id: int, status: str) -> None:
    conn = get_db()
    conn.execute(
        "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
        (status, _now(), task_id),
    )
    conn.commit()


def get_task(task_id: int):
    return get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def list_tasks(course=None, status=None, priority=None) -> list:
    """按课程 / 状态 / 优先级筛选，条件可组合，空值表示不筛选。"""
    sql = "SELECT * FROM tasks"
    where, params = [], []
    if course:
        where.append("course = ?")
        params.append(course)
    if status:
        where.append("status = ?")
        params.append(status)
    if priority:
        where.append("priority = ?")
        params.append(priority)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY due_date ASC, id ASC"
    return get_db().execute(sql, params).fetchall()


def all_courses() -> list[str]:
    rows = get_db().execute(
        "SELECT DISTINCT course FROM tasks ORDER BY course"
    ).fetchall()
    return [r["course"] for r in rows]


# ---------------------------------------------------------------- 统计与展示


def stats() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    done = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status = ?", (DONE,)
    ).fetchone()[0]
    rate = round(done / total * 100, 1) if total else 0.0
    return {"total": total, "done": done, "rate": rate}


def decorate(tasks) -> list[dict]:
    """给每条任务补充 逾期 / 即将到期 标记（FR-07）。已完成任务不再提醒。"""
    today = date.today()
    soon_limit = today + timedelta(days=SOON_DAYS)
    result = []
    for row in tasks:
        item = dict(row)
        badge, badge_class = "", ""
        due = date.fromisoformat(item["due_date"])
        if item["status"] != DONE:
            if due < today:
                badge, badge_class = "逾期", "badge-overdue"
            elif today <= due <= soon_limit:
                badge, badge_class = "即将到期", "badge-soon"
        item["badge"] = badge
        item["badge_class"] = badge_class
        result.append(item)
    return result


def db_path(app) -> Path:
    return Path(app.config["DATABASE"])
