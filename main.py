import tetgen
from stl import mesh
import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Node import Node
from C3D4 import C3D4
from Boundary import Boundary
from FEM import FEM

# STLファイルの読み込み
stl_mesh = mesh.Mesh.from_file("test.stl")

# 頂点情報の取得
points = np.unique(stl_mesh.vectors.reshape(-1, 3), axis=0)

# 面（ファセット）の定義
faces = []
for triangle in stl_mesh.vectors:
    face = []
    for vertex in triangle:
        index = np.where((points == vertex).all(axis=1))[0][0]
        face.append(index)
    faces.append(face)

# TetGenオブジェクトの作成
tet = tetgen.TetGen(points, np.array(faces))

# メッシュの生成
nodes, elems = tet.tetrahedralize(order=1)

# tkinterのウィンドウ作成
root = tk.Tk()
root.title("Python FEM Tool")

# 左側のフレームに3Dプロットを表示
plot_frame = tk.Frame(root)
plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

fig = Figure(figsize=(6, 6))
ax = fig.add_subplot(111, projection="3d")

# 各テトラヘドロンを描画
for elem in elems:
    tetra = nodes[elem]
    verts = [
        [tetra[0], tetra[1], tetra[2]],
        [tetra[0], tetra[1], tetra[3]],
        [tetra[0], tetra[2], tetra[3]],
        [tetra[1], tetra[2], tetra[3]]
    ]
    ax.add_collection3d(Poly3DCollection(verts, edgecolor="k", alpha=0.1))

# 軸ラベル設定
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")

# FigureCanvasTkAggを使用してtkinterウィンドウにプロットを埋め込む
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# ノードのプロットと選択イベント
node_scatter = []
for i in range(len(nodes)):
    node_scatter.append(ax.scatter(nodes[i, 0], nodes[i, 1], nodes[i, 2], color="blue", picker=True))

quiver_plots = []
fixed_node_nums = []
applied_forces = []
# ノードがクリックされたときの処理
def on_node_click(event):
    artist = event.artist
    if event.mouseevent.button == 1:  # 左クリック
        try:
            input_x_value = float(entry_x.get())
        except ValueError:
            input_x_value = 0.0
        try:
            input_y_value = float(entry_y.get())
        except ValueError:
            input_y_value = 0.0
        try:
            input_z_value = float(entry_z.get())
        except ValueError:
            input_z_value = 0.0
        print(input_x_value,input_y_value,input_z_value)

        for i in range(len(nodes)):
            if node_scatter[i] == artist:
                # 指定されたノードのベクトルを削除
                for j in range(len(quiver_plots)):
                    if quiver_plots[j][0] == i:
                        quiver_plots[j][1].remove()
                        del quiver_plots[j]
                        break

                for j in range(len(fixed_node_nums)):
                    if fixed_node_nums[j] == i:
                        del fixed_node_nums[j]
                        break

                for j in range(len(applied_forces)):
                    if applied_forces[j][0] == i:
                        del applied_forces[j]
                        break

                if input_x_value == 0.0 and input_y_value == 0.0 and input_z_value == 0.0:
                    node_scatter[i].set_facecolor("r")
                    node_scatter[i].set_edgecolor("r")
                    
                    fixed_node_nums.append(i)
                else:
                    node_scatter[i].set_facecolor("g")
                    node_scatter[i].set_edgecolor("g")                
                    # ベクトルを描画
                    quiver = ax.quiver(
                        nodes[i, 0], nodes[i, 1], nodes[i, 2],
                        input_x_value, input_y_value, input_z_value,
                        color="g", length=1.0, normalize=True
                    )
                    quiver_plots.append((i, quiver))
                    
                    applied_forces.append([i, input_x_value, input_y_value, input_z_value])
                break
    elif event.mouseevent.button == 3:  # 右クリック
        for i in range(len(nodes)):
            if node_scatter[i] == artist:
                # 指定されたノードのベクトルを削除
                for j in range(len(quiver_plots)):
                    if quiver_plots[j][0] == i:
                        quiver_plots[j][1].remove()
                        del quiver_plots[j]
                        break

                for j in range(len(fixed_node_nums)):
                    if fixed_node_nums[j] == i:
                        del fixed_node_nums[j]
                        break

                for j in range(len(applied_forces)):
                    if applied_forces[j][0] == i:
                        del applied_forces[j]
                        break

                node_scatter[i].set_facecolor("b")
                node_scatter[i].set_edgecolor("b")

    print(fixed_node_nums)
    print(applied_forces)
    # 再描画
    canvas.draw()

# イベントリスナーを登録
fig.canvas.mpl_connect("pick_event", on_node_click)

# 右側のフレームにコントロールを追加
control_frame = tk.Frame(root, padx=10, pady=10)
control_frame.pack(side=tk.RIGHT, fill=tk.Y)

# ボタンと数値入力フィールドの作成
label = tk.Label(control_frame, text="ノードに加える力[N]:")
label.pack(anchor=tk.NW, pady=5)
label_x = tk.Label(control_frame, text="x方向:")
label_x.pack(anchor=tk.NW, pady=5)

entry_x = ttk.Entry(control_frame)
entry_x.pack(anchor=tk.NW, pady=5)

label_y = tk.Label(control_frame, text="y方向:")
label_y.pack(anchor=tk.NW, pady=5)

