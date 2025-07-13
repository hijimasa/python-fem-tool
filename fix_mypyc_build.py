#!/usr/bin/env python3
"""
Windows PyInstaller mypyc error fix script
mypyc関連のエラーを修正するためのスクリプト
"""

import os
import subprocess
import sys
import tempfile

def uninstall_mypyc_packages():
    """mypycで最適化されたパッケージをアンインストール"""
    print("Checking for mypyc-optimized packages...")
    
    # 既知のmypycで最適化されることがあるパッケージ
    mypyc_packages = [
        'mypy',
        'black',
        'ujson',
        'orjson',
        'pydantic',
    ]
    
    for package in mypyc_packages:
        try:
            # パッケージが存在するかチェック
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Found {package}, reinstalling without mypyc optimization...")
                
                # アンインストール
                subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', package])
                
                # 再インストール（--no-binary でmypyc最適化を避ける）
                subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-binary', package, package])
                
        except Exception as e:
            print(f"Warning: Could not process {package}: {e}")

def create_clean_environment():
    """クリーンな環境でビルドするための準備"""
    print("Setting up clean build environment...")
    
    # 環境変数を設定してmypycを無効化
    os.environ['MYPY_CACHE_DIR'] = tempfile.mkdtemp()
    os.environ['MYPYC_OPT_LEVEL'] = '0'
    
    # PyInstallerキャッシュをクリア
    cache_dirs = [
        os.path.expanduser('~/.pyinstaller'),
        os.path.join(os.getcwd(), 'build'),
        os.path.join(os.getcwd(), 'dist'),
        os.path.join(os.getcwd(), '__pycache__'),
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            print(f"Removing cache directory: {cache_dir}")
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(['rmdir', '/s', '/q', cache_dir], shell=True)
                else:  # Unix-like
                    subprocess.run(['rm', '-rf', cache_dir])
            except Exception as e:
                print(f"Warning: Could not remove {cache_dir}: {e}")

def build_with_spec():
    """spec ファイルを使用してビルド"""
    print("Building with windows.spec...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            'windows.spec'
        ], check=True)
        
        if os.path.exists('dist/PythonFEMTool.exe'):
            print("Build successful!")
            print("Executable created: dist/PythonFEMTool.exe")
            return True
        else:
            print("Build failed: executable not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        return False

def main():
    """メイン処理"""
    print("=== Python FEM Tool - Windows mypyc Fix Build ===")
    print()
    
    # Step 1: 環境をクリーンアップ
    create_clean_environment()
    
    # Step 2: mypycパッケージを処理
    uninstall_mypyc_packages()
    
    # Step 3: specファイルでビルド
    success = build_with_spec()
    
    if success:
        print()
        print("=== Build Complete Successfully ===")
        print("You can now run: dist\\PythonFEMTool.exe")
    else:
        print()
        print("=== Build Failed ===")
        print("Please check the error messages above.")
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())