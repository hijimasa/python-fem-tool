# python-fem-tool
![demo](./figs/python-fem-tool-demo.gif)
このリポジトリでは、Pythonで簡易的にFEMを試してみることができます。
基本は参考サイトのアルタカさんのプログラムをベースにしています。
参考サイトのものは、メッシュ方法を手書きしていたので、STLファイルから読み込めるように拡張しました。
勉強がてら作っているので、誤作動や誤動作を起こす可能性があります。自己責任でご使用ください。

## 使い方
0. 必要なパッケージのインストール
   ```
   git clone https://github.com/hijimasa/python-fem-tool.git
   cd python-fem-tool
   pip install -r requirements.txt
   ```

1. プログラムの起動
   ```
   python main.py
   ```

2. 読み込みファイルの指定

   読み込むSTLファイルパスを記載の上、「読み込み」ボタンからファイルの読み込みを実行してください。
   読み込むファイルの長さ単位はメートル指定にしたほうが良いと思います。


3. 固定端の指定

   x, y, z方向の力を未入力の状態（あるいは全て0）で表示されたメッシュのノードをクリックすると、ノードが赤色になり固定端になります。右クリックで固定端ではなくなります。

4. 力点の指定
   x, y, z方向の力を入力した状態で表示されたメッシュのノードをクリックすると、ノードが緑色になり力の大きさに応じた緑のベクトルが生成されます。右クリックで力点ではなくなります。

5. 各種物性の入力

   ヤング率やポアソン比、密度などの項目を適宜設定してください。
   また、部材全体にかかる重力の有無を選択できます。

6. 解析開始ボタンを押す

   「解析開始」ボタンを押すことで、有限要素法が実行され、結果表示のスケールに合わせた倍率で拡大された変位が表示されます。
   詳細な結果は、pythonを実行した場所に生成されるtest.txtに記載されます。
   

## 参考サイト
- [3次元有限要素法をPythonで実装する(四面体要素)](https://qiita.com/Altaka4128/items/41101c96729b68d7c96f)
