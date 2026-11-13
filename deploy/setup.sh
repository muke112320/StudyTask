#!/usr/bin/env bash
# StudyTask 一键部署脚本（Ubuntu 22.04 / 24.04）
#
# 前置条件：项目代码已上传到 /opt/studytask（见 README「部署到云服务器」）
# 用法：sudo bash deploy/setup.sh
set -euo pipefail

APP_DIR=/opt/studytask
SERVICE=studytask
PIP_INDEX=https://mirrors.aliyun.com/pypi/simple/

echo "==> 1/6 安装系统依赖"
apt-get update -y
apt-get install -y python3-venv python3-pip nginx

echo "==> 2/6 创建运行用户"
if ! id -u studytask >/dev/null 2>&1; then
    useradd --system --create-home --home-dir "$APP_DIR" --shell /usr/sbin/nologin studytask
fi
mkdir -p "$APP_DIR"
chown -R studytask:studytask "$APP_DIR"

echo "==> 3/6 创建虚拟环境并安装依赖"
sudo -u studytask python3 -m venv "$APP_DIR/.venv"
sudo -u studytask "$APP_DIR/.venv/bin/pip" install -q --upgrade pip
sudo -u studytask "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements-prod.txt" -i "$PIP_INDEX"

echo "==> 4/6 安装并启动 systemd 服务"
# 若用户没改过 SECRET_KEY，生成一个随机的
if grep -q "请替换为随机字符串" "$APP_DIR/deploy/studytask.service"; then
    SECRET=$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 40)
    sed -i "s|STUDYTASK_SECRET=请替换为随机字符串|STUDYTASK_SECRET=$SECRET|" "$APP_DIR/deploy/studytask.service"
    echo "    已生成随机 SECRET_KEY"
fi
cp "$APP_DIR/deploy/studytask.service" "/etc/systemd/system/$SERVICE.service"
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

echo "==> 5/6 配置 Nginx 反向代理"
cp "$APP_DIR/deploy/nginx-studytask.conf" /etc/nginx/sites-available/studytask
ln -sf /etc/nginx/sites-available/studytask /etc/nginx/sites-enabled/studytask
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "==> 6/6 防火墙（如启用 ufw）"
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo "    ufw 已放行 22/80/443"
else
    echo "    ufw 未启用，跳过"
fi

echo
echo "完成。检查状态："
echo "  systemctl status $SERVICE"
echo "  curl -I http://127.0.0.1"
echo "浏览器访问：http://<服务器公网IP>"
