@echo off
echo Building Raiden+ Desktop Application...
python build.py
if errorlevel 1 (
    echo Build failed with error code %errorlevel%
    pause
    exit /b %errorlevel%
)
echo Build successful! Find Raiden.exe in the dist folder.
pause
