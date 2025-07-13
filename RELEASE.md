# Python FEM Tool v2.0 - リリースノート

## 🎉 メジャーアップデート v2.0

Python FEM Tool が大幅にエンハンスされ、v2.0としてリリースされました！
新しい解析機能と大幅なユーザビリティ向上を実現しています。

## 🆕 新機能

### パラメトリック解析
- X、Y、Z方向のスケールを変化させた最適化解析
- 複数ケースの自動実行と結果比較
- CSV形式での結果エクスポート
- 個別ケースの詳細表示（変形表示付き）

### 振動解析
- 固有振動数とモード形状の解析
- 指定したモード数での固有値解析
- モード形状の3D可視化
- 結果のCSVエクスポート

### メッシュ表示最適化
- メッシュ表示率の調整（10%～100%）
- エッジのみ表示モード
- 最大表示要素数の制限
- インテリジェントな要素選択

### 変形表示スケール
- パラメトリック解析での変形表示
- カスタムスケール倍率の指定
- インタラクティブな入力ダイアログ

## 🔧 技術的改善

### アーキテクチャの改善
- **メッシュ分離**: 解析用メッシュと表示用メッシュを分離
- **スケール累積問題の解決**: 表示操作が解析に影響しない設計
- **モジュラー設計**: 機能ごとの独立したクラス設計

### パフォーマンス最適化
- 大規模メッシュでの軽快な動作
- 効率的な描画アルゴリズム
- メモリ使用量の最適化

## 📦 配布形式

### ソースコード版
```bash
git clone https://github.com/hijimasa/python-fem-tool.git
cd python-fem-tool
pip install -r requirements.txt
python main.py
```

### スタンドアロン実行ファイル
- **Linux版**: `PythonFEMTool` (実行権限付き)
- **Windows版**: `PythonFEMTool.exe`

## 🛠 スタンドアロン実行ファイルの作成

### 自分でビルドする場合

#### Linux環境
```bash
# PyInstallerをインストール
pip install pyinstaller

# ビルドスクリプトを実行
chmod +x build_linux.sh
./build_linux.sh
```

#### Windows環境
```cmd
REM PyInstallerをインストール
pip install pyinstaller

REM ビルドスクリプトを実行
build_windows.bat
```

### 詳細なビルド手順
詳細な手順については `BUILD_INSTRUCTIONS.md` を参照してください。

## 📋 システム要件

### 最小要件
- Python 3.7以上
- 2GB以上のRAM
- 1GB以上の空きディスク容量

### 推奨要件
- Python 3.8以上
- 4GB以上のRAM
- 2GB以上の空きディスク容量
- GPU（表示性能向上のため）

### 対応OS
- **Linux**: Ubuntu 18.04+, CentOS 7+, その他主要ディストリビューション
- **Windows**: Windows 10/11
- **macOS**: macOS 10.14+（テスト済み）

## 📁 ファイル構成

```
python-fem-tool/
├── main.py                    # メインプログラム（エンハンス版）
├── main_original.py           # 元のプログラム（バックアップ）
├── requirements.txt           # 必要パッケージ
├── README.md                  # 使用方法
├── RELEASE.md                 # このファイル
├── BUILD_INSTRUCTIONS.md      # ビルド手順
├── build_linux.sh            # Linuxビルドスクリプト
├── build_windows.bat          # Windowsビルドスクリプト
├── main.spec                  # PyInstaller設定ファイル
├── MaterialDatabase.py        # 材料データベース
├── GeometryGenerator.py       # 形状生成
├── LoadManager.py             # 荷重管理
├── DocumentExporter.py        # レポート出力
├── ProjectData.py             # プロジェクト管理
├── Node.py                    # ノードクラス
├── C3D4.py                    # 要素クラス
├── FEM.py                     # FEM解析エンジン
├── Boundary.py                # 境界条件
└── Dmatrix.py                 # 材料マトリクス
```

## 🚀 使用開始手順

### 1. インストール
```bash
# リポジトリをクローン
git clone https://github.com/hijimasa/python-fem-tool.git
cd python-fem-tool

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 起動
```bash
python main.py
```

### 3. 基本的な使用フロー
1. **Geometry**タブで基本形状を生成、または**File**タブでSTLを読み込み
2. **Material**タブで材料を選択
3. **Boundary**タブで固定端と荷重を設定
4. **Analysis**タブで解析を実行

### 4. 新機能の使用
- **パラメトリック解析**: **Parametric**タブでスケール範囲を設定して実行
- **振動解析**: **Vibration**タブでモード数を指定して実行
- **表示最適化**: **Geometry**タブの「表示設定」パネルで調整

## 📊 パフォーマンス指標

### ベンチマーク結果（Linux環境）
- **小規模メッシュ** (1000要素以下): 即座に表示
- **中規模メッシュ** (1000-10000要素): 1-3秒で表示
- **大規模メッシュ** (10000要素以上): 軽量化モードで快適な操作

### メモリ使用量
- **基本起動**: 約100MB
- **中規模メッシュ読み込み**: 約200-500MB
- **大規模パラメトリック解析**: 約500MB-1GB

## 🐛 既知の問題と制限事項

### 既知の問題
1. 非常に大きなSTLファイル（100MB以上）の読み込みに時間がかかる場合がある
2. 一部のLinuxディストリビューションでtkinterのインストールが必要な場合がある

### 制限事項
1. 現在は線形解析のみ対応（非線形解析は今後の予定）
2. 四面体要素のみ対応（六面体要素は今後の予定）
3. 動解析は対応していない（静解析と振動解析のみ）

## 🔄 v1.0からの移行

### 互換性
- v1.0のプロジェクトファイルはそのまま読み込み可能
- 既存のSTLファイルも問題なく使用可能
- 操作方法の基本は変わらず

### 新機能の活用
1. 既存プロジェクトを開く
2. 新しいタブ（Parametric, Vibration）を試す
3. 表示設定で快適性を向上

## 🆘 サポート

### トラブルシューティング
1. `README.md`のトラブルシューティング章を確認
2. `BUILD_INSTRUCTIONS.md`でビルド関連の問題を確認
3. GitHubのIssuesで報告

### 連絡先
- GitHub Issues: https://github.com/hijimasa/python-fem-tool/issues
- 元の参考実装: [3次元有限要素法をPythonで実装する(四面体要素)](https://qiita.com/Altaka4128/items/41101c96729b68d7c96f)

## 📅 今後の予定

### v2.1 (予定)
- 材料非線形解析
- 結果の詳細可視化
- エクスポート機能の拡張

### v3.0 (構想)
- 六面体要素対応
- 動解析機能
- クラウド連携

## 🙏 謝辞

このプロジェクトは以下の方々・プロジェクトのおかげで実現できました：

- **Altaka4128**さん: 元の3D FEM実装（[Qiita記事](https://qiita.com/Altaka4128/items/41101c96729b68d7c96f)）
- **NumPy/SciPy**コミュニティ: 数値計算ライブラリ
- **Matplotlib**コミュニティ: 可視化ライブラリ
- **TetGen**プロジェクト: メッシュ生成
- **PyInstaller**プロジェクト: 実行ファイル生成

---

**Python FEM Tool v2.0** - より強力で使いやすい有限要素解析ツール