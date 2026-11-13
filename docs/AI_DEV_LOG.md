# AI 开发过程记录（AI_DEV_LOG）

> 用途：记录“人给 AI 下达了什么任务、AI 产出了什么、人做了什么判断、出了什么问题、怎么修好的”。
> 评分项「AI 使用与过程记录」25 分，主要看这份文件，**不要写成流水账**。

## 记录模板

```
### [日期] 任务标题
- 我下达的任务：
- AI 的产出：
- 我的判断 / 修改：
- 问题与修复：
- 证据（截图、提交号）：
```

---

## 记录 1 · 2026-11-13 环境搭建：pip 安装依赖失败

- **我下达的任务**：在桌面新建 `软件工程实验一` 工作区，初始化 Git 与 Python 虚拟环境，安装 Flask、pytest。
- **AI 的产出**：创建 `.venv`，执行 `pip install flask pytest`。
- **现象**：报错
  ```
  ERROR: Could not find a version that satisfies the requirement flask (from versions: none)
  ERROR: No matching distribution found for flask
  ```
- **定位过程**：让 AI 用 `pip download -vvv` 打印详细日志，发现真正原因是
  `GET /simple/flask/ HTTP/1.1" 403 None`，即**清华镜像对 pip 的请求返回 403**。
  再用 `Invoke-WebRequest` 测试，镜像本身可访问（200），说明是 UA/风控拦截而非断网。
- **修复**：在 `.venv\pip.ini` 中把索引改为阿里云镜像 `https://mirrors.aliyun.com/pypi/simple/`，
  重装成功（flask 3.1.3、pytest 9.2.0）。未改动全局 pip 配置。
- **我的判断**：索引属于环境问题，不应写进业务代码；把它记入 README 的「网络提示」。

## 记录 2 · 2026-11-13 自动化测试 T5 误报

- **我下达的任务**：按附录 A 实现功能，并写覆盖 T1~T10 的 pytest 用例。
- **现象**：首次运行 `pytest` 时 T5 失败：
  `assert 'C' not in page` 不成立，但数据库里确实只应有 A、B 两条任务。
- **定位过程**：失败信息里 pytest 打印出了页面片段，发现页面 `<html lang="zh-CN">` 中含有字母 `C`。
  原来测试用 `A/B/C` 作为任务名，**断言字符串与 HTML 源码撞车**，是测试用例的缺陷，不是功能缺陷。
- **修复**：把任务名改为 `甲任务 / 乙任务 / 丙任务` 这类不会出现在页面骨架里的中文名，重跑通过。
- **我的判断**：断言页面内容时要选“只可能来自数据本身”的字符串，避免与模板/属性值冲突。

---

## 记录 3 · （待你补充：手工验收中发现的问题）

- **我下达的任务**：
- **现象 / 复现步骤**：
- **AI 输出中的错误信息**：
- **修复与复测结果**：