entry_y = ttk.Entry(control_frame)
entry_y.pack(anchor=tk.NW, pady=5)

label_z = tk.Label(control_frame, text="z方向:")
label_z.pack(anchor=tk.NW, pady=5)

entry_z = ttk.Entry(control_frame)
entry_z.pack(anchor=tk.NW, pady=5)

label_material = tk.Label(control_frame, text="物性:")
label_material.pack(anchor=tk.NW, pady=5)

label_young = tk.Label(control_frame, text="ヤング率:")
label_young.pack(anchor=tk.NW, pady=5)

entry_young = ttk.Entry(control_frame)
entry_young.pack(anchor=tk.NW, pady=5)
entry_young.insert(0, "210e9")

label_poisson = tk.Label(control_frame, text="ポアソン比:")
label_poisson.pack(anchor=tk.NW, pady=5)

entry_poisson = ttk.Entry(control_frame)
entry_poisson.pack(anchor=tk.NW, pady=5)
entry_poisson.insert(0, "0.3")

label_density = tk.Label(control_frame, text="密度[kg/m^3]:")
label_density.pack(anchor=tk.NW, pady=5)

entry_density = ttk.Entry(control_frame)
entry_density.pack(anchor=tk.NW, pady=5)
entry_density.insert(0, "7850.0")

label_gravity = tk.Label(control_frame, text="重力の有無:")
label_gravity.pack(anchor=tk.NW, pady=5)

var_gravity = tk.BooleanVar()
var_gravity.set(False)
entry_gravity = ttk.Checkbutton(control_frame, variable=var_gravity)
entry_gravity.pack(anchor=tk.NW, pady=5)

label_scale = tk.Label(control_frame, text="結果表示のスケール:")
label_scale.pack(anchor=tk.NW, pady=5)

entry_scale = ttk.Entry(control_frame)
entry_scale.pack(anchor=tk.NW, pady=5)
entry_scale.insert(0, "10000.0")

draw_result = []
def start_analysis():
    # 材料情報を定義する
    try:
        young = float(entry_young.get())
    except ValueError:
        print("wrong young is setted")
        young = 210e9
    try:
        poisson = float(entry_poisson.get())
    except ValueError:
        print("wrong poisson is setted")
        poisson = 0.3
    try:
        density = float(entry_density.get())
    except ValueError:
        print("wrong density is setted")
        density = 7850.0
    if var_gravity.get():
        vecGrav = np.array([0.0, 0.0, -9.81])
    else:
        vecGrav = np.array([0.0, 0.0, 0.0])

    fem_nodes = []
    for i in range(len(nodes)):
        fem_nodes.append(Node(i + 1, nodes[i][0], nodes[i][1], nodes[i][2]))
    fem_elems = []
    for i in range(len(elems)):
        fem_elems.append(C3D4(i + 1, [fem_nodes[elems[i][0]], fem_nodes[elems[i][1]], fem_nodes[elems[i][2]], fem_nodes[elems[i][3]]], young, poisson, density, vecGrav))
        
    # 境界条件を設定する
    bound = Boundary(len(nodes))
    for i in range(len(fixed_node_nums)):
        bound.addSPC(i + 1, 0.0, 0.0, 0.0)
    for i in range(len(applied_forces)):
        bound.addForce(applied_forces[i][0] + 1, applied_forces[i][1], applied_forces[i][2], applied_forces[i][3])

    fem = FEM(fem_nodes, fem_elems, bound)
    fem.analysis()
    fem.outputTxt("test")
    displacement = fem.outputDisplacement()

    # 既存の結果を削除
    for result in draw_result:
        result.remove()
    draw_result.clear()

    # 変形したノードを生成
    try:
        scale = float(entry_scale.get())
    except ValueError:
        print("wrong scale is setted")
        scale = 10000.0

    result_nodes = np.zeros((len(nodes), 3), dtype=np.float32)
    for i in range(len(nodes)):
        for j in range(3):
            result_nodes[i][j] = nodes[i][j] + scale * displacement[i][j]
        
    # 各テトラヘドロンを描画
    for elem in elems:
        tetra = result_nodes[elem]
        verts = [
            [tetra[0], tetra[1], tetra[2]],
            [tetra[0], tetra[1], tetra[3]],
            [tetra[0], tetra[2], tetra[3]],
            [tetra[1], tetra[2], tetra[3]]
        ]
        draw_result.append(ax.add_collection3d(Poly3DCollection(verts, edgecolor="b", alpha=0.0)))

    # ここにプロットの更新処理を追加可能
    canvas.draw()

# 更新ボタン
def update_plot():
    # ここにプロットの更新処理を追加可能
    canvas.draw()


button = tk.Button(control_frame, text="解析開始", command=start_analysis)
button.pack(anchor=tk.NW, pady=5)

# TODO: 力と変位の表示を切り替えるようにするかも
#redraw_button = tk.Button(control_frame, text="描画更新", command=update_plot) 
#redraw_button.pack(anchor=tk.NW, pady=5)

# 他のボタンの追加（例）
exit_button = tk.Button(control_frame, text="終了", command=root.quit)
exit_button.pack(anchor=tk.NW, pady=5)

# tkinterのメインループ開始
root.mainloop()

