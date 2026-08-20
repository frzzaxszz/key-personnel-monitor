@echo off
chcp 65001 >nul
echo ============================================
echo    重点人员综合管控平台 - 启动脚本
echo ============================================
echo.

REM 启动后端
echo [1/2] 正在启动后端服务 (http://127.0.0.1:8000) ...
start "后端服务" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

REM 启动前端
echo [2/2] 正在启动前端服务 (http://127.0.0.1:5173) ...
start "前端服务" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 3 /nobreak >nul
start http://127.0.0.1:5173

echo.
echo 启动完成，浏览器将自动打开大屏页面。
echo 如未自动打开，请手动访问 http://127.0.0.1:5173
pause
