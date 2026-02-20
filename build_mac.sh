#!/bin/bash
set -e

# Load python environment if needed, assume run in venv
source venv/bin/activate
echo "Installing pyinstaller if not present..."
pip install pyinstaller

echo "Building macOS application..."
# - windowed mode for Mac .app, name is KeywordSearchTool
pyinstaller --windowed --name "KeywordSearchTool" -y main.py

echo "Creating DMG..."
cd dist
# Check if a dmg already exists and remove it
if [ -f "KeywordSearchTool_v1.0.dmg" ]; then
    rm "KeywordSearchTool_v1.0.dmg"
fi

# Create dmg from the .app folder
hdiutil create -volname "KeywordSearchTool_v1.0" -srcfolder "KeywordSearchTool.app" -ov -format UDZO "KeywordSearchTool_v1.0.dmg"

echo "Done! The DMG package is located at dist/KeywordSearchTool_v1.0.dmg"
