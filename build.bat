@echo off
echo Cleaning old builds...
rmdir /s /q build dist
echo Building Standalone Gentle Reminder EXE (One File)...
python -m PyInstaller --noconfirm --onefile --windowed --icon "assets/icon.ico" --add-data "assets;assets/" --name "GentleReminder" main.py
echo Build complete. Check the 'dist' folder for GentleReminder.exe
pause
