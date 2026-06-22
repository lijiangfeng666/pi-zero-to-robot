@echo off
REM ================================================
REM pi-zero-to-robot 推送仓库到 GitHub
REM 在 Windows 上双击运行（需要 Git 已安装）
REM ================================================

echo 正在复制仓库到桌面...
xcopy /E /I /Y \\wsl.localhost\Ubuntu\home\lijiangfeng1314\pi-zero-to-robot %USERPROFILE%\Desktop\pi-zero-to-robot\

echo.
echo 仓库已复制到桌面：%USERPROFILE%\Desktop\pi-zero-to-robot\
echo.
echo 下一步（手动操作）：
echo 1. 打开 cmd 或 PowerShell
echo 2. cd %USERPROFILE%\Desktop\pi-zero-to-robot
echo 3. git remote set-url origin https://github.com/lijiangfeng666/pi-zero-to-robot.git
echo 4. git push -u origin main
echo.

pause
