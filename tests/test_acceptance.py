"""StudyTask 验收自动化测试（对应手册 2.5 节 T1~T10）。

运行：
    pytest -v
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import pytest

import db as dbmod
from app import create_app


# ------------------------------------------------------------------ 夹具

@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": str(tmp_path / "test.db"),
    })


@pytest.fixture
def client(app):
    return app.test_client()


# ------------------------------------------------------------------ 辅助

def add(client, name="数据结构作业", course="数据结构", due=None,
        priority="中", status="待完成", description=""):
    """通过真实 HTTP 表单创建任务，返回响应。"""
    due = due or (date.today() + timedelta(days=7)).isoformat()
    return client.post("/tasks/new", data={
        "name": name, "course": course, "due_date": due,
        "priority": priority, "status": status, "description": description,
    }, follow_redirects=False)


def count(app) -> int:
    with app.app_context():
        return dbmod.get_db().execute("SELECT COUNT(*) FROM tasks").fetchone()[0]


def fetch(app, task_id: int):
    with app.app_context():
        return dbmod.get_task(task_id)


# ------------------------------------------------------------------ T1

def test_t1_create_task_and_show_in_list(client, app):
    resp = add(client, name="数据结构第三章作业", course="数据结构",
               due=(date.today() + timedelta(days=1)).isoformat(), priority="高")
    assert resp.status_code == 302

    page = client.get("/")
    assert page.status_code == 200
    assert "数据结构第三章作业" in page.get_data(as_text=True)
    assert count(app) == 1


# ------------------------------------------------------------------ T2

def test_t2_empty_name_rejected(client, app):
    resp = client.post("/tasks/new", data={
        "name": "   ", "course": "数据结构",
        "due_date": (date.today() + timedelta(days=1)).isoformat(),
        "priority": "中", "status": "待完成",
    }, follow_redirects=True)
    assert resp.status_code == 400
    assert "任务名称不能为空" in resp.get_data(as_text=True)
    assert count(app) == 0          # 不产生脏数据


# ------------------------------------------------------------------ T3

def test_t3_edit_persists(client, app):
    add(client, name="原名称")
    with app.app_context():
        task_id = dbmod.list_tasks()[0]["id"]

    resp = client.post(f"/tasks/{task_id}/edit", data={
        "name": "改后的名称", "course": "数据结构",
        "due_date": (date.today() + timedelta(days=2)).isoformat(),
        "priority": "低", "status": "进行中",
        "description": "新的描述内容",
    }, follow_redirects=True)
    assert resp.status_code == 200

    page = client.get("/").get_data(as_text=True)   # 刷新列表
    assert "改后的名称" in page

    row = fetch(app, task_id)                        # 直查数据库确认落库
    assert row["priority"] == "低"
    assert row["description"] == "新的描述内容"


# ------------------------------------------------------------------ T4

def test_t4_status_progress(client, app):
    add(client)
    with app.app_context():
        task_id = dbmod.list_tasks()[0]["id"]

    for expected in ("进行中", "已完成"):
        client.post(f"/tasks/{task_id}/status",
                    data={"status": expected}, follow_redirects=True)
        assert fetch(app, task_id)["status"] == expected


# ------------------------------------------------------------------ T5

def test_t5_filters(client, app):
    add(client, name="甲任务", course="数据结构", status="待完成", priority="高")
    add(client, name="乙任务", course="数据结构", status="已完成", priority="高")
    add(client, name="丙任务", course="操作系统", status="待完成", priority="低")

    page = client.get("/?course=数据结构").get_data(as_text=True)
    assert "甲任务" in page and "乙任务" in page and "丙任务" not in page

    page = client.get("/?course=数据结构&status=已完成").get_data(as_text=True)
    assert "乙任务" in page and "甲任务" not in page

    page = client.get("/?priority=低").get_data(as_text=True)
    assert "丙任务" in page and "甲任务" not in page


# ------------------------------------------------------------------ T6 / T7

def test_t6_overdue(client, app):
    add(client, name="逾期任务", due=(date.today() - timedelta(days=1)).isoformat())
    page = client.get("/").get_data(as_text=True)
    assert "逾期任务" in page
    assert "逾期" in page


def test_t7_due_soon(client, app):
    add(client, name="明天到期任务", due=(date.today() + timedelta(days=1)).isoformat())
    page = client.get("/").get_data(as_text=True)
    assert "即将到期" in page


def test_completed_task_has_no_overdue_badge(client, app):
    add(client, name="已完成的过期任务", status="已完成",
        due=(date.today() - timedelta(days=5)).isoformat())
    page = client.get("/").get_data(as_text=True)
    assert "已完成的过期任务" in page
    assert 'class="badge badge-overdue"' not in page


# ------------------------------------------------------------------ T8

def test_t8_statistics(client, app):
    for i in range(5):
        add(client, name=f"任务{i}")
    with app.app_context():
        ids = [r["id"] for r in dbmod.list_tasks()]
        for tid in ids[:2]:
            dbmod.set_status(tid, "已完成")
        stats = dbmod.stats()

    assert stats["total"] == 5
    assert stats["done"] == 2
    assert stats["rate"] == 40.0

    page = client.get("/").get_data(as_text=True)
    assert "40%" in page


def test_stats_zero_tasks(client, app):
    with app.app_context():
        assert dbmod.stats() == {"total": 0, "done": 0, "rate": 0.0}
    assert "0%" in client.get("/").get_data(as_text=True)


# ------------------------------------------------------------------ T9

def test_t9_delete_requires_post(client, app):
    add(client, name="待删除任务")
    with app.app_context():
        task_id = dbmod.list_tasks()[0]["id"]

    # 取消 = 没有发出 POST，数据必须还在；GET 也不能删
    assert client.get(f"/tasks/{task_id}/delete").status_code == 405
    assert fetch(app, task_id) is not None

    # 确认 = POST，删除生效
    resp = client.post(f"/tasks/{task_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert fetch(app, task_id) is None
    assert count(app) == 0


# ------------------------------------------------------------------ T10

def test_t10_data_survives_restart(tmp_path):
    db_file = str(tmp_path / "restart.db")

    first = create_app({"TESTING": True, "DATABASE": db_file, "SECRET_KEY": "t"})
    c1 = first.test_client()
    c1.post("/tasks/new", data={
        "name": "重启后仍存在", "course": "数据结构",
        "due_date": (date.today() + timedelta(days=3)).isoformat(),
        "priority": "中", "status": "待完成",
    }, follow_redirects=True)

    # 模拟“关闭并重新启动应用”：重新创建 app 实例，复用同一个数据库文件
    second = create_app({"TESTING": True, "DATABASE": db_file, "SECRET_KEY": "t"})
    page = second.test_client().get("/").get_data(as_text=True)
    assert "重启后仍存在" in page


# ------------------------------------------------------------------ 其他校验

def test_invalid_date_rejected(client, app):
    resp = client.post("/tasks/new", data={
        "name": "日期非法", "course": "数据结构",
        "due_date": "2026-13-45", "priority": "中", "status": "待完成",
    }, follow_redirects=True)
    assert resp.status_code == 400
    assert "截止日期格式应为" in resp.get_data(as_text=True)
    assert count(app) == 0


def test_detail_404(client):
    assert client.get("/tasks/9999").status_code == 404


def test_list_order_by_due_date(client, app):
    add(client, name="后到期", due=(date.today() + timedelta(days=9)).isoformat())
    add(client, name="先到期", due=(date.today() + timedelta(days=2)).isoformat())
    page = client.get("/").get_data(as_text=True)
    assert page.index("先到期") < page.index("后到期")
