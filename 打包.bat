@echo off
chcp 65001 >nul
cls
echo ================================================================================
echo 快报填写程序 - 打包脚本 v3.0
echo ================================================================================
echo.

echo [1/5] 检查环境...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo     正在安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo     错误: 安装失败
        pause
        exit /b 1
    )
)
echo     ✓ PyInstaller已安装

if exist "icon.ico" (
    echo     ✓ 发现icon.ico
) else (
    echo     ℹ 未发现icon.ico（将使用默认图标）
)

if not exist "快报填写程序.spec" (
    echo     ✗ 未找到spec文件
    pause
    exit /b 1
)
echo     ✓ spec文件存在
echo.

echo [2/5] 清理缓存...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist __pycache__ rmdir /s /q __pycache__ 2>nul
if exist "%LOCALAPPDATA%\pyinstaller" rmdir /s /q "%LOCALAPPDATA%\pyinstaller" 2>nul
echo     ✓ 缓存已清理
echo.

echo [3/5] 开始打包...
echo     预计需要5-10分钟
echo     控制台会显示大量信息，这是正常的
echo.
pyinstaller --clean 快报填写程序.spec
if errorlevel 1 (
    echo.
    echo ✗ 打包失败
    pause
    exit /b 1
)
echo.
echo     ✓ 打包完成
echo.

echo [4/5] 整理发布文件...
if not exist "dist\快报填写程序_发布" mkdir "dist\快报填写程序_发布"

if not exist "dist\快报填写程序.exe" (
    echo     ✗ 未找到exe
    pause
    exit /b 1
)

copy /y "dist\快报填写程序.exe" "dist\快报填写程序_发布\" >nul
if exist "config" xcopy /E /I /Y "config" "dist\快报填写程序_发布\config\" >nul
if exist "Fomular" xcopy /E /I /Y "Fomular" "dist\快报填写程序_发布\Fomular\" >nul
if exist "icon.ico" copy /y "icon.ico" "dist\快报填写程序_发布\" >nul
if not exist "dist\快报填写程序_发布\data\chat" mkdir "dist\快报填写程序_发布\data\chat"
echo     ✓ 文件已整理
echo.

echo [5/5] 刷新图标缓存...
ie4uinit.exe -show >nul 2>&1
echo     ✓ 图标缓存已刷新
echo.

echo ================================================================================
echo 打包完成！
echo ================================================================================
echo.
echo 📂 发布位置: dist\快报填写程序_发布\
echo.
echo 📋 文件列表:
dir /b "dist\快报填写程序_发布\" 2>nul
echo.

if exist "icon.ico" (
    echo ✅ 已使用自定义图标
    echo.
    echo 💡 如果图标不显示:
    echo    1. 打开资源管理器，切换到"大图标"或"超大图标"视图
    echo    2. 按F5刷新，或重启资源管理器
    echo    3. 运行: ie4uinit.exe -show
    echo    4. 或重启电脑
    echo.
    echo    注意: 这是Windows图标缓存问题，不是打包问题
    echo           图标已正确嵌入exe，只是Windows显示有延迟
    echo.
)

echo 📦 下一步:
echo    1. 测试exe: cd dist\快报填写程序_发布
echo    2. 运行程序: 快报填写程序.exe
echo    3. 压缩文件夹分发
echo.
pause
