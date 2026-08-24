# AGENTS.md — 项目代理操作指南

本文件是供 AI 代理（以及后续开发者）在本仓库内工作时的约定与操作说明。请在改动或排查问题前先阅读。

## 项目一句话

重点人员综合管控大屏：后端 FastAPI + MySQL/SQLite，前端 Vue3 + Vite + ECharts，中央中国地图热力/打点，两侧与下方多图表联动钻取。

## 技术栈

- 后端：Python 3.7+（实际 `.venv` 为 3.14）、FastAPI、SQLAlchemy 2.0、openpyxl、PyMySQL
- 前端：Vue 3（Composition API）、Vite、ECharts（注册中国地图 `china.json`）、vue-router（hash 模式）、axios
- 数据库：默认 MySQL（连接信息在 `backend/data/db_config.json`），连接失败回退 SQLite（`backend/data/app.db`）

## 目录结构

```
e:\大屏\
├─ 启动系统.bat          # 一键启动（后端 5174 + 前端 5173）
├─ backend\
│  ├─ main.py            # FastAPI 入口、lifespan 建库/种子、实时动态后台任务
│  ├─ config.py          # DATA_DIR/UPLOAD_DIR、MySQL 配置持久化(json)
│  ├─ database.py        # 引擎/会话，运行时切换 MySQL/SQLite
│  ├─ models.py          # Person/VisitRecord/AlertRecord/ImportLog/DBSettings
│  ├─ seed.py            # 5000 条模拟数据生成（31 省随机分布）
│  ├─ sync_service.py    # 实时动态/预警后台生成 + MySQL 建库
│  ├─ schemas.py         # Pydantic 模型
│  ├─ routers\
│  │  ├─ dashboard.py    # /api/dashboard/summary、/map（聚合 + 过滤 + 钻取）
│  │  ├─ persons.py      # /api/persons CRUD + 照片上传 + 走访
│  │  ├─ import_export.py# /api/import Excel 按表头导入/导出/日志
│  │  └─ settings.py     # /api/settings 数据库连接 + reseed/drop
│  └─ requirements.txt
└─ frontend\
   └─ src\
      ├─ api\index.js    # axios 封装
      ├─ router\index.js # 路由表
      ├─ assets\geo\china.json
      ├─ components\BaseChart.vue
      ├─ styles\main.css
      └─ views\{Dashboard,PersonList,PersonDetail,ImportData,Settings}.vue
```

## 常用命令

- 一键启动：双击「启动系统.bat」（后端 `http://127.0.0.1:5174`，前端 `http://127.0.0.1:5173`）
- 仅后端：`cd backend && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 5174`
- 仅前端：`cd frontend && npm run dev`

> 注意：`uvicorn` **未开启 `--reload`**。修改后端代码后必须手动重启后端进程才能生效。

## 关键约定与易错点（务必遵守）

1. **后端改代码必须重启**：无 `--reload`。改了 `routers/*.py`、`models.py` 等后，停掉 5174 端口进程再启动。
2. **地图图层必须单一 geo**：热力/区域着色与打点必须挂在**同一个 `geo`** 组件上，否则滚轮缩放时两层错位不重合。
3. **地图坐标字段访问**：SQLAlchemy 行对象在 `mapOption` 里是 dict（`mapData.points`），必须用 `p["longitude"]` 方括号访问；用点号 `p.longitude` 会抛 AttributeError（历史 bug）。
4. **Excel 导入按表头映射**，不是固定列序：
   - 必填列：`姓名`、`身份证号`（缺失则 400 报错）
   - 可选字段缺失时用 `FIELD_DEFAULTS` 默认值并返回 `warnings`
   - 督办身份证号去重（重复行计入 failed）
5. **汇总/地图接口的过滤参数**：`district`、`category`、`status`、`risk`（过滤人员）、`alert_type`（过滤预警链路）。所有图表联动都通过 `refreshAll()` 把这些参数一起传给后端，勿只传其中一两个。
6. **图表联动**：左/中/下各图点击事件绑定到 `Dashboard.vue` 的 `onXxxClick` 处理器，设置 `filters` 后调用 `refreshAll()`。饼图判 `params.seriesType === 'pie'`。时间维度图（近7日趋势等）点击仅 `onTimeClick` 提示，不触发过滤。
7. **MySQL 连接**：字段为 host/port/database/username/password，存在 `backend/data/db_config.json`。测试连接成功后全局引擎切 MySQL 并 `create_all`（`settings/db/test`），MySQL 库不存在时 `ensure_mysql_database` 自建。
8. **种子数据**：默认 `SEED_COUNT = 5000` 启动时生成；`POST /api/settings/reseed?count=N` 清空重建；`POST /api/settings/drop` 仅清空业务数据。Idempotent：`seed_demo` 在 `force=False` 且已有数据时跳过。

## 前端基础

- 图表统一用 `components/BaseChart.vue`，通过 `:option` 传 ECharts 配置，`:on-events="{ click: handler }"` 绑定点击。
- ECharts 全局注册了 `china`（`assets/geo/china.json`）。
- 主题变量在 `styles/main.css`（`--text-dim`、`--accent-*` 等），新图表配色优先复用。
- 页面为深色大屏风，背景 `main.css` 指定；居中对齐、绝对定位浮层（如地图上的筛选条）注意与地图同背景层。

## 验证清单（大屏核心链路）

1. `GET /api/health` → `{"status":"ok"}`
2. `GET /api/dashboard/summary` → 含 `total / high_risk / today_new / control_rate / pending_alerts / risk_data / monthly_trend / alert_type_data` 等；新版含 `yesterday_new / today_alerts / yesterday_alerts`
3. `GET /api/dashboard/map` → 含 `districts`（按省聚合）与 `points`（带 `longitude/latitude/risk_level/name`）
4. 过滤钻取：`/api/dashboard/summary?district=广东省&category=涉毒人员&risk=高` 应联动各图表与顶部 KPI
5. Excel：上传后返回 `{total, success, failed, errors, warnings}`
6. MySQL：`POST /api/settings/db/test` 成功后重启仍保持（读 `db_config.json`）

## 环境限制（重要）

- 本机 PowerShell 脚本执行策略可能被禁用，直接执行命令会报 `UnauthorizedAccess`。若命令行工具不可用，需先由人在外部执行：
  `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force`
- 浏览器验证优先使用 Vite 开发服务器（5173）并检查控制台无报错。
