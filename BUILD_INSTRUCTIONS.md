# スタンドアロン実行ファイルの作成方法

このドキュメントでは、Python FEM ToolをLinuxとWindows用のスタンドアロン実行ファイルに変換する方法を説明します。

## 必要なツール

### PyInstaller
スタンドアロン実行ファイルの作成には**PyInstaller**を使用します。

```bash
pip install pyinstaller
```

## ビルド手順

### 1. 事前準備

#### requirements.txtの確認
必要なパッケージが全て含まれていることを確認：

```bash
cat requirements.txt
```

#### 現在のディレクトリ構造確認
```bash
ls -la
```

### 2. Linux用実行ファイルの作成

#### 基本的なコマンド
```bash
pyinstaller --onefile --windowed main.py
```

#### より詳細な設定（推奨）
```bash
pyinstaller --onefile \
    --windowed \
    --name "PythonFEMTool" \
    --icon=icon.ico \
    --add-data "MaterialDatabase.py:." \
    --add-data "GeometryGenerator.py:." \
    --add-data "LoadManager.py:." \
    --add-data "DocumentExporter.py:." \
    --add-data "ProjectData.py:." \
    --add-data "requirements.txt:." \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import matplotlib \
    --hidden-import tetgen \
    --hidden-import stl \
    main.py
```

#### specファイルを使用した高度な設定
より複雑な設定が必要な場合は、specファイルを作成：

```bash
pyinstaller --onefile --windowed main.py
# これで main.spec ファイルが生成される
```

生成されたspecファイルを編集してから実行：
```bash
pyinstaller main.spec
```

### 3. Windows用実行ファイルの作成

Windows環境では以下の手順で実行：

#### Windows上での直接ビルド
1. Windows環境にPythonとPyInstallerをインストール
2. ビルドスクリプトを実行：
```cmd
REM 標準ビルドスクリプト
build_windows_fixed.bat

REM または、mypycエラーが発生する場合は修正スクリプトを使用
python fix_mypyc_build.py
```

#### Windows環境でのトラブルシューティング

**mypycエラーが発生する場合**:
```
ModuleNotFoundError: No module named '91844386ccf7a24691a0__mypyc'
```

このエラーは、mypycで最適化されたパッケージがPyInstallerと互換性がない場合に発生します。

**解決方法1**: 修正スクリプトを使用
```cmd
python fix_mypyc_build.py
```

**解決方法2**: 手動修正
```cmd
REM mypyc最適化されたパッケージを再インストール
pip uninstall -y mypy black
pip install --no-binary mypy mypy
pip install --no-binary black black

REM キャッシュをクリア
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q __pycache__

REM specファイルでビルド
pyinstaller windows.spec
```

**解決方法3**: UTF-8エンコーディング問題
Windows環境でbatファイルが動作しない場合は、`build_windows_fixed.bat` を使用してください。

#### クロスコンパイル（Linux→Windows）
PyInstallerはクロスコンパイルをサポートしていないため、Windows用実行ファイルはWindows環境で作成する必要があります。

### 4. 詳細なspecファイル設定例

以下は高度な設定を含むspecファイルの例：

```python
# main.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('MaterialDatabase.py', '.'),
        ('GeometryGenerator.py', '.'),
        ('LoadManager.py', '.'),
        ('DocumentExporter.py', '.'),
        ('ProjectData.py', '.'),
        ('Node.py', '.'),
        ('C3D4.py', '.'),
        ('FEM.py', '.'),
        ('Boundary.py', '.'),
        ('Dmatrix.py', '.'),
    ],
    hiddenimports=[
        'numpy',
        'scipy',
        'scipy.linalg',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'mpl_toolkits.mplot3d',
        'tetgen',
        'stl',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PythonFEMTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'  # アイコンファイルがある場合
)
```

### 5. オプション説明

