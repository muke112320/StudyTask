#!/usr/bin/env bash
# 部署后自检：访问 → 创建 → 列表可见 → 重启服务 → 持久化校验 → 删除清理
# 用法：bash deploy/smoke_test.sh [http://127.0.0.1]
set -euo pipefail

BASE=${1:-http://127.0.0.1}
NAME="部署自检任务"

echo "== 1. 首页 =="
curl -s -o /dev/null -w "GET / -> %{http_code}\n" "$BASE/"
if ! curl -s "$BASE/" | grep -q "StudyTask"; then
    echo "FAIL: 首页内容异常"; exit 1
fi

echo "== 2. 创建任务 =="
code=$(curl -s -o /dev/null -w '%{http_code}' \
    --data-urlencode "name=$NAME" \
    --data-urlencode "course=部署测试" \
    --data-urlencode "due_date=2026-12-01" \
    --data-urlencode "priority=中" \
    --data-urlencode "status=待完成" \
    --data-urlencode "description=部署完成后的自动自检" \
    "$BASE/tasks/new")
echo "POST /tasks/new -> $code"
[ "$code" = "302" ] || { echo "FAIL: 创建未跳转"; exit 1; }

echo "== 3. 列表可见 =="
BODY=$(curl -s "$BASE/")
echo "$BODY" | grep -q "$NAME" && echo "OK: 列表可见" || { echo "FAIL: 列表不可见"; exit 1; }

echo "== 4. 重启服务后仍存在（T10 持久化）=="
sudo systemctl restart studytask
sleep 3
for i in $(seq 1 10); do
    curl -s -o /dev/null "$BASE/" && break
    sleep 1
done
curl -s "$BASE/" | grep -q "$NAME" && echo "OK: 重启后数据仍在" || { echo "FAIL: 重启后数据丢失"; exit 1; }

echo "== 5. 清理自检数据 =="
TID=$(curl -s "$BASE/" | grep -o "tasks/[0-9]*/delete" | head -1 | grep -o "[0-9]*")
curl -s -o /dev/null -w "POST /tasks/$TID/delete -> %{http_code}\n" -X POST "$BASE/tasks/$TID/delete"
curl -s "$BASE/" | grep -q "$NAME" && { echo "FAIL: 未删除"; exit 1; } || echo "OK: 已清理"

echo
echo "自检通过 ✅"
