@echo off
chcp 65001 >nul
echo ============================================
echo    重点人员综合管控平台 - 启动脚本
echo ============================================
echo.

REM ---------- 启动后端 (5174) ----------
echo [1/2] 正在启动后端服务 (http://127.0.0.1:5174) ...
start "后端服务" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 5174"

set /a _tries=0
echo 正在等待后端就绪（健康检查）...
:wait_backend
set /a _tries+=1
if %_tries% geq 60 goto backend_timeout
timeout /t 1 /nobreak >nul
curl -s -o nul http://127.0.0.1:5174/api/health
if errorlevel 1 goto wait_backend
echo     后端已就绪 (http://127.0.0.1:5174/api/health) OK
goto backend_started

:backend_timeout
echo.
echo [错误] 后端启动超时。请查看"后端服务"窗口的报错信息：
echo         - 依赖是否已安装 (.venv\Scripts\pip install -r requirements.txt)
echo         - MySQL 是否可连（设置页可测；连接失败会回退 SQLite）
echo         - 端口 5174 是否被占用
pause
exit /b 1

:backend_started
REM ---------- 启动前端 (5173) ----------
echo [2/2] 正在启动前端服务 (http://127.0.0.1:5173) ...
start "前端服务" cmd /k "cd /d %~dp0frontend && npm run dev"

set /a _tries=0
echo 正在等待前端就绪...
:wait_frontend
set /a _tries+=1
if %_tries% geq 120 goto frontend_timeout
timeout /t 1 /nobreak >nul
curl -s -o nul http://127.0.0.1:5173/
if errorlevel 1 goto wait_frontend
goto frontend_started

:frontend_timeout
echo.
echo [警告] 前端启动较慢（或已就绪）。如需访问： http://127.0.0.1:5173
start http://127.0.0.1:5173
pause
exit /b 0

:frontend_started
echo     前端已就绪 (http://127.0.0.1:5173)

echo.
echo 启动完成，正在打开大屏页面...
start http://127.0.0.1:5173

echo.
echo 如未自动打开，请手动访问 http://127.0.0.1:5173
echo 关闭本窗口即可退出（不影响已启动的前后端窗口）。
pause