# 快速部署与打包指南 (DEPLOYMENT)

## 1. 结论
本文档指导如何安装依赖并在目标环境（包括 macOS 和 Windows）中打包生成独立运行的安装程序(`.dmg` 或 `.exe`)。

## 2. 范围/假设
假设您在本地机器已经安装了 Python (建议版本 >= 3.9) 并且身处相应的操作系统。如果您需要 Mac 版，请在 Mac 下构建；如果您需要 Windows 版，请在 Windows 下构建。

## 3. 设计要点
- 使用 `PyInstaller` 将 Python 代码与 `PyQt6`、`pdfplumber`、`openai` 依赖库集成构建。
- macOS 下使用 `hdiutil` 将 `.app` 打包为 `.dmg`。

## 4. 施工步骤 (macOS DMG 打包流程)

1. **执行自动化打包脚本**：
   在 Mac 终端中进入项目根目录并执行提供的脚本：
   ```bash
   cd /Users/duobaobao/keyword
   chmod +x build_mac.sh
   ./build_mac.sh
   ```
2. **获取产物**：
   打包完成后，前往 `dist/` 文件夹即可获取生成的 `KeywordSearchTool.dmg`。双击即可挂载并将应用拖入 Applications 文件夹。

## 4.1 施工步骤 (Windows EXE 打包流程)

1. **准备环境与进入项目**：
   在 Windows 命令行 (Command Prompt / PowerShell) 中执行：
   ```bash
   cd /path/to/keyword
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. **执行打包指令**：
   为避免黑框控制台弹出，且以单文件分发，执行：
   ```bash
   pyinstaller -w -F --name "KeywordSearchTool" main.py
   ```
   *(注：如果您觉得单文件打开速度慢，可去除 `-F` 标签变为目录形式分发)*

3. **获取产物**：
   打包完成后，前往 `dist/` 文件夹即可获取到生成的 `KeywordSearchTool.exe`，直接双击运行测试。

## 5. 验收标准
1. `dist` 文件夹内成功生成 `KeywordSearchTool.dmg` (Mac) 或 `KeywordSearchTool.exe` (Windows)。
2. 程序启动后无终端黑框，不报找不到库的致命错误，且 DeepSeek 调用畅通。

## 6. 风险与回滚
- **风险**：复杂 GUI 库打包可能漏失依赖文件。
  - *回滚/应对*：若运行闪退，尝试去除 `-w` 重新打包查看黑框中是否有 `ModuleNotFoundError`，并在终端使用 `pip install` 补全。
