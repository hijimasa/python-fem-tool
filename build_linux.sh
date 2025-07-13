#!/bin/bash
# Linux用ビルドスクリプト - Python FEM Tool

echo "=== Python FEM Tool - Linux Build Script ==="
echo ""

# PyInstallerがインストールされているかチェック
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstallerがインストールされていません。インストール中..."
    pip install pyinstaller
fi

# 既存のビルドファイルをクリーンアップ
echo "既存のビルドファイルをクリーンアップ中..."
rm -rf build/ dist/ *.spec

echo "Linux用実行ファイルをビルド中..."
echo ""

# PyInstallerでビルド実行
pyinstaller --onefile \
    --windowed \
    --name "PythonFEMTool" \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import scipy.linalg \
    --hidden-import matplotlib \
    --hidden-import matplotlib.backends.backend_tkagg \
    --hidden-import mpl_toolkits.mplot3d \
    --hidden-import mpl_toolkits.mplot3d.art3d \
    --hidden-import tetgen \
    --hidden-import stl \
    --hidden-import tkinter \
    --hidden-import tkinter.ttk \
    --hidden-import tkinter.filedialog \
    --hidden-import tkinter.messagebox \
    --hidden-import reportlab \
    --hidden-import reportlab.lib \
    --hidden-import reportlab.lib.pagesizes \
    --hidden-import reportlab.platypus \
    --hidden-import reportlab.graphics \
    --hidden-import PIL \
    --hidden-import PIL.Image \
    --add-data "MaterialDatabase.py:." \
    --add-data "GeometryGenerator.py:." \
    --add-data "LoadManager.py:." \
    --add-data "DocumentExporter.py:." \
    --add-data "ProjectData.py:." \
    --add-data "Node.py:." \
    --add-data "C3D4.py:." \
    --add-data "FEM.py:." \
    --add-data "Boundary.py:." \
    --add-data "Dmatrix.py:." \
    main.py

# ビルド結果をチェック
if [ -f "dist/PythonFEMTool" ]; then
    echo ""
    echo "✅ ビルド成功!"
    echo "実行ファイル: dist/PythonFEMTool"
    echo ""
    
    # ファイル情報を表示
    ls -lh dist/PythonFEMTool
    echo ""
    
    # 実行権限を付与
    chmod +x dist/PythonFEMTool
    echo "実行権限を付与しました。"
    echo ""
    
    echo "実行方法:"
    echo "  ./dist/PythonFEMTool"
    echo ""
    
    # 配布用ディレクトリを作成
    mkdir -p release/linux
    cp dist/PythonFEMTool release/linux/
    cp README.md release/linux/
    cp BUILD_INSTRUCTIONS.md release/linux/
    echo "配布用ファイルを release/linux/ に配置しました。"
    
else
    echo "❌ ビルド失敗"
    echo "エラーを確認してください。"
    exit 1
fi

echo ""
echo "=== ビルド完了 ==="