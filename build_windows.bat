@echo off
REM Windows Build Script - Python FEM Tool
REM UTF-8 Encoding with Windows line endings

echo === Python FEM Tool - Windows Build Script ===
echo.

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean existing build files
echo Cleaning existing build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo Building Windows executable...
echo.

REM Build using spec file to avoid mypyc issues
pyinstaller windows.spec

REM Check build result
if exist "dist\PythonFEMTool.exe" (
    echo.
    echo Build successful!
    echo Executable: dist\PythonFEMTool.exe
    echo.
    
    REM Display file information
    dir dist\PythonFEMTool.exe
    echo.
    
    echo Usage:
    echo   dist\PythonFEMTool.exe
    echo.
    
    REM Create distribution directory
    if not exist release\windows mkdir release\windows
    copy dist\PythonFEMTool.exe release\windows\
    copy README.md release\windows\
    copy BUILD_INSTRUCTIONS.md release\windows\
    copy RELEASE.md release\windows\
    echo Distribution files placed in release\windows\
    
) else (
    echo Build failed
    echo Please check errors above.
    pause
    exit /b 1
)

echo.
echo === Build Complete ===
pause