"""StudyTask 个人学习任务管理系统 —— Flask 路由层。

启动：
    python app.py
测试：
    pytest -v
"""
from __future__ import annotations

from pathlib import Path

from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)

import db

BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="studytask-local-secret-key",
        DATABASE=str(BASE_DIR / "studytask.db"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # ------------------------------------------------------------ 首页 / 列表
    @app.route("/")
    def index():
        course = request.args.get("course", "").strip()
        status = request.args.get("status", "").strip()
        priority = request.args.get("priority", "").strip()

        tasks = db.list_tasks(course or None, status or None, priority or None)
        return render_template(
            "index.html",
            tasks=db.decorate(tasks),
            stats=db.stats(),
            courses=db.all_courses(),
            filters={"course": course, "status": status, "priority": priority},
            priorities=db.PRIORITIES,
            statuses=db.STATUSES,
            is_filtered=bool(course or status or priority),
        )

    # ------------------------------------------------------------ 新建任务
    @app.route("/tasks/new", methods=["GET", "POST"])
    def task_new():
        if request.method == "POST":
            data, errors = db.validate_task(request.form)
            if errors:
                return render_template(
                    "form.html", mode="new", task=dict(request.form),
                    errors=errors, priorities=db.PRIORITIES,
                    statuses=db.STATUSES,
                ), 400

            task_id = db.create_task(data)
            flash("任务创建成功", "success")
            return redirect(url_for("task_detail", task_id=task_id))

        return render_template(
            "form.html", mode="new", task={}, errors={},
            priorities=db.PRIORITIES, statuses=db.STATUSES,
        )

    # ------------------------------------------------------------ 详情
    @app.route("/tasks/<int:task_id>")
    def task_detail(task_id: int):
        task = db.get_task(task_id)
        if task is None:
            abort(404)
        item = db.decorate([task])[0]
        return render_template("detail.html", task=item, statuses=db.STATUSES)

    # ------------------------------------------------------------ 编辑
    @app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
    def task_edit(task_id: int):
        task = db.get_task(task_id)
        if task is None:
            abort(404)

        if request.method == "POST":
            data, errors = db.validate_task(request.form)
            if errors:
                return render_template(
                    "form.html", mode="edit", task=dict(request.form),
                    errors=errors, priorities=db.PRIORITIES,
                    statuses=db.STATUSES, task_id=task_id,
                ), 400

            db.update_task(task_id, data)
            flash("任务已更新", "success")
            return redirect(url_for("task_detail", task_id=task_id))

        return render_template(
            "form.html", mode="edit", task=db.row_to_dict(task), errors={},
            priorities=db.PRIORITIES, statuses=db.STATUSES, task_id=task_id,
        )

    # ------------------------------------------------------------ 删除
    @app.route("/tasks/<int:task_id>/delete", methods=["POST"])
    def task_delete(task_id: int):
        if db.get_task(task_id) is None:
            abort(404)
        db.delete_task(task_id)
        flash("任务已删除", "success")
        return redirect(url_for("index"))

    # ------------------------------------------------------------ 状态流转
    @app.route("/tasks/<int:task_id>/status", methods=["POST"])
    def task_status(task_id: int):
        if db.get_task(task_id) is None:
            abort(404)

        new_status = (request.form.get("status") or "").strip()
        if new_status not in db.STATUSES:
            flash("无效的任务状态", "error")
            return redirect(url_for("task_detail", task_id=task_id))

        db.set_status(task_id, new_status)
        flash(f"状态已更新为「{new_status}」", "success")
        return redirect(url_for("task_detail", task_id=task_id))

    # ------------------------------------------------------------ 错误页
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