#### 主要オプション
- `--onefile`: 全てを1つの実行ファイルにまとめる
- `--windowed`: コンソールウィンドウを表示しない（GUI用）
- `--name`: 出力ファイル名を指定
- `--icon`: アイコンファイルを指定
- `--add-data`: 追加ファイルを含める

#### デバッグオプション
- `--debug all`: 詳細なデバッグ情報を表示
- `--console`: コンソールウィンドウを表示（デバッグ時）

### 6. トラブルシューティング

#### よくある問題と解決方法

1. **モジュールが見つからないエラー**
   ```bash
   --hidden-import [モジュール名]
   ```
   を追加

2. **tkinterエラー**
   ```bash
   --hidden-import tkinter
   --hidden-import tkinter.ttk
   ```

3. **matplotlib関連エラー**
   ```bash
   --hidden-import matplotlib.backends.backend_tkagg
   ```

4. **tetgen/stlライブラリエラー**
   システムにC++ライブラリが必要な場合があります：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tetgen libtetgen-dev
   
   # CentOS/RHEL
   sudo yum install tetgen-devel
   ```

5. **ファイルサイズが大きい場合**
   - `--exclude-module` を使用して不要なモジュールを除外
   - UPX圧縮を使用: `--upx-dir=/path/to/upx`

### 7. 実行とテスト

#### ビルド後のテスト
```bash
# 生成されたファイルの確認
ls -la dist/

# 実行テスト
./dist/PythonFEMTool
```

#### 配布前のチェック
1. 異なる環境でのテスト
2. 必要なシステムライブラリの確認
3. ファイルサイズの確認
4. 起動時間の確認

### 8. 配布方法

#### Linux用配布
- 生成されたバイナリファイルをそのまま配布
- 必要に応じてシェルスクリプトでラップ

#### Windows用配布
- `.exe` ファイルをそのまま配布
- インストーラー作成ツール（NSIS、InnoSetupなど）を使用

#### クロスプラットフォーム配布
それぞれのOS用にビルドしたファイルを用意：
```
releases/
├── linux/
│   └── PythonFEMTool
├── windows/
│   └── PythonFEMTool.exe
└── README.txt
```

### 9. 自動化スクリプト

#### Linux用ビルドスクリプト
```bash
#!/bin/bash
# build_linux.sh

echo "Building Linux executable..."
pyinstaller --onefile \
    --windowed \
    --name "PythonFEMTool" \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import matplotlib \
    --hidden-import tetgen \
    --hidden-import stl \
    main.py

echo "Build completed. Executable is in dist/ directory."
```

#### Windows用ビルドスクリプト
```batch
@echo off
REM build_windows.bat

echo Building Windows executable...
pyinstaller --onefile ^
    --windowed ^
    --name "PythonFEMTool" ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import matplotlib ^
    --hidden-import tetgen ^
    --hidden-import stl ^
    main.py

echo Build completed. Executable is in dist\ directory.
pause
```

### 10. 高度な設定

#### 仮想環境での完全な分離
```bash
# 新しい仮想環境作成
python -m venv build_env
source build_env/bin/activate  # Linux
# build_env\Scripts\activate.bat  # Windows

# 必要なパッケージのみインストール
pip install -r requirements.txt
pip install pyinstaller

# ビルド実行
pyinstaller main.spec
```

#### 依存関係の最適化
```bash
# 実際に使用されているモジュールを調査
python -m pip show [package-name]

# 不要なパッケージを除外
pyinstaller --exclude-module [unwanted-module] main.py
```

## 注意事項

1. **ライセンス**: 組み込まれるライブラリのライセンスを確認
2. **サイズ**: tkinter + matplotlib + scipyを含むため、ファイルサイズが大きくなる
3. **起動時間**: 初回起動時に展開処理があるため時間がかかる場合がある
4. **プラットフォーム依存**: 各OS用に個別にビルドが必要

これらの手順に従って、各プラットフォーム用のスタンドアロン実行ファイルを作成できます。