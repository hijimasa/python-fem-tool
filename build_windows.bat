@echo off
REM Windows用ビルドスクリプト - Python FEM Tool

echo === Python FEM Tool - Windows Build Script ===
echo.

REM PyInstallerがインストールされているかチェック
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstallerがインストールされていません。インストール中...
    pip install pyinstaller
)

REM 既存のビルドファイルをクリーンアップ
echo 既存のビルドファイルをクリーンアップ中...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo Windows用実行ファイルをビルド中...
echo.

REM PyInstallerでビルド実行
pyinstaller --onefile ^
    --windowed ^
    --name "PythonFEMTool" ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import scipy.linalg ^
    --hidden-import matplotlib ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import mpl_toolkits.mplot3d ^
    --hidden-import mpl_toolkits.mplot3d.art3d ^
    --hidden-import tetgen ^
    --hidden-import stl ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.messagebox ^
    --add-data "MaterialDatabase.py;." ^
    --add-data "GeometryGenerator.py;." ^
    --add-data "LoadManager.py;." ^
    --add-data "DocumentExporter.py;." ^
    --add-data "ProjectData.py;." ^
    --add-data "Node.py;." ^
    --add-data "C3D4.py;." ^
    --add-data "FEM.py;." ^
    --add-data "Boundary.py;." ^
    --add-data "Dmatrix.py;." ^
    main.py

REM ビルド結果をチェック
if exist "dist\PythonFEMTool.exe" (
    echo.
    echo ✅ ビルド成功!
    echo 実行ファイル: dist\PythonFEMTool.exe
    echo.
    
    REM ファイル情報を表示
    dir dist\PythonFEMTool.exe
    echo.
    
    echo 実行方法:
    echo   dist\PythonFEMTool.exe
    echo.
    
    REM 配布用ディレクトリを作成
    if not exist release\windows mkdir release\windows
    copy dist\PythonFEMTool.exe release\windows\
    copy README.md release\windows\
    copy BUILD_INSTRUCTIONS.md release\windows\
    echo 配布用ファイルを release\windows\ に配置しました。
    
) else (
    echo ❌ ビルド失敗
    echo エラーを確認してください。
    pause
    exit /b 1
)

echo.
echo === ビルド完了 ===
pause