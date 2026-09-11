@echo off
chcp 65001 >nul
setlocal

if "%~1"=="" (
  echo 请把 Minecraft Java 版结构文件 .nbt 拖到这个批处理文件上。
  echo.
  pause
  exit /b 1
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0nbt_structure_to_json.py" "%~1" --html --open
  goto finish
)

where python >nul 2>nul
if not errorlevel 1 (
  python "%~dp0nbt_structure_to_json.py" "%~1" --html --open
  goto finish
)

echo 没有找到 Python 3。请先从 https://www.python.org/downloads/ 安装，安装时勾选 Add Python to PATH。

:finish
if errorlevel 1 (
  echo.
  echo 生成失败，请把上面的报错截图发给文件提供者。
)
echo.
pause
