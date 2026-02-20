@echo off
echo =========================================
echo  KeywordSearchTool v1.0 Windows 打包程序
echo =========================================

echo 1. 检查并安装打包所需依赖 (确保您已经安装了 Python)...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo 2. 开始构建 Windows 可执行文件 (EXE)...
echo (打包过程可能需要几分钟，请耐心等待...)
pyinstaller -w -F -y --name "KeywordSearchTool_v1.0" main.py

echo.
echo 3. 清理临时构建目录...
rmdir /s /q build
del /q KeywordSearchTool_v1.0.spec

echo.
echo =========================================
echo 打包完成！
echo 您的 EXE 文件已生成在 .\dist\KeywordSearchTool_v1.0.exe
echo =========================================
pause
