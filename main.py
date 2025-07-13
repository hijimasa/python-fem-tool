import tetgen
from stl import mesh
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

from Node import Node
from C3D4 import C3D4
from Boundary import Boundary
from FEM import FEM
from ProjectData import ProjectData
from DocumentExporter import DocumentExporter
from MaterialDatabase import MaterialDatabase
from GeometryGenerator import GeometryGenerator
from LoadManager import LoadManager

class EnhancedFEMTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Python FEM Tool")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)  # 最小ウィンドウサイズを設定
        
        # データ管理オブジェクト
        self.project_data = ProjectData()
        self.material_db = MaterialDatabase()
        self.load_manager = None
        self.current_yield_strength = 250e6  # デフォルト降伏応力（Pa）
        
        # 描画関連変数
        self.nodes = None
        self.elems = None
        self.base_nodes = None      # 解析用の基本メッシュ（不変）
        self.display_nodes = None   # 表示用メッシュ（変形可能）
        self.draw_stl_list = []
        self.draw_result = []
        self.node_scatter = []
        self.quiver_plots = []
        self.selected_nodes = []
        
        # メッシュ表示設定
        self.mesh_display_level = 1.0  # 1.0 = 全表示, 0.5 = 50%表示, 等
        self.show_mesh_edges_only = False  # True = エッジのみ表示
        self.max_display_elements = 10000  # 最大表示要素数
        
        # 境界条件管理
        self.boundary_conditions = []  # 設定済み境界条件のリスト
        self.condition_id_counter = 0  # 条件IDカウンター
        
        # 選択管理
        self.selected_edges = []  # 選択されたエッジ（ノードペアのリスト）
        self.selected_faces = []  # 選択された面（ノード3つ組のリスト）
        
        # GUI作成
        self.setup_gui()
        
        # イベントバインド
        self.setup_events()
    
    def setup_gui(self):
        """GUI要素を作成"""
        # メインフレーム構成
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 右側：コントロールパネルを先にpack（固定幅を確保）
        control_frame = tk.Frame(main_frame, width=500)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        control_frame.pack_propagate(False)
        
        # 左側：3Dプロット（残りの領域を使用）
        plot_frame = tk.Frame(main_frame)
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Figureサイズを動的に調整（固定サイズを削除）
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.ax.set_xlabel("X [m]")
        self.ax.set_ylabel("Y [m]")
        self.ax.set_zlabel("Z [m]")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # ノートブック（タブ）
        self.notebook = ttk.Notebook(control_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # タブの幅を調整
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[8, 4])
        
        # 各タブを作成
        self.create_file_tab()
        self.create_geometry_tab()
        self.create_material_tab()
        self.create_boundary_tab()
        self.create_analysis_tab()
        self.create_parametric_tab()
        self.create_vibration_tab()
        self.create_export_tab()
        
        # 最初のタブを選択状態にする
        self.notebook.select(0)
        
        # タブ切り替えイベントをバインド
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_file_tab(self):
        """ファイル操作タブ"""
        file_frame = ttk.Frame(self.notebook)
        self.notebook.add(file_frame, text="File")
        
        # プロジェクト管理
        tk.Label(file_frame, text="プロジェクト管理", font=("Arial", 12, "bold")).pack(pady=5)
        
        tk.Label(file_frame, text="プロジェクト名:").pack(anchor=tk.W)
        self.project_name_entry = tk.Entry(file_frame, width=30)
        self.project_name_entry.pack(pady=2)
        
        project_buttons_frame = tk.Frame(file_frame)
        project_buttons_frame.pack(pady=5)
        tk.Button(project_buttons_frame, text="新規", command=self.new_project).pack(side=tk.LEFT, padx=2)
        tk.Button(project_buttons_frame, text="保存", command=self.save_project).pack(side=tk.LEFT, padx=2)
        tk.Button(project_buttons_frame, text="読込", command=self.load_project).pack(side=tk.LEFT, padx=2)
        
        tk.Label(file_frame, text="", height=1).pack()  # スペーサー
        
        # STLファイル読み込み
        tk.Label(file_frame, text="STLファイル読み込み", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(file_frame, text="STLファイルパス:").pack(anchor=tk.W)
        
        stl_frame = tk.Frame(file_frame)
        stl_frame.pack(fill=tk.X, pady=2)
        self.entry_read_stl = tk.Entry(stl_frame, width=25)
        self.entry_read_stl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(stl_frame, text="参照", command=self.browse_stl_file).pack(side=tk.RIGHT, padx=(5,0))
        
        tk.Button(file_frame, text="STL読み込み", command=self.read_stl_button_pressed).pack(pady=5)
    
    def create_geometry_tab(self):
        """形状生成タブ"""
        geom_frame = ttk.Frame(self.notebook)
        self.notebook.add(geom_frame, text="Geometry")
        
        tk.Label(geom_frame, text="基本形状生成", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 形状選択
        tk.Label(geom_frame, text="形状タイプ:").pack(anchor=tk.W)
        self.geometry_type = tk.StringVar(value="rectangular_block")
        geometry_options = [
            ("直方体", "rectangular_block"),
            ("円柱", "cylinder"), 
            ("円筒", "hollow_cylinder"),
            ("L字断面", "l_shape")
        ]
        
        for text, value in geometry_options:
            tk.Radiobutton(geom_frame, text=text, variable=self.geometry_type, 
                          value=value, command=self.update_geometry_params).pack(anchor=tk.W)
        
        # パラメータ入力フレーム
        self.geom_params_frame = tk.Frame(geom_frame)
        self.geom_params_frame.pack(fill=tk.X, pady=10)
        
        self.update_geometry_params()  # 初期パラメータ表示
        
        tk.Button(geom_frame, text="形状生成", command=self.generate_geometry).pack(pady=10)
        
        # 表示設定コントロールを追加
        self.create_display_settings_controls(geom_frame)
    
    def create_material_tab(self):
        """材料選択タブ"""
        mat_frame = ttk.Frame(self.notebook)
        self.notebook.add(mat_frame, text="Material")
        
        tk.Label(mat_frame, text="材料選択", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 材料カテゴリ選択
        tk.Label(mat_frame, text="カテゴリ:").pack(anchor=tk.W)
        self.material_category = ttk.Combobox(mat_frame, width=25, state="readonly")
        self.material_category.pack(pady=2)
        self.material_category['values'] = self.material_db.get_categories()
        self.material_category.bind('<<ComboboxSelected>>', self.update_material_list)
        
        # 材料選択
        tk.Label(mat_frame, text="材料:").pack(anchor=tk.W, pady=(10,0))
        self.material_name = ttk.Combobox(mat_frame, width=25, state="readonly")
        self.material_name.pack(pady=2)
        self.material_name.bind('<<ComboboxSelected>>', self.load_material_properties)
        
        # 材料物性表示・編集
        tk.Label(mat_frame, text="材料物性", font=("Arial", 11, "bold")).pack(pady=(15,5))
        
        # ヤング率
        tk.Label(mat_frame, text="ヤング率 [Pa]:").pack(anchor=tk.W)
        self.entry_young = tk.Entry(mat_frame, width=25)
        self.entry_young.pack(pady=2)
        self.entry_young.insert(0, "210e9")
        
        # ポアソン比
        tk.Label(mat_frame, text="ポアソン比:").pack(anchor=tk.W)
        self.entry_poisson = tk.Entry(mat_frame, width=25)
        self.entry_poisson.pack(pady=2)
        self.entry_poisson.insert(0, "0.3")
        
        # 密度
        tk.Label(mat_frame, text="密度 [kg/m³]:").pack(anchor=tk.W)
        self.entry_density = tk.Entry(mat_frame, width=25)
        self.entry_density.pack(pady=2)
        self.entry_density.insert(0, "7850.0")
        
        # 降伏強度
        tk.Label(mat_frame, text="降伏強度 [MPa]:").pack(anchor=tk.W)
        self.entry_yield_strength = tk.Entry(mat_frame, width=25)
        self.entry_yield_strength.pack(pady=2)
        self.entry_yield_strength.insert(0, "250")
        
        # 重力考慮
        self.var_gravity = tk.BooleanVar()
        tk.Checkbutton(mat_frame, text="重力を考慮", variable=self.var_gravity).pack(anchor=tk.W, pady=5)
    
    def create_boundary_tab(self):
        """境界条件タブ"""
        bound_frame = ttk.Frame(self.notebook)
        self.notebook.add(bound_frame, text="Boundary")
        
        # スクロール可能なフレームを作成
        canvas = tk.Canvas(bound_frame)
        scrollbar = tk.Scrollbar(bound_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- 新規条件設定エリア ---
        new_condition_frame = tk.LabelFrame(scrollable_frame, text="新規境界条件設定", font=("Arial", 11, "bold"))
        new_condition_frame.pack(fill=tk.X, padx=5, pady=5)
        
        
        # 荷重タイプ選択
        tk.Label(new_condition_frame, text="荷重タイプ").pack(anchor=tk.W, pady=(10,0))
        
        self.load_type = tk.StringVar(value="point")
        type_frame = tk.Frame(new_condition_frame)
        type_frame.pack(anchor=tk.W)
        tk.Radiobutton(type_frame, text="点荷重", variable=self.load_type, value="point", 
                      command=self.update_selected_nodes_display).pack(side=tk.LEFT)
        tk.Radiobutton(type_frame, text="辺荷重(自動検出)", variable=self.load_type, value="edge",
                      command=self.update_selected_nodes_display).pack(side=tk.LEFT)
        tk.Radiobutton(type_frame, text="面荷重(自動検出)", variable=self.load_type, value="surface",
                      command=self.update_selected_nodes_display).pack(side=tk.LEFT)
        
        # 説明ラベル
        help_label = tk.Label(new_condition_frame, 
                             text="※辺荷重：2個以上の一直線ノード / 面荷重：3個以上の同一平面ノード", 
                             font=("Arial", 8), fg="gray")
        help_label.pack(anchor=tk.W, pady=(2,0))
        
        # 自動選択設定
        self.auto_select_enabled = tk.BooleanVar(value=True)
        auto_select_frame = tk.Frame(new_condition_frame)
        auto_select_frame.pack(anchor=tk.W, pady=2)
        tk.Checkbutton(auto_select_frame, text="関連ノードを自動選択", 
                      variable=self.auto_select_enabled).pack(side=tk.LEFT)
        
        # 力の入力
        tk.Label(new_condition_frame, text="力 [N]:").pack(anchor=tk.W, pady=(10,0))
        
        force_frame = tk.Frame(new_condition_frame)
        force_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(force_frame, text="X:").pack(side=tk.LEFT)
        self.entry_x = tk.Entry(force_frame, width=8)
        self.entry_x.pack(side=tk.LEFT, padx=2)
        
        tk.Label(force_frame, text="Y:").pack(side=tk.LEFT)
        self.entry_y = tk.Entry(force_frame, width=8)
        self.entry_y.pack(side=tk.LEFT, padx=2)
        
        tk.Label(force_frame, text="Z:").pack(side=tk.LEFT)
        self.entry_z = tk.Entry(force_frame, width=8)
        self.entry_z.pack(side=tk.LEFT, padx=2)
        
        # 選択されたノード表示
        tk.Label(new_condition_frame, text="選択ノード: (左クリック=追加 / 右クリック=解除)").pack(anchor=tk.W, pady=(10,0))
        self.selected_nodes_text = tk.Text(new_condition_frame, height=3, width=50)
        self.selected_nodes_text.pack(pady=2)
        
        # 操作ボタン
        button_frame = tk.Frame(new_condition_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="条件適用", command=self.apply_load, bg="lightgreen").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="選択クリア", command=self.clear_selection).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="全クリア", command=self.clear_all_loads, bg="lightcoral").pack(side=tk.LEFT, padx=2)
        
        # --- 設定済み条件一覧エリア ---
        conditions_frame = tk.LabelFrame(scrollable_frame, text="設定済み境界条件", font=("Arial", 11, "bold"))
        conditions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 条件リストのフレーム
        self.conditions_list_frame = tk.Frame(conditions_frame)
        self.conditions_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初期表示
        self.update_conditions_display()
        
        # --- 表示制御エリア ---
        display_frame = tk.LabelFrame(scrollable_frame, text="表示制御", font=("Arial", 11, "bold"))
        display_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # ボタンを横並びに配置
        button_frame = tk.Frame(display_frame)
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text="表示リセット", command=self.reset_display_scale, 
                 bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="視点リセット", command=self.reset_view, 
                 bg="#2196F3", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        
        # 操作説明
        tk.Label(display_frame, text="マウスホイール: 拡大/縮小", font=("Arial", 8), 
                fg="gray").pack(pady=1)
        tk.Label(display_frame, text="マウスドラッグ: 視点回転", font=("Arial", 8), 
                fg="gray").pack(pady=1)
    
    def create_analysis_tab(self):
        """解析実行タブ"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")
        
        tk.Label(analysis_frame, text="解析設定", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 結果表示スケール
        tk.Label(analysis_frame, text="変形表示スケール:").pack(anchor=tk.W)
        self.entry_scale = tk.Entry(analysis_frame, width=25)
        self.entry_scale.pack(pady=2)
        self.entry_scale.insert(0, "10000.0")
        
        # 解析実行ボタン
        tk.Button(analysis_frame, text="解析開始", command=self.start_analysis,
                 bg="lightgreen", font=("Arial", 12, "bold")).pack(pady=20)
        
        # 結果表示
        tk.Label(analysis_frame, text="解析結果", font=("Arial", 12, "bold")).pack(pady=(20,5))
        
        self.result_text = tk.Text(analysis_frame, height=15, width=35)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(analysis_frame, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
    
    def create_parametric_tab(self):
        """パラメトリック解析タブ"""
        param_frame = ttk.Frame(self.notebook)
        self.notebook.add(param_frame, text="Parametric")
        
        # スクロール可能なフレームを作成
        canvas = tk.Canvas(param_frame)
        scrollbar = tk.Scrollbar(param_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- パラメトリック設定エリア ---
        param_settings_frame = tk.LabelFrame(scrollable_frame, text="パラメトリック解析設定", font=("Arial", 11, "bold"))
        param_settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(param_settings_frame, text="形状スケール変更による強度解析", font=("Arial", 10)).pack(pady=5)
        
        # X軸スケール設定
        x_frame = tk.Frame(param_settings_frame)
        x_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(x_frame, text="X軸スケール:", width=12).pack(side=tk.LEFT)
        tk.Label(x_frame, text="開始:", width=6).pack(side=tk.LEFT)
        self.param_x_start = tk.Entry(x_frame, width=8)
        self.param_x_start.pack(side=tk.LEFT, padx=2)
        self.param_x_start.insert(0, "50")
        tk.Label(x_frame, text="終了:", width=6).pack(side=tk.LEFT)
        self.param_x_end = tk.Entry(x_frame, width=8)
        self.param_x_end.pack(side=tk.LEFT, padx=2)
        self.param_x_end.insert(0, "200")
        tk.Label(x_frame, text="刻み:", width=6).pack(side=tk.LEFT)
        self.param_x_step = tk.Entry(x_frame, width=8)
        self.param_x_step.pack(side=tk.LEFT, padx=2)
        self.param_x_step.insert(0, "25")
        tk.Label(x_frame, text="%").pack(side=tk.LEFT)
        
        # Y軸スケール設定
        y_frame = tk.Frame(param_settings_frame)
        y_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(y_frame, text="Y軸スケール:", width=12).pack(side=tk.LEFT)
        tk.Label(y_frame, text="開始:", width=6).pack(side=tk.LEFT)
        self.param_y_start = tk.Entry(y_frame, width=8)
        self.param_y_start.pack(side=tk.LEFT, padx=2)
        self.param_y_start.insert(0, "50")
        tk.Label(y_frame, text="終了:", width=6).pack(side=tk.LEFT)
        self.param_y_end = tk.Entry(y_frame, width=8)
        self.param_y_end.pack(side=tk.LEFT, padx=2)
        self.param_y_end.insert(0, "200")
        tk.Label(y_frame, text="刻み:", width=6).pack(side=tk.LEFT)
        self.param_y_step = tk.Entry(y_frame, width=8)
        self.param_y_step.pack(side=tk.LEFT, padx=2)
        self.param_y_step.insert(0, "25")
        tk.Label(y_frame, text="%").pack(side=tk.LEFT)
        
        # Z軸スケール設定
        z_frame = tk.Frame(param_settings_frame)
        z_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(z_frame, text="Z軸スケール:", width=12).pack(side=tk.LEFT)
        tk.Label(z_frame, text="開始:", width=6).pack(side=tk.LEFT)
        self.param_z_start = tk.Entry(z_frame, width=8)
        self.param_z_start.pack(side=tk.LEFT, padx=2)
        self.param_z_start.insert(0, "50")
        tk.Label(z_frame, text="終了:", width=6).pack(side=tk.LEFT)
        self.param_z_end = tk.Entry(z_frame, width=8)
        self.param_z_end.pack(side=tk.LEFT, padx=2)
        self.param_z_end.insert(0, "200")
        tk.Label(z_frame, text="刻み:", width=6).pack(side=tk.LEFT)
        self.param_z_step = tk.Entry(z_frame, width=8)
        self.param_z_step.pack(side=tk.LEFT, padx=2)
        self.param_z_step.insert(0, "25")
        tk.Label(z_frame, text="%").pack(side=tk.LEFT)
        
        # 実行ボタン
        tk.Button(param_settings_frame, text="パラメトリック解析実行", 
                 command=self.run_parametric_analysis, bg="#FF9800", fg="white", 
                 font=("Arial", 11, "bold")).pack(pady=10)
        
        # --- 結果表示エリア ---
        results_frame = tk.LabelFrame(scrollable_frame, text="解析結果", font=("Arial", 11, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 結果テーブル用フレーム
        table_frame = tk.Frame(results_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 結果テーブル（Treeview使用）
        columns = ("Case", "X_Scale", "Y_Scale", "Z_Scale", "Max_Stress", "Safety_Factor", "Volume_Ratio")
        self.param_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        # カラムヘッダー設定
        self.param_tree.heading("Case", text="ケース")
        self.param_tree.heading("X_Scale", text="X倍率")
        self.param_tree.heading("Y_Scale", text="Y倍率") 
        self.param_tree.heading("Z_Scale", text="Z倍率")
        self.param_tree.heading("Max_Stress", text="最大応力[MPa]")
        self.param_tree.heading("Safety_Factor", text="安全率")
        self.param_tree.heading("Volume_Ratio", text="体積比")
        
        # カラム幅設定
        self.param_tree.column("Case", width=60)
        self.param_tree.column("X_Scale", width=60)
        self.param_tree.column("Y_Scale", width=60)
        self.param_tree.column("Z_Scale", width=60)
        self.param_tree.column("Max_Stress", width=100)
        self.param_tree.column("Safety_Factor", width=80)
        self.param_tree.column("Volume_Ratio", width=80)
        
        # スクロールバー
        tree_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.param_tree.yview)
        self.param_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.param_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 結果選択とプロット表示ボタン
        button_frame = tk.Frame(results_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(button_frame, text="選択ケースを表示", 
                 command=self.display_selected_case, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="結果をCSV出力", 
                 command=self.export_parametric_results, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
    
    def create_vibration_tab(self):
        """振動解析タブ"""
        vib_frame = ttk.Frame(self.notebook)
        self.notebook.add(vib_frame, text="Vibration")
        
        # スクロール可能なフレームを作成
        canvas = tk.Canvas(vib_frame)
        scrollbar = tk.Scrollbar(vib_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- 振動解析設定エリア ---
        vib_settings_frame = tk.LabelFrame(scrollable_frame, text="振動解析設定", font=("Arial", 11, "bold"))
        vib_settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(vib_settings_frame, text="固有振動数・固有モード解析", font=("Arial", 10)).pack(pady=5)
        
        # 解析パラメータ設定
        params_frame = tk.Frame(vib_settings_frame)
        params_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 解析するモード数
        mode_frame = tk.Frame(params_frame)
        mode_frame.pack(fill=tk.X, pady=2)
        tk.Label(mode_frame, text="解析モード数:", width=15).pack(side=tk.LEFT)
        self.vib_num_modes = tk.Entry(mode_frame, width=10)
        self.vib_num_modes.pack(side=tk.LEFT, padx=5)
        self.vib_num_modes.insert(0, "10")
        tk.Label(mode_frame, text="個").pack(side=tk.LEFT)
        
        # 解析実行ボタン
        tk.Button(vib_settings_frame, text="振動解析実行", 
                 command=self.run_vibration_analysis, bg="#9C27B0", fg="white", 
                 font=("Arial", 11, "bold")).pack(pady=10)
        
        # --- 解析結果表示エリア ---
        results_frame = tk.LabelFrame(scrollable_frame, text="解析結果", font=("Arial", 11, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 固有振動数表示テーブル
        freq_frame = tk.Frame(results_frame)
        freq_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(freq_frame, text="固有振動数一覧", font=("Arial", 10, "bold")).pack(pady=5)
        
        # 結果テーブル（Treeview使用）
        freq_columns = ("Mode", "Frequency_Hz", "Frequency_rad", "Period")
        self.vib_tree = ttk.Treeview(freq_frame, columns=freq_columns, show="headings", height=10)
        
        # カラムヘッダー設定
        self.vib_tree.heading("Mode", text="モード")
        self.vib_tree.heading("Frequency_Hz", text="振動数 [Hz]")
        self.vib_tree.heading("Frequency_rad", text="角振動数 [rad/s]")
        self.vib_tree.heading("Period", text="周期 [s]")
        
        # カラム幅設定
        self.vib_tree.column("Mode", width=60)
        self.vib_tree.column("Frequency_Hz", width=100)
        self.vib_tree.column("Frequency_rad", width=120)
        self.vib_tree.column("Period", width=100)
        
        # スクロールバー付きでテーブルを配置
        vib_scrollbar = ttk.Scrollbar(freq_frame, orient="vertical", command=self.vib_tree.yview)
        self.vib_tree.configure(yscrollcommand=vib_scrollbar.set)
        self.vib_tree.pack(side="left", fill="both", expand=True)
        vib_scrollbar.pack(side="right", fill="y")
        
        # 制御ボタン
        button_frame = tk.Frame(results_frame)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="選択モードを表示", 
                 command=self.display_selected_mode, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="結果をCSV出力", 
                 command=self.export_vibration_results, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
    
    def create_export_tab(self):
        """エクスポートタブ"""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Export")
        
        tk.Label(export_frame, text="ドキュメント出力", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 出力形式選択
        tk.Label(export_frame, text="出力形式:").pack(anchor=tk.W)
        self.export_format = tk.StringVar(value="html")
        formats = [
            ("HTML", "html"),
            ("PDF", "pdf"),
            ("画像のみ", "images")
        ]
        
        for text, value in formats:
            tk.Radiobutton(export_frame, text=text, variable=self.export_format, value=value).pack(anchor=tk.W)
        
        # 出力ボタン
        tk.Button(export_frame, text="ドキュメント出力", command=self.export_document).pack(pady=10)
        
        tk.Label(export_frame, text="", height=2).pack()  # スペーサー
        
        # その他のエクスポート
        tk.Label(export_frame, text="その他", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Button(export_frame, text="テキスト結果出力", command=self.export_text_results).pack(pady=5)
        tk.Button(export_frame, text="現在の設定を保存", command=self.save_current_settings).pack(pady=5)
    
    def setup_events(self):
        """イベントハンドラを設定"""
        self.fig.canvas.mpl_connect("pick_event", self.on_node_click)
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
    
    def browse_stl_file(self):
        """STLファイル選択ダイアログ"""
        filename = filedialog.askopenfilename(
            title="STLファイルを選択",
            filetypes=[("STL files", "*.stl"), ("All files", "*.*")]
        )
        if filename:
            self.entry_read_stl.delete(0, tk.END)
            self.entry_read_stl.insert(0, filename)
    
    def update_geometry_params(self):
        """形状パラメータ入力欄を更新"""
        # 既存のウィジェットを削除
        for widget in self.geom_params_frame.winfo_children():
            widget.destroy()
        
        geom_type = self.geometry_type.get()
        
        if geom_type == "rectangular_block":
            tk.Label(self.geom_params_frame, text="長さ [m]:").pack(anchor=tk.W)
            self.geom_length = tk.Entry(self.geom_params_frame, width=15)
            self.geom_length.pack(pady=2)
            self.geom_length.insert(0, "0.1")
            
            tk.Label(self.geom_params_frame, text="幅 [m]:").pack(anchor=tk.W)
            self.geom_width = tk.Entry(self.geom_params_frame, width=15)
            self.geom_width.pack(pady=2)
            self.geom_width.insert(0, "0.05")
            
            tk.Label(self.geom_params_frame, text="高さ [m]:").pack(anchor=tk.W)
            self.geom_height = tk.Entry(self.geom_params_frame, width=15)
            self.geom_height.pack(pady=2)
            self.geom_height.insert(0, "0.02")
            
        elif geom_type == "cylinder":
            tk.Label(self.geom_params_frame, text="半径 [m]:").pack(anchor=tk.W)
            self.geom_radius = tk.Entry(self.geom_params_frame, width=15)
            self.geom_radius.pack(pady=2)
            self.geom_radius.insert(0, "0.025")
            
            tk.Label(self.geom_params_frame, text="高さ [m]:").pack(anchor=tk.W)
            self.geom_height = tk.Entry(self.geom_params_frame, width=15)
            self.geom_height.pack(pady=2)
            self.geom_height.insert(0, "0.1")
            
        elif geom_type == "hollow_cylinder":
            tk.Label(self.geom_params_frame, text="外径 [m]:").pack(anchor=tk.W)
            self.geom_outer_radius = tk.Entry(self.geom_params_frame, width=15)
            self.geom_outer_radius.pack(pady=2)
            self.geom_outer_radius.insert(0, "0.03")
            
            tk.Label(self.geom_params_frame, text="内径 [m]:").pack(anchor=tk.W)
            self.geom_inner_radius = tk.Entry(self.geom_params_frame, width=15)
            self.geom_inner_radius.pack(pady=2)
            self.geom_inner_radius.insert(0, "0.02")
            
            tk.Label(self.geom_params_frame, text="高さ [m]:").pack(anchor=tk.W)
            self.geom_height = tk.Entry(self.geom_params_frame, width=15)
            self.geom_height.pack(pady=2)
            self.geom_height.insert(0, "0.1")
            
        elif geom_type == "l_shape":
            tk.Label(self.geom_params_frame, text="幅 [m]:").pack(anchor=tk.W)
            self.geom_width = tk.Entry(self.geom_params_frame, width=15)
            self.geom_width.pack(pady=2)
            self.geom_width.insert(0, "0.05")
            
            tk.Label(self.geom_params_frame, text="高さ [m]:").pack(anchor=tk.W)
            self.geom_height = tk.Entry(self.geom_params_frame, width=15)
            self.geom_height.pack(pady=2)
            self.geom_height.insert(0, "0.05")
            
            tk.Label(self.geom_params_frame, text="厚さ [m]:").pack(anchor=tk.W)
            self.geom_thickness = tk.Entry(self.geom_params_frame, width=15)
            self.geom_thickness.pack(pady=2)
            self.geom_thickness.insert(0, "0.005")
            
            tk.Label(self.geom_params_frame, text="長さ [m]:").pack(anchor=tk.W)
            self.geom_length = tk.Entry(self.geom_params_frame, width=15)
            self.geom_length.pack(pady=2)
            self.geom_length.insert(0, "0.1")
    
    def generate_geometry(self):
        """基本形状を生成"""
        try:
            geom_type = self.geometry_type.get()
            
            if geom_type == "rectangular_block":
                length = float(self.geom_length.get())
                width = float(self.geom_width.get())
                height = float(self.geom_height.get())
                nodes, elems = GeometryGenerator.create_rectangular_block(length, width, height)
                
            elif geom_type == "cylinder":
                radius = float(self.geom_radius.get())
                height = float(self.geom_height.get())
                nodes, elems = GeometryGenerator.create_cylinder(radius, height)
                
            elif geom_type == "hollow_cylinder":
                outer_radius = float(self.geom_outer_radius.get())
                inner_radius = float(self.geom_inner_radius.get())
                height = float(self.geom_height.get())
                nodes, elems = GeometryGenerator.create_hollow_cylinder(outer_radius, inner_radius, height)
                
            elif geom_type == "l_shape":
                width = float(self.geom_width.get())
                height = float(self.geom_height.get())
                thickness = float(self.geom_thickness.get())
                length = float(self.geom_length.get())
                nodes, elems = GeometryGenerator.create_l_shape(width, height, thickness, length)
            
            # メッシュデータを設定（解析用と表示用を分離）
            self.set_mesh_data(nodes, elems)
            
            # 生成された形状を描画
            self.draw_mesh()
            
            # LoadManagerを更新（荷重情報は保持）
            if self.load_manager and (self.load_manager.point_loads or self.load_manager.edge_loads or self.load_manager.surface_loads):
                if messagebox.askyesno("警告", "形状を生成すると既存の荷重設定が失われます。続行しますか？"):
                    # 荷重情報をバックアップ
                    load_backup = self.load_manager.backup_loads()
                    self.load_manager = LoadManager(self.nodes, self.elems)
                    # 荷重情報を復元
                    self.load_manager.restore_loads(load_backup)
                    print(f"荷重情報を復元しました: 点荷重{len(load_backup['point_loads'])}個, 辺荷重{len(load_backup['edge_loads'])}個, 面荷重{len(load_backup['surface_loads'])}個")
                else:
                    return
            else:
                self.load_manager = LoadManager(self.nodes, self.elems)
            
            messagebox.showinfo("成功", f"{geom_type}を生成しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"形状生成に失敗しました: {str(e)}")
    
    def update_material_list(self, event=None):
        """選択されたカテゴリの材料リストを更新"""
        category = self.material_category.get()
        if category:
            materials = self.material_db.get_materials_in_category(category)
            self.material_name['values'] = materials
            self.material_name.set('')
    
    def load_material_properties(self, event=None):
        """選択された材料の物性値を読み込み"""
        category = self.material_category.get()
        material = self.material_name.get()
        
        if category and material:
            properties = self.material_db.get_material_properties(category, material)
            if properties:
                self.entry_young.delete(0, tk.END)
                self.entry_young.insert(0, str(properties['young_modulus']))
                
                self.entry_poisson.delete(0, tk.END)
                self.entry_poisson.insert(0, str(properties['poisson_ratio']))
                
                self.entry_density.delete(0, tk.END)
                self.entry_density.insert(0, str(properties['density']))
                
                # 降伏強度を表示・保存（安全率計算用）
                self.current_yield_strength = properties.get('yield_strength', 250e6)
                self.entry_yield_strength.delete(0, tk.END)
                self.entry_yield_strength.insert(0, str(int(self.current_yield_strength/1e6)))
                
                print(f"材料選択: {properties['name']}, 降伏応力: {self.current_yield_strength/1e6:.0f} MPa")
    
    def read_stl_button_pressed(self):
        """STLファイル読み込み"""
        file_path = self.entry_read_stl.get()
        if file_path == "":
            messagebox.showwarning("警告", "STLファイルパスを入力してください")
            return
        
        try:
            nodes, elems = self.read_stl(file_path)
            self.set_mesh_data(nodes, elems)
            self.draw_mesh()
            
            # LoadManagerを更新（荷重情報は保持）
            if self.load_manager and (self.load_manager.point_loads or self.load_manager.edge_loads or self.load_manager.surface_loads):
                if messagebox.askyesno("警告", "STLファイルを読み込むと既存の荷重設定が失われます。続行しますか？"):
                    # 荷重情報をバックアップ
                    load_backup = self.load_manager.backup_loads()
                    self.load_manager = LoadManager(self.nodes, self.elems)
                    # 荷重情報を復元
                    self.load_manager.restore_loads(load_backup)
                    print(f"荷重情報を復元しました: 点荷重{len(load_backup['point_loads'])}個, 辺荷重{len(load_backup['edge_loads'])}個, 面荷重{len(load_backup['surface_loads'])}個")
                else:
                    return
            else:
                self.load_manager = LoadManager(self.nodes, self.elems)
            messagebox.showinfo("成功", "STLファイルを読み込みました")
        except Exception as e:
            messagebox.showerror("エラー", f"STLファイルの読み込みに失敗しました: {str(e)}")
    
    def read_stl(self, file_path):
        """STLファイルを読み込んでメッシュ生成"""
        stl_mesh = mesh.Mesh.from_file(file_path)
        points = np.unique(stl_mesh.vectors.reshape(-1, 3), axis=0)
        
        faces = []
        for triangle in stl_mesh.vectors:
            face = []
            for vertex in triangle:
                index = np.where((points == vertex).all(axis=1))[0][0]
                face.append(index)
            faces.append(face)
        
        tet = tetgen.TetGen(points, np.array(faces))
        nodes, elems = tet.tetrahedralize(order=1)
        
        return nodes, elems
    
    def draw_mesh(self):
        """メッシュを描画（表示用ノードを使用）"""
        if self.display_nodes is None or self.elems is None:
            return
        
        # 既存の描画をクリア
        self.clear_plot()
        
        # メッシュを描画（表示用ノードを使用）
        for elem in self.elems:
            tetra = self.display_nodes[elem]
            verts = [
                [tetra[0], tetra[1], tetra[2]],
                [tetra[0], tetra[1], tetra[3]],
                [tetra[0], tetra[2], tetra[3]],
                [tetra[1], tetra[2], tetra[3]]
            ]
            collection = Poly3DCollection(verts, edgecolor="k", alpha=0.1, facecolor='lightgray')
            self.draw_stl_list.append(self.ax.add_collection3d(collection))
        
        # ノードを描画（表示用ノードを使用）
        for i in range(len(self.display_nodes)):
            scatter = self.ax.scatter(self.display_nodes[i, 0], self.display_nodes[i, 1], self.display_nodes[i, 2], 
                                    color="blue", picker=True, s=20)
            self.node_scatter.append(scatter)
        
        # 軸スケールを統一
        self.set_equal_axis_scale(self.display_nodes)
        
        self.canvas.draw()
    
    def create_display_settings_controls(self, parent_frame):
        """表示設定コントロールを作成"""
        settings_frame = tk.LabelFrame(parent_frame, text="表示設定", font=("Arial", 10, "bold"))
        settings_frame.pack(fill=tk.X, pady=5)
        
        # メッシュ表示レベル
        tk.Label(settings_frame, text="メッシュ表示率 [%]:").pack(anchor=tk.W)
        self.mesh_level_scale = tk.Scale(settings_frame, from_=10, to=100, 
                                       orient=tk.HORIZONTAL, length=200,
                                       command=self.on_mesh_level_change)
        self.mesh_level_scale.set(100)
        self.mesh_level_scale.pack(anchor=tk.W)
        
        # エッジのみ表示オプション
        self.var_edges_only = tk.BooleanVar()
        edges_check = tk.Checkbutton(settings_frame, text="エッジのみ表示（軽量化）", 
                                   variable=self.var_edges_only,
                                   command=self.on_display_mode_change)
        edges_check.pack(anchor=tk.W, pady=2)
        
        # 最大表示要素数
        tk.Label(settings_frame, text="最大表示要素数:").pack(anchor=tk.W)
        self.max_elements_entry = tk.Entry(settings_frame, width=10)
        self.max_elements_entry.pack(anchor=tk.W)
        self.max_elements_entry.insert(0, "10000")
        self.max_elements_entry.bind('<KeyRelease>', self.on_max_elements_change)
        
        # リフレッシュボタン
        tk.Button(settings_frame, text="表示更新", command=self.refresh_display).pack(pady=5)
    
    def on_mesh_level_change(self, value):
        """メッシュ表示レベル変更時の処理"""
        self.mesh_display_level = float(value) / 100.0
        if hasattr(self, 'auto_refresh') and self.auto_refresh:
            self.refresh_display()
    
    def on_display_mode_change(self):
        """表示モード変更時の処理"""
        self.show_mesh_edges_only = self.var_edges_only.get()
        self.refresh_display()
    
    def on_max_elements_change(self, event):
        """最大表示要素数変更時の処理"""
        try:
            self.max_display_elements = int(self.max_elements_entry.get())
        except ValueError:
            pass
    
    def refresh_display(self):
        """表示をリフレッシュ"""
        if self.display_nodes is not None and self.elems is not None:
            self.draw_mesh()
    
    def set_mesh_data(self, nodes, elems):
        """メッシュデータを設定（解析用と表示用を分離）"""
        # numpy配列であることを確認
        if not isinstance(nodes, np.ndarray):
            nodes = np.array(nodes)
        
        # 解析用メッシュ（不変）
        self.base_nodes = nodes.copy()
        
        # 表示用メッシュ（変形可能）
        self.display_nodes = nodes.copy()
        
        # 作業用（後方互換性のため）
        self.nodes = self.display_nodes
        
        # 要素データ
        self.elems = elems
        
        print(f"メッシュデータを設定: ノード{len(self.base_nodes)}個, 要素{len(self.elems)}個")
    
    def reset_display_mesh(self):
        """表示用メッシュを基本メッシュにリセット"""
        if self.base_nodes is not None:
            self.display_nodes = self.base_nodes.copy()
            self.nodes = self.display_nodes
            print("表示メッシュをリセットしました")
    
    def get_analysis_nodes(self):
        """解析用ノードを取得"""
        return self.base_nodes
    
    def clear_plot(self):
        """プロット表示をクリア"""
        for draw in self.draw_stl_list:
            draw.remove()
        self.draw_stl_list.clear()
        
        for draw in self.draw_result:
            draw.remove()
        self.draw_result.clear()
        
        for scatter in self.node_scatter:
            scatter.remove()
        self.node_scatter.clear()
        
        for plot in self.quiver_plots:
            if len(plot) > 1:
                plot[1].remove()
        self.quiver_plots.clear()
        
        self.selected_nodes.clear()
        self.update_selected_nodes_display()
    
    def on_node_click(self, event):
        """ノードクリック時の処理"""
        if self.display_nodes is None:
            return
        
        # クリックされたノードを特定
        for i in range(len(self.display_nodes)):
            if self.node_scatter[i] == event.artist:
                if event.mouseevent.button == 1:  # 左クリック
                    self.handle_node_selection(i)
                elif event.mouseevent.button == 3:  # 右クリック
                    self.handle_node_deselection(i)
                break
        
        self.canvas.draw()
    
    def on_scroll(self, event):
        """マウスホイールによる拡大縮小"""
        if self.display_nodes is None:
            return
        
        # 現在の軸の範囲を取得
        ax_limits = [self.ax.get_xlim(), self.ax.get_ylim(), self.ax.get_zlim()]
        
        # スクロール方向に応じてスケール係数を決定
        if event.button == 'up':
            scale_factor = 0.9  # 拡大
        elif event.button == 'down':
            scale_factor = 1.1  # 縮小
        else:
            return
        
        # 各軸の中心を計算
        centers = [(lim[0] + lim[1]) / 2 for lim in ax_limits]
        
        # 各軸の範囲をスケール
        for i, (center, (low, high)) in enumerate(zip(centers, ax_limits)):
            range_half = (high - low) / 2 * scale_factor
            new_low = center - range_half
            new_high = center + range_half
            
            if i == 0:
                self.ax.set_xlim(new_low, new_high)
            elif i == 1:
                self.ax.set_ylim(new_low, new_high)
            else:
                self.ax.set_zlim(new_low, new_high)
        
        self.canvas.draw()
    
    def reset_view(self):
        """視点をデフォルトに戻す"""
        if self.display_nodes is None:
            return
        
        # デフォルトの視点角度に設定
        self.ax.view_init(elev=20, azim=45)
        
        # スケールも同時にリセット
        if self.display_nodes is not None:
            self.set_equal_axis_scale(self.display_nodes)
    
    def reset_display_scale(self):
        """表示スケールをリセット"""
        if self.display_nodes is not None:
            self.set_equal_axis_scale(self.display_nodes)
            self.canvas.draw()
    
    def on_tab_changed(self, event):
        """タブ切り替え時の処理"""
        try:
            # 現在のタブの名前を取得
            current_tab = self.notebook.tab(self.notebook.select(), "text")
            
            # タブ切り替え時に3D表示をリセット
            self.reset_3d_display()
            
            # タブ固有の初期化処理
            if current_tab == "Analysis":
                # 解析タブに切り替わった場合、解析結果表示をクリア
                self.clear_analysis_results()
                # 他の解析結果テーブルもクリア
                self.clear_other_analysis_tables()
            elif current_tab == "Vibration":
                # 振動解析タブに切り替わった場合、振動解析結果表示をクリア
                self.clear_vibration_display()
                # パラメトリック解析の結果テーブルもクリア
                if hasattr(self, 'param_tree'):
                    for item in self.param_tree.get_children():
                        self.param_tree.delete(item)
            elif current_tab == "Parametric":
                # パラメトリック解析タブに切り替わった場合、パラメトリック表示をクリア
                self.clear_parametric_display()
                # 振動解析の結果テーブルもクリア
                if hasattr(self, 'vib_tree'):
                    for item in self.vib_tree.get_children():
                        self.vib_tree.delete(item)
            else:
                # その他のタブに切り替わった場合、すべての解析結果テーブルをクリア
                self.clear_other_analysis_tables()
                
        except Exception as e:
            print(f"タブ切り替えエラー: {e}")
    
    def clear_other_analysis_tables(self):
        """他の解析結果テーブルをクリア"""
        # 振動解析の結果テーブルをクリア
        if hasattr(self, 'vib_tree'):
            for item in self.vib_tree.get_children():
                self.vib_tree.delete(item)
        
        # パラメトリック解析の結果テーブルをクリア
        if hasattr(self, 'param_tree'):
            for item in self.param_tree.get_children():
                self.param_tree.delete(item)
    
    def reset_3d_display(self):
        """3D表示を基本状態にリセット"""
        # 3D軸を完全にクリア
        self.ax.clear()
        self.ax.set_xlabel("X [m]")
        self.ax.set_ylabel("Y [m]")
        self.ax.set_zlabel("Z [m]")
        self.ax.set_title("")  # タイトルもクリア
        
        # 描画リストをクリア
        self.draw_stl_list.clear()
        self.draw_result.clear()
        self.node_scatter.clear()
        self.quiver_plots.clear()
        
        # 表示メッシュをリセット（スケール累積を防ぐ）
        self.reset_display_mesh()
        
        if self.display_nodes is not None and self.elems is not None:
            # 基本メッシュ表示に戻す
            self.draw_mesh()
        else:
            # メッシュがない場合は表示をクリア
            self.canvas.draw()
    
    def clear_analysis_results(self):
        """解析結果表示をクリア"""
        # 変形結果表示をクリア
        for draw in self.draw_result:
            try:
                draw.remove()
            except:
                pass
        self.draw_result.clear()
        
        # 結果テキストエリアがある場合はクリア
        if hasattr(self, 'result_text'):
            self.result_text.delete(1.0, tk.END)
    
    def clear_vibration_display(self):
        """振動解析表示をクリア"""
        # 振動解析結果のタイトルをクリア
        self.ax.set_title("")
        
        # 3D表示を完全にクリアして再描画
        self.ax.clear()
        self.ax.set_xlabel("X [m]")
        self.ax.set_ylabel("Y [m]")
        self.ax.set_zlabel("Z [m]")
        
        # 描画リストもクリア
        self.draw_stl_list.clear()
        self.draw_result.clear()
        self.node_scatter.clear()
        self.quiver_plots.clear()
        
        # 基本メッシュがある場合は再描画
        if self.nodes is not None and self.elems is not None:
            self.draw_mesh()
        else:
            self.canvas.draw()
    
    def clear_parametric_display(self):
        """パラメトリック解析表示をクリア"""
        # 3D表示を完全にクリア
        self.ax.clear()
        self.ax.set_xlabel("X [m]")
        self.ax.set_ylabel("Y [m]")
        self.ax.set_zlabel("Z [m]")
        self.ax.set_title("")
        
        # 描画リストをクリア
        self.draw_stl_list.clear()
        self.draw_result.clear()
        self.node_scatter.clear()
        self.quiver_plots.clear()
        
        # 元の形状に戻す（スケールをリセット）
        if hasattr(self, 'original_nodes') and self.original_nodes is not None:
            self.nodes = self.original_nodes.copy()
            print("パラメトリック解析: 元の形状に復帰しました")
        
        # メッシュを再描画
        if self.nodes is not None and self.elems is not None:
            self.draw_mesh()
        else:
            self.canvas.draw()
    
    def handle_node_selection(self, node_id):
        """ノード選択処理（複数選択対応）"""
        if node_id not in self.selected_nodes:
            self.selected_nodes.append(node_id)
            self.node_scatter[node_id].set_facecolor("orange")
            self.node_scatter[node_id].set_edgecolor("orange")
        
        self.update_selected_nodes_display()
    
    def handle_node_deselection(self, node_id):
        """ノード選択解除処理"""
        if node_id in self.selected_nodes:
            self.selected_nodes.remove(node_id)
            self.node_scatter[node_id].set_facecolor("blue")
            self.node_scatter[node_id].set_edgecolor("blue")
        
        self.update_selected_nodes_display()
    
    def reset_node_colors(self):
        """全ノードの色をリセット"""
        for scatter in self.node_scatter:
            scatter.set_facecolor("blue")
            scatter.set_edgecolor("blue")
    
    def update_selected_nodes_display(self):
        """選択されたノードの表示を更新"""
        self.selected_nodes_text.delete(1.0, tk.END)
        if self.selected_nodes:
            node_list = ", ".join(map(str, self.selected_nodes))
            count = len(self.selected_nodes)
            
            # 荷重タイプに応じたステータス表示と自動選択
            load_type = self.load_type.get()
            status = ""
            if load_type == "point":
                status = f" (点荷重: {count}個)"
            elif load_type == "edge":
                if count >= 2:
                    status = f" (辺荷重: {count}個 - 適用可能)"
                    # 辺荷重の場合、直線上の追加ノードを自動選択
                    if self.auto_select_enabled.get():
                        self.auto_select_line_nodes()
                else:
                    status = f" (辺荷重: {count}個 - 2個以上必要)"
            elif load_type == "surface":
                if count >= 3:
                    status = f" (面荷重: {count}個 - 適用可能)"
                    # 面荷重の場合、平面上の追加ノードを自動選択
                    if self.auto_select_enabled.get():
                        self.auto_select_plane_nodes()
                else:
                    status = f" (面荷重: {count}個 - 3個以上必要)"
            
            # 自動選択後に再度ノードリストを更新
            if len(self.selected_nodes) != count:
                node_list = ", ".join(map(str, self.selected_nodes))
                count = len(self.selected_nodes)
                if load_type == "edge":
                    status = f" (辺荷重: {count}個 - 自動選択含む)"
                elif load_type == "surface":
                    status = f" (面荷重: {count}個 - 自動選択含む)"
            
            self.selected_nodes_text.insert(tk.END, f"選択ノード: {node_list}{status}")
        else:
            self.selected_nodes_text.insert(tk.END, "ノードが選択されていません")
    
    def auto_select_line_nodes(self):
        """直線上の追加ノードを自動選択"""
        if not self.load_manager or len(self.selected_nodes) < 2:
            return
        
        try:
            # 直線上のノードを検出
            line_nodes = self.load_manager.find_nodes_on_line(self.selected_nodes)
            
            # 新しく見つかったノードを選択に追加
            new_nodes = []
            for node_id in line_nodes:
                if node_id not in self.selected_nodes:
                    self.selected_nodes.append(node_id)
                    self.node_scatter[node_id].set_facecolor("orange")
                    self.node_scatter[node_id].set_edgecolor("orange")
                    new_nodes.append(node_id)
            
            if new_nodes:
                print(f"辺荷重自動選択: {len(new_nodes)}個のノードを追加選択 {new_nodes}")
                self.canvas.draw()
                
        except Exception as e:
            print(f"辺荷重自動選択エラー: {e}")
    
    def auto_select_plane_nodes(self):
        """平面上の追加ノードを自動選択"""
        if not self.load_manager or len(self.selected_nodes) < 3:
            return
        
        try:
            # 平面上のノードを検出
            plane_nodes = self.load_manager.find_nodes_on_plane(self.selected_nodes)
            
            # 新しく見つかったノードを選択に追加
            new_nodes = []
            for node_id in plane_nodes:
                if node_id not in self.selected_nodes:
                    self.selected_nodes.append(node_id)
                    self.node_scatter[node_id].set_facecolor("orange")
                    self.node_scatter[node_id].set_edgecolor("orange")
                    new_nodes.append(node_id)
            
            if new_nodes:
                print(f"面荷重自動選択: {len(new_nodes)}個のノードを追加選択 {new_nodes}")
                self.canvas.draw()
                
        except Exception as e:
            print(f"面荷重自動選択エラー: {e}")
    
    def apply_load(self):
        """選択されたノードに荷重を適用"""
        if not self.selected_nodes:
            messagebox.showwarning("警告", "ノードを選択してください")
            return
        
        if not self.load_manager:
            messagebox.showerror("エラー", "メッシュが読み込まれていません")
            return
        
        try:
            fx = float(self.entry_x.get()) if self.entry_x.get() else 0.0
            fy = float(self.entry_y.get()) if self.entry_y.get() else 0.0
            fz = float(self.entry_z.get()) if self.entry_z.get() else 0.0
            
            load_type = self.load_type.get()
            
            # 境界条件オブジェクトを作成
            self.condition_id_counter += 1
            condition = {
                'id': self.condition_id_counter,
                'nodes': self.selected_nodes.copy(),
                'type': 'fixed' if (fx == 0 and fy == 0 and fz == 0) else load_type,
                'forces': [fx, fy, fz],
                'description': self.get_condition_description(load_type, self.selected_nodes, fx, fy, fz)
            }
            
            if fx == 0 and fy == 0 and fz == 0:
                # 固定端として設定
                for node_id in self.selected_nodes:
                    self.project_data.add_fixed_node(node_id)
                    self.node_scatter[node_id].set_facecolor("red")
                    self.node_scatter[node_id].set_edgecolor("red")
            else:
                if load_type == "point":
                    # 点荷重
                    for node_id in self.selected_nodes:
                        self.load_manager.add_point_load(node_id, fx, fy, fz)
                        self.project_data.add_force(node_id, fx, fy, fz)
                        self.visualize_force_vector(node_id, fx, fy, fz)
                
                elif load_type == "edge" and len(self.selected_nodes) >= 2:
                    # 辺荷重（自動検出）
                    if self.load_manager.find_collinear_nodes(self.selected_nodes):
                        force_magnitude = np.sqrt(fx**2 + fy**2 + fz**2)
                        direction = [fx, fy, fz] if force_magnitude > 0 else [0, 0, 1]
                        self.load_manager.add_edge_load(self.selected_nodes.copy(), force_magnitude, direction)
                        
                        # 等価ノード荷重を取得して可視化
                        equivalent_loads = self.load_manager.distribute_edge_load_to_nodes(
                            self.selected_nodes, force_magnitude, direction)
                        for load in equivalent_loads:
                            self.visualize_force_vector(load[0], load[1], load[2], load[3])
                        
                        # LoadManagerの状態をデバッグ出力
                        print(f"辺荷重追加後のLoadManager状態:")
                        print(f"  辺荷重数: {len(self.load_manager.edge_loads)}")
                        print(f"  点荷重数: {len(self.load_manager.point_loads)}")
                        all_loads = self.load_manager.get_all_equivalent_point_loads()
                        print(f"  等価点荷重合計: {len(all_loads)}")
                        for i, load in enumerate(all_loads):
                            print(f"    {i+1}. ノード{load[0]}: ({load[1]:.2f}, {load[2]:.2f}, {load[3]:.2f}) N")
                        
                        node_list = ", ".join(map(str, self.selected_nodes))
                        messagebox.showinfo("成功", f"辺荷重を設定しました\nノード: {node_list}\n等価点荷重{len(equivalent_loads)}個を生成")
                    else:
                        # 一直線でない場合の詳細メッセージ
                        node_list = ", ".join(map(str, self.selected_nodes))
                        messagebox.showwarning("警告", 
                            f"選択ノードが一直線上にありません\n"
                            f"ノード: {node_list}\n\n"
                            f"辺荷重には一直線上に並ぶノードを選択してください。\n"
                            f"同一エッジ上のノードを選択することを推奨します。")
                        return
                
                elif load_type == "surface" and len(self.selected_nodes) >= 3:
                    # 面荷重（自動検出）
                    if self.load_manager.find_coplanar_nodes(self.selected_nodes):
                        force_magnitude = np.sqrt(fx**2 + fy**2 + fz**2)
                        direction = [fx, fy, fz] if force_magnitude > 0 else [0, 0, 1]
                        self.load_manager.add_surface_load(self.selected_nodes.copy(), force_magnitude, direction)
                        
                        # 等価ノード荷重を取得して可視化
                        equivalent_loads = self.load_manager.distribute_surface_load_to_nodes(
                            self.selected_nodes, force_magnitude, direction)
                        for load in equivalent_loads:
                            self.visualize_force_vector(load[0], load[1], load[2], load[3])
                        
                        # LoadManagerの状態をデバッグ出力
                        print(f"面荷重追加後のLoadManager状態:")
                        print(f"  面荷重数: {len(self.load_manager.surface_loads)}")
                        print(f"  点荷重数: {len(self.load_manager.point_loads)}")
                        all_loads = self.load_manager.get_all_equivalent_point_loads()
                        print(f"  等価点荷重合計: {len(all_loads)}")
                        for i, load in enumerate(all_loads):
                            print(f"    {i+1}. ノード{load[0]}: ({load[1]:.2f}, {load[2]:.2f}, {load[3]:.2f}) N")
                        
                        node_list = ", ".join(map(str, self.selected_nodes))
                        messagebox.showinfo("成功", f"面荷重を設定しました\nノード: {node_list}\n等価点荷重{len(equivalent_loads)}個を生成")
                    else:
                        # 同一平面でない場合の詳細メッセージ
                        node_list = ", ".join(map(str, self.selected_nodes))
                        messagebox.showwarning("警告", 
                            f"選択ノードが同一平面上にありません\n"
                            f"ノード: {node_list}\n\n"
                            f"面荷重には同一平面上に並ぶノードを選択してください。\n"
                            f"同一面上のノードを選択することを推奨します。")
                        return
                
                elif load_type == "edge" and len(self.selected_nodes) < 2:
                    messagebox.showwarning("警告", "辺荷重には2個以上のノードを選択してください")
                    return
                    
                elif load_type == "surface" and len(self.selected_nodes) < 3:
                    messagebox.showwarning("警告", "面荷重には3個以上のノードを選択してください")
                    return
            
            # 境界条件リストに追加
            self.boundary_conditions.append(condition)
            
            # 選択をクリア
            self.clear_selection()
            
            # 表示を更新
            self.update_conditions_display()
            self.canvas.draw()
            
        except ValueError:
            messagebox.showerror("エラー", "数値を正しく入力してください")
    
    def visualize_force_vector(self, node_id, fx, fy, fz):
        """力ベクトルを可視化"""
        if self.nodes is None:
            return
        
        node_pos = self.nodes[node_id]
        quiver = self.ax.quiver(
            node_pos[0], node_pos[1], node_pos[2],
            fx, fy, fz,
            color="green", length=0.01, normalize=True
        )
        self.quiver_plots.append((node_id, quiver))
        
        # ノードの色を緑に変更
        self.node_scatter[node_id].set_facecolor("green")
        self.node_scatter[node_id].set_edgecolor("green")
    
    def clear_selection(self):
        """選択をクリア"""
        print(f"[DEBUG] clear_selection() 実行: {len(self.selected_nodes)}個のノードをクリア")
        self.selected_nodes.clear()
        self.selected_edges.clear()
        self.selected_faces.clear()
        self.reset_node_colors()
        self.update_selected_nodes_display()
        self.canvas.draw()
    
    def clear_all_loads(self):
        """全ての荷重をクリア"""
        if self.load_manager:
            self.load_manager.clear_all_loads()
        
        self.project_data.fixed_nodes.clear()
        self.project_data.applied_forces.clear()
        self.boundary_conditions.clear()
        
        for plot in self.quiver_plots:
            if len(plot) > 1:
                plot[1].remove()
        self.quiver_plots.clear()
        
        self.reset_node_colors()
        self.update_conditions_display()
        self.canvas.draw()
        
        messagebox.showinfo("完了", "全ての荷重をクリアしました")
    
    def get_condition_description(self, load_type, nodes, fx, fy, fz):
        """境界条件の説明文を生成"""
        if fx == 0 and fy == 0 and fz == 0:
            return f"固定端: ノード {', '.join(map(str, nodes))}"
        else:
            force_str = f"({fx:.2f}, {fy:.2f}, {fz:.2f})"
            if load_type == "point":
                return f"点荷重: ノード {', '.join(map(str, nodes))} に {force_str} N"
            elif load_type == "edge":
                return f"辺荷重: ノード {', '.join(map(str, nodes))} に {force_str} N/m"
            elif load_type == "surface":
                return f"面荷重: ノード {', '.join(map(str, nodes))} に {force_str} N/m²"
    
    def update_conditions_display(self):
        """設定済み境界条件の表示を更新"""
        # 既存の表示をクリア
        for widget in self.conditions_list_frame.winfo_children():
            widget.destroy()
        
        if not self.boundary_conditions:
            tk.Label(self.conditions_list_frame, text="設定されている境界条件はありません", 
                    fg="gray", font=("Arial", 10, "italic")).pack(pady=10)
            return
        
        # テーブル用のフレーム
        table_frame = tk.Frame(self.conditions_list_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 列の重み設定（500px幅に合わせて調整）
        table_frame.grid_columnconfigure(0, weight=0, minsize=40)   # ID列
        table_frame.grid_columnconfigure(1, weight=1, minsize=280)  # 条件列
        table_frame.grid_columnconfigure(2, weight=0, minsize=160)  # 操作列
        
        # ヘッダー（500px幅に合わせて調整）
        tk.Label(table_frame, text="ID", width=4, font=("Arial", 9, "bold"), 
                relief=tk.RIDGE, bd=1).grid(row=0, column=0, sticky="ew")
        tk.Label(table_frame, text="条件", width=40, font=("Arial", 9, "bold"), 
                relief=tk.RIDGE, bd=1).grid(row=0, column=1, sticky="ew")
        tk.Label(table_frame, text="削除", width=15, font=("Arial", 9, "bold"), 
                relief=tk.RIDGE, bd=1).grid(row=0, column=2, sticky="ew")
        
        # 各境界条件を表示
        for i, condition in enumerate(self.boundary_conditions, 1):
            self.create_condition_grid_row(table_frame, condition, i)
    
    def create_condition_grid_row(self, parent, condition, row):
        """Grid形式で境界条件の行を作成"""
        # ID表示
        tk.Label(parent, text=str(condition['id']), width=4, relief=tk.RIDGE, bd=1).grid(
            row=row, column=0, sticky="ew")
        
        # 条件説明（長い場合は省略）
        desc_text = condition['description']
        if len(desc_text) > 45:
            desc_text = desc_text[:42] + "..."
        tk.Label(parent, text=desc_text, width=40, anchor="w", relief=tk.RIDGE, bd=1).grid(
            row=row, column=1, sticky="ew")
        
        # 操作ボタンフレーム
        button_frame = tk.Frame(parent, relief=tk.RIDGE, bd=1)
        button_frame.grid(row=row, column=2, sticky="ew", padx=2, pady=2)
        
        delete_btn = tk.Button(button_frame, text="削除", width=15, font=("Arial", 9), bg="lightcoral",
                              command=lambda: self.delete_condition(condition['id']))
        delete_btn.pack(padx=5, pady=3)
    
    
    
    def delete_condition(self, condition_id):
        """境界条件を削除"""
        if messagebox.askyesno("確認", "この境界条件を削除しますか？"):
            condition = next((c for c in self.boundary_conditions if c['id'] == condition_id), None)
            if not condition:
                return
            
            # データから削除
            if condition['type'] == 'fixed':
                for node_id in condition['nodes']:
                    self.project_data.remove_fixed_node(node_id)
                    if node_id < len(self.node_scatter):
                        self.node_scatter[node_id].set_facecolor("blue")
                        self.node_scatter[node_id].set_edgecolor("blue")
            else:
                for node_id in condition['nodes']:
                    self.project_data.remove_force(node_id)
                    if self.load_manager:
                        self.load_manager.remove_point_load(node_id)
                    
                    # 力ベクトル表示を削除
                    for i, plot in enumerate(self.quiver_plots):
                        if len(plot) > 0 and plot[0] == node_id:
                            if len(plot) > 1:
                                plot[1].remove()
                            self.quiver_plots.pop(i)
                            break
                    
                    if node_id < len(self.node_scatter):
                        self.node_scatter[node_id].set_facecolor("blue")
                        self.node_scatter[node_id].set_edgecolor("blue")
            
            # 境界条件リストから削除
            self.boundary_conditions = [c for c in self.boundary_conditions if c['id'] != condition_id]
            
            # 表示を更新
            self.update_conditions_display()
            self.canvas.draw()
    
    
    def start_analysis(self):
        """解析を開始"""
        if self.nodes is None or self.elems is None:
            messagebox.showerror("エラー", "メッシュが読み込まれていません")
            return
        
        # 前回の解析結果をクリア
        self.clear_analysis_results()
        
        # 振動解析の結果もクリア
        if hasattr(self, 'vibration_results'):
            delattr(self, 'vibration_results')
        
        try:
            # 材料物性を取得
            young = float(self.entry_young.get())
            poisson = float(self.entry_poisson.get())
            density = float(self.entry_density.get())
            gravity_enabled = self.var_gravity.get()
            
            # 重力ベクトル
            vec_grav = np.array([0.0, 0.0, -9.81]) if gravity_enabled else np.array([0.0, 0.0, 0.0])
            
            # FEMノードと要素を作成
            fem_nodes = []
            for i in range(len(self.nodes)):
                fem_nodes.append(Node(i + 1, self.nodes[i][0], self.nodes[i][1], self.nodes[i][2]))
            
            fem_elems = []
            for i in range(len(self.elems)):
                elem_nodes = [fem_nodes[self.elems[i][j]] for j in range(4)]
                fem_elems.append(C3D4(i + 1, elem_nodes, young, poisson, density, vec_grav))
            
            # 境界条件を設定
            boundary = Boundary(len(self.nodes))
            
            # 固定端を設定
            for node_id in self.project_data.fixed_nodes:
                boundary.addSPC(node_id + 1, 0.0, 0.0, 0.0)
            
            # 荷重を設定
            print(f"解析開始時のLoadManager状態確認:")
            if self.load_manager:
                print(f"  LoadManagerが存在: True")
                print(f"  点荷重数: {len(self.load_manager.point_loads)}")
                print(f"  辺荷重数: {len(self.load_manager.edge_loads)}")
                print(f"  面荷重数: {len(self.load_manager.surface_loads)}")
                print(f"  LoadManager.nodes形状: {self.load_manager.nodes.shape if self.load_manager.nodes is not None else 'None'}")
                print(f"  main.nodes形状: {self.nodes.shape if self.nodes is not None else 'None'}")
                
                # 辺荷重の詳細確認
                for i, edge_load in enumerate(self.load_manager.edge_loads):
                    print(f"  辺荷重{i+1}: ノード{edge_load['nodes']}, 荷重{edge_load['force_per_length']}, 方向{edge_load['direction']}")
                    # ノードが範囲内かチェック
                    for node_id in edge_load['nodes']:
                        if node_id >= len(self.load_manager.nodes):
                            print(f"    警告: ノード{node_id}は範囲外（最大インデックス: {len(self.load_manager.nodes)-1}）")
                # LoadManagerから等価点荷重を取得
                equivalent_loads = self.load_manager.get_all_equivalent_point_loads()
                
                # LoadManagerが管理している荷重の概要を出力
                load_summary = self.load_manager.get_load_summary()
                print(f"荷重情報: 点荷重{load_summary['point_loads']}個, 辺荷重{load_summary['edge_loads']}個, 面荷重{load_summary['surface_loads']}個")
                print(f"等価点荷重合計: {load_summary['total_equivalent_loads']}個")
                
                # 等価荷重の詳細を出力
                if len(equivalent_loads) > 0:
                    print("等価点荷重の詳細:")
                    for load in equivalent_loads:
                        print(f"  ノード{load[0]+1}: ({load[1]:.2f}, {load[2]:.2f}, {load[3]:.2f}) N")
                        boundary.addForce(load[0] + 1, load[1], load[2], load[3])
                else:
                    print("警告: 等価点荷重が0個です")
                
                # 注意: LoadManagerが等価点荷重をすべて管理しているため、
                # project_data.applied_forcesは表示用のみとし、重複適用を避ける
            else:
                # 従来の方法（LoadManagerが初期化されていない場合）
                print("LoadManagerが初期化されていません。従来の方法で荷重を設定します。")
                for force in self.project_data.applied_forces:
                    boundary.addForce(force[0] + 1, force[1], force[2], force[3])
                    print(f"  荷重 - ノード{force[0]+1}: ({force[1]:.2f}, {force[2]:.2f}, {force[3]:.2f}) N")
            
            # FEM解析実行
            fem = FEM(fem_nodes, fem_elems, boundary)
            fem.analysis()
            
            # 結果をテキスト出力
            fem.outputTxt("analysis_result")
            displacement = fem.outputDisplacement()
            
            # 応力計算
            try:
                max_stress, max_element_id, all_stresses = fem.calculateMaxStress()
                print(f"応力計算完了: 最大von Mises応力 = {max_stress/1e6:.2f} MPa (要素{max_element_id})")
            except Exception as e:
                print(f"応力計算エラー: {e}")
                max_stress = None
                all_stresses = None
            
            # 材料物性情報を取得
            material_properties = {
                'young_modulus': young,
                'poisson_ratio': poisson,
                'density': density,
                'yield_strength': getattr(self, 'current_yield_strength', 250e6)  # デフォルト値
            }
            
            # プロジェクトデータに結果を保存
            self.project_data.calculate_results_summary(displacement, all_stresses, material_properties)
            self.project_data.update_material_properties(young, poisson, density, gravity_enabled)
            
            # 結果を表示
            self.display_results()
            
            # 変形形状を描画
            self.draw_deformed_shape(displacement)
            
            messagebox.showinfo("完了", "解析が完了しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"解析に失敗しました: {str(e)}")
    
    def display_results(self):
        """解析結果をテキストに表示"""
        self.result_text.delete(1.0, tk.END)
        
        # サマリー表示
        summary = f"""解析結果サマリー
================

最大変位: {self.project_data.max_displacement:.6f} m"""
        
        # 応力と安全率情報を追加
        if self.project_data.max_stress is not None:
            summary += f"""

応力解析:
- 最大von Mises応力: {self.project_data.max_stress/1e6:.2f} MPa"""
            
            if self.project_data.safety_factor is not None:
                if self.project_data.safety_factor >= 10:
                    safety_status = "非常に安全"
                elif self.project_data.safety_factor >= 3:
                    safety_status = "安全"
                elif self.project_data.safety_factor >= 1.5:
                    safety_status = "注意"
                else:
                    safety_status = "危険"
                summary += f"""
- 安全率: {self.project_data.safety_factor:.2f} ({safety_status})
- 材料降伏応力: {self.current_yield_strength/1e6:.0f} MPa"""
        
        summary += f"""

材料物性:
- ヤング率: {self.project_data.young_modulus:.2e} Pa
- ポアソン比: {self.project_data.poisson_ratio}
- 密度: {self.project_data.density} kg/m³

境界条件:
- 固定端数: {len(self.project_data.fixed_nodes)}個
- 荷重点数: {len(self.project_data.applied_forces)}個"""
        
        # LoadManagerの荷重情報も追加
        if self.load_manager:
            load_summary = self.load_manager.get_load_summary()
            summary += f"""
- 辺荷重: {load_summary['edge_loads']}個
- 面荷重: {load_summary['surface_loads']}個
- 等価点荷重合計: {load_summary['total_equivalent_loads']}個"""
        
        summary += "\n\n詳細な結果は analysis_result.txt を参照してください。\n"
        
        if self.project_data.safety_factor:
            summary += f"\n安全率: {self.project_data.safety_factor:.2f}"
        
        self.result_text.insert(tk.END, summary)
    
    def draw_deformed_shape(self, displacement, custom_scale=None):
        """変形後の形状を描画"""
        if self.display_nodes is None or self.elems is None:
            return
        
        if custom_scale is not None:
            scale = custom_scale
        else:
            try:
                scale = float(self.entry_scale.get())
            except ValueError:
                scale = 10000.0
        
        # 既存の変形結果をクリア
        for draw in self.draw_result:
            draw.remove()
        self.draw_result.clear()
        
        # 変形後のノード座標を計算（表示用メッシュを使用）
        deformed_nodes = np.zeros_like(self.display_nodes)
        for i in range(len(self.display_nodes)):
            for j in range(3):
                deformed_nodes[i][j] = self.display_nodes[i][j] + scale * displacement[i][j]
        
        # 変形後の形状を描画
        for elem in self.elems:
            tetra = deformed_nodes[elem]
            verts = [
                [tetra[0], tetra[1], tetra[2]],
                [tetra[0], tetra[1], tetra[3]],
                [tetra[0], tetra[2], tetra[3]],
                [tetra[1], tetra[2], tetra[3]]
            ]
            collection = Poly3DCollection(verts, edgecolor="blue", alpha=0.2, facecolor='lightblue')
            self.draw_result.append(self.ax.add_collection3d(collection))
        
        # 軸スケールを統一（変形前後の両方を考慮）
        all_nodes = np.vstack([self.display_nodes, deformed_nodes])
        self.set_equal_axis_scale(all_nodes)
        
        self.canvas.draw()
    
    def new_project(self):
        """新規プロジェクト"""
        self.project_data = ProjectData()
        self.boundary_conditions.clear()
        self.condition_id_counter = 0
        self.selected_edges.clear()
        self.selected_faces.clear()
        self.clear_plot()
        self.nodes = None
        self.elems = None
        self.load_manager = None
        self.project_name_entry.delete(0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.update_conditions_display()
        messagebox.showinfo("完了", "新規プロジェクトを作成しました")
    
    def save_project(self):
        """プロジェクト保存"""
        project_name = self.project_name_entry.get()
        if not project_name:
            messagebox.showwarning("警告", "プロジェクト名を入力してください")
            return
        
        filename = filedialog.asksaveasfilename(
            title="プロジェクトを保存",
            defaultextension=".json",
            filetypes=[("Project files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # 拡張子を除いたベース名を取得
                base_name = filename.replace('.json', '')
                
                self.project_data.project_name = project_name
                self.project_data.nodes = self.nodes
                self.project_data.elements = self.elems
                self.project_data.save_project(base_name)
                
                messagebox.showinfo("完了", "プロジェクトを保存しました")
            except Exception as e:
                messagebox.showerror("エラー", f"保存に失敗しました: {str(e)}")
    
    def load_project(self):
        """プロジェクト読み込み"""
        filename = filedialog.askopenfilename(
            title="プロジェクトを読み込み",
            filetypes=[("Project files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                base_name = filename.replace('.json', '')
                
                self.project_data.load_project(base_name)
                
                # UIに値を反映
                self.project_name_entry.delete(0, tk.END)
                self.project_name_entry.insert(0, self.project_data.project_name)
                
                self.entry_young.delete(0, tk.END)
                self.entry_young.insert(0, str(self.project_data.young_modulus))
                
                self.entry_poisson.delete(0, tk.END)
                self.entry_poisson.insert(0, str(self.project_data.poisson_ratio))
                
                self.entry_density.delete(0, tk.END)
                self.entry_density.insert(0, str(self.project_data.density))
                
                self.var_gravity.set(self.project_data.gravity_enabled)
                
                # メッシュデータを復元
                if self.project_data.nodes is not None and self.project_data.elements is not None:
                    self.nodes = self.project_data.nodes
                    self.elems = self.project_data.elements
                    self.draw_mesh()
                    # プロジェクト読み込み時は荷重情報も復元するためLoadManagerを初期化
                    self.load_manager = LoadManager(self.nodes, self.elems)
                    
                    # プロジェクトデータから荷重情報を復元
                    for force in self.project_data.applied_forces:
                        self.load_manager.add_point_load(force[0], force[1], force[2], force[3])
                
                messagebox.showinfo("完了", "プロジェクトを読み込みました")
                
            except Exception as e:
                messagebox.showerror("エラー", f"読み込みに失敗しました: {str(e)}")
    
    def export_document(self):
        """ドキュメントを出力"""
        if self.project_data.displacement is None:
            messagebox.showwarning("警告", "先に解析を実行してください")
            return
        
        export_format = self.export_format.get()
        
        if export_format == "html":
            filename = filedialog.asksaveasfilename(
                title="HTMLレポートを保存",
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
            )
            
            if filename:
                try:
                    # load_managerが存在しない場合は安全にNoneを渡す
                    load_manager = getattr(self, 'load_manager', None)
                    exporter = DocumentExporter(self.project_data, load_manager)
                    exporter.export_to_html(filename, self.canvas)
                    messagebox.showinfo("完了", f"HTMLレポートを保存しました: {filename}")
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"HTMLエクスポートエラー: {error_details}")
                    messagebox.showerror("エラー", f"HTMLエクスポートに失敗しました: {str(e)}\n\n詳細:\n{error_details}")
        
        elif export_format == "pdf":
            filename = filedialog.asksaveasfilename(
                title="PDFレポートを保存",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            
            if filename:
                try:
                    # load_managerが存在しない場合は安全にNoneを渡す
                    load_manager = getattr(self, 'load_manager', None)
                    exporter = DocumentExporter(self.project_data, load_manager)
                    exporter.export_to_pdf(filename, self.canvas)
                    messagebox.showinfo("完了", f"PDFレポートを保存しました: {filename}")
                except Exception as e:
                    messagebox.showerror("エラー", f"PDFエクスポートに失敗しました: {str(e)}")
        
        elif export_format == "images":
            directory = filedialog.askdirectory(title="画像保存フォルダを選択")
            
            if directory:
                try:
                    # load_managerが存在しない場合は安全にNoneを渡す
                    load_manager = getattr(self, 'load_manager', None)
                    exporter = DocumentExporter(self.project_data, load_manager)
                    exporter.export_images(directory)
                    messagebox.showinfo("完了", f"画像を保存しました: {directory}")
                except Exception as e:
                    messagebox.showerror("エラー", f"画像エクスポートに失敗しました: {str(e)}")
    
    def export_text_results(self):
        """テキスト結果出力"""
        filename = filedialog.asksaveasfilename(
            title="解析結果を保存",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import shutil
                shutil.copy("analysis_result.txt", filename)
                messagebox.showinfo("完了", f"解析結果を保存しました: {filename}")
            except Exception as e:
                messagebox.showerror("エラー", f"ファイル保存に失敗しました: {str(e)}")
    
    def save_current_settings(self):
        """現在の設定を保存"""
        filename = filedialog.asksaveasfilename(
            title="設定を保存",
            defaultextension=".json",
            filetypes=[("Settings files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                settings = {
                    'young_modulus': self.entry_young.get(),
                    'poisson_ratio': self.entry_poisson.get(),
                    'density': self.entry_density.get(),
                    'gravity_enabled': self.var_gravity.get(),
                    'display_scale': self.entry_scale.get()
                }
                
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("完了", f"設定を保存しました: {filename}")
            except Exception as e:
                messagebox.showerror("エラー", f"設定保存に失敗しました: {str(e)}")
    
    def run_parametric_analysis(self):
        """パラメトリック解析実行"""
        if self.base_nodes is None or self.elems is None:
            messagebox.showerror("エラー", "メッシュが生成されていません。")
            return
        
        if not self.project_data.applied_forces and not (self.load_manager and 
           (self.load_manager.edge_loads or self.load_manager.surface_loads)):
            messagebox.showerror("エラー", "荷重が設定されていません。")
            return
        
        # 前回の解析結果をクリア
        self.clear_analysis_results()
        self.clear_vibration_display()
        
        # 他の解析結果もクリア
        if hasattr(self, 'vibration_results'):
            delattr(self, 'vibration_results')
        self.project_data.displacement = None
        self.project_data.max_displacement = None
        self.project_data.max_stress = None
        self.project_data.safety_factor = None
        
        # 元の形状の体積を保存（100%スケール時の体積）
        self.original_volume = self.calculate_mesh_volume()
        
        try:
            # パラメータ取得
            x_start = float(self.param_x_start.get())
            x_end = float(self.param_x_end.get())
            x_step = float(self.param_x_step.get())
            y_start = float(self.param_y_start.get())
            y_end = float(self.param_y_end.get())
            y_step = float(self.param_y_step.get())
            z_start = float(self.param_z_start.get())
            z_end = float(self.param_z_end.get())
            z_step = float(self.param_z_step.get())
        except ValueError:
            messagebox.showerror("エラー", "スケール設定に無効な値があります。")
            return
        
        # 元の座標を保存（解析用メッシュから）
        original_nodes = self.base_nodes.copy()
        
        # 結果テーブルをクリア
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)
        
        # スケール範囲を生成
        x_scales = [x_start + i * x_step for i in range(int((x_end - x_start) / x_step) + 1) if x_start + i * x_step <= x_end]
        y_scales = [y_start + i * y_step for i in range(int((y_end - y_start) / y_step) + 1) if y_start + i * y_step <= y_end]
        z_scales = [z_start + i * z_step for i in range(int((z_end - z_start) / z_step) + 1) if z_start + i * z_step <= z_end]
        
        total_cases = len(x_scales) * len(y_scales) * len(z_scales)
        
        if total_cases > 100:
            if not messagebox.askyesno("確認", f"解析ケース数が{total_cases}件になります。実行しますか？"):
                return
        
        # プログレスバー表示
        progress_window = tk.Toplevel(self.root)
        progress_window.title("パラメトリック解析中...")
        progress_window.geometry("400x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_label = tk.Label(progress_window, text="解析を実行中...")
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, length=300, mode='determinate')
        progress_bar.pack(pady=10)
        progress_bar['maximum'] = total_cases
        
        # パラメトリック解析実行
        results = []
        case_num = 0
        
        for x_scale in x_scales:
            for y_scale in y_scales:
                for z_scale in z_scales:
                    case_num += 1
                    
                    # プログレス更新
                    progress_label.config(text=f"ケース {case_num}/{total_cases} (X:{x_scale}%, Y:{y_scale}%, Z:{z_scale}%)")
                    progress_bar['value'] = case_num
                    progress_window.update()
                    
                    try:
                        # スケール適用（解析用メッシュで作業）
                        scaled_nodes = original_nodes.copy()
                        self.apply_scale_to_nodes(scaled_nodes, x_scale/100, y_scale/100, z_scale/100)
                        
                        # 解析実行（スケールされたメッシュで）
                        result = self.analyze_single_case_with_nodes(scaled_nodes)
                        if result[0] is not None and len(result) == 5:
                            max_stress, safety_factor, volume_ratio, displacement, max_displacement = result
                        else:
                            max_stress, safety_factor, volume_ratio = result[0], result[1], result[2]
                            displacement, max_displacement = None, None
                        
                        # 結果保存
                        results.append({
                            'case': case_num,
                            'x_scale': x_scale,
                            'y_scale': y_scale,
                            'z_scale': z_scale,
                            'max_stress': max_stress,
                            'safety_factor': safety_factor,
                            'volume_ratio': volume_ratio,
                            'displacement': displacement,
                            'max_displacement': max_displacement
                        })
                        
                        # テーブルに追加
                        self.param_tree.insert("", "end", values=(
                            case_num,
                            f"{x_scale:.0f}%",
                            f"{y_scale:.0f}%", 
                            f"{z_scale:.0f}%",
                            f"{max_stress/1e6:.2f}" if max_stress else "N/A",
                            f"{safety_factor:.2f}" if safety_factor else "N/A",
                            f"{volume_ratio:.3f}"
                        ))
                        
                    except Exception as e:
                        print(f"ケース {case_num} でエラー: {e}")
                        continue
        
        # 表示メッシュをリセット（元の形状に戻す）
        self.reset_display_mesh()
        self.draw_mesh()
        
        # プログレスウィンドウを閉じる
        progress_window.destroy()
        
        # 結果保存
        self.parametric_results = results
        
        messagebox.showinfo("完了", f"パラメトリック解析が完了しました。\n{len(results)}ケースの解析を実行しました。")
    
    def apply_scale_to_nodes(self, nodes, x_scale, y_scale, z_scale):
        """指定されたノード座標にスケールを適用"""
        if nodes is None:
            return
        
        # numpy配列であることを確認
        if not isinstance(nodes, np.ndarray):
            nodes = np.array(nodes)
        
        # 重心を計算
        centroid = np.mean(nodes, axis=0)
        
        # 重心を原点とした座標に変換
        centered_nodes = nodes - centroid
        
        # スケール適用
        centered_nodes[:, 0] *= float(x_scale)  # X軸
        centered_nodes[:, 1] *= float(y_scale)  # Y軸
        centered_nodes[:, 2] *= float(z_scale)  # Z軸
        
        # 重心を元に戻す
        nodes[:] = centered_nodes + centroid
    
    def apply_scale(self, x_scale, y_scale, z_scale):
        """表示用メッシュにスケールを適用（後方互換性のため）"""
        if self.display_nodes is None:
            return
        
        # 表示用メッシュにスケール適用
        self.apply_scale_to_nodes(self.display_nodes, x_scale, y_scale, z_scale)
        
        # 作業用参照を更新
        self.nodes = self.display_nodes
    
    def analyze_single_case(self):
        """単一ケースの解析実行"""
        try:
            # 解析実行（既存のメソッドを利用）
            young = float(self.entry_young.get())
            poisson = float(self.entry_poisson.get())
            density = float(self.entry_density.get())
            gravity = self.var_gravity.get()
            
            # ノードオブジェクト作成
            nodes = []
            for i, coord in enumerate(self.nodes):
                nodes.append(Node(i + 1, coord[0], coord[1], coord[2]))
            
            # 要素オブジェクト作成
            elements = []
            gravity_vec = np.array([0.0, 0.0, -9.81]) if gravity else None
            
            for i, elem in enumerate(self.elems):
                elem_nodes = [nodes[j] for j in elem]
                elements.append(C3D4(i + 1, elem_nodes, young, poisson, density, gravity_vec))
            
            # 境界条件作成
            boundary = Boundary(len(nodes))
            
            # 固定端設定
            for node_id in self.project_data.fixed_nodes:
                boundary.addSPC(node_id, 0.0, 0.0, 0.0)
            
            # 荷重設定
            for force in self.project_data.applied_forces:
                boundary.addForce(force[0], force[1], force[2], force[3])
            
            # LoadManagerからの荷重も適用
            if self.load_manager:
                equivalent_loads = self.load_manager.get_all_equivalent_point_loads()
                for load in equivalent_loads:
                    node_id = load[0] + 1  # ノード番号は0ベースから1ベースに変換
                    fx, fy, fz = load[1], load[2], load[3]
                    boundary.addForce(node_id, fx, fy, fz)
            
            # FEM解析実行
            fem = FEM(nodes, elements, boundary)
            displacement_vec, _ = fem.analysis()
            
            # 変位を2次元配列に変換
            displacement = fem.outputDisplacement()
            
            # 応力計算
            max_stress, _, _ = fem.calculateMaxStress()
            
            # 安全率計算
            safety_factor = self.project_data.calculate_safety_factor(max_stress, self.current_yield_strength)
            
            # 体積比計算（元の体積との比）
            volume_ratio = self.calculate_volume_ratio()
            
            # 変位の最大値計算
            max_displacement = np.max([np.linalg.norm(disp) for disp in displacement])
            
            return max_stress, safety_factor, volume_ratio, displacement, max_displacement
            
        except Exception as e:
            import traceback
            print(f"解析エラー: {e}")
            print(f"詳細: {traceback.format_exc()}")
            return None, None, 1.0, None, None
    
    def analyze_single_case_with_nodes(self, nodes):
        """指定されたノードで単一ケースの解析実行"""
        try:
            # 解析実行（既存のメソッドを利用）
            young = float(self.entry_young.get())
            poisson = float(self.entry_poisson.get())
            density = float(self.entry_density.get())
            gravity = self.var_gravity.get()
            
            # ノードオブジェクト作成
            node_objects = []
            for i, coord in enumerate(nodes):
                node_objects.append(Node(i + 1, coord[0], coord[1], coord[2]))
            
            # 要素オブジェクト作成
            elements = []
            gravity_vec = np.array([0.0, 0.0, -9.81]) if gravity else None
            
            for i, elem in enumerate(self.elems):
                elem_nodes = [node_objects[j] for j in elem]
                elements.append(C3D4(i + 1, elem_nodes, young, poisson, density, gravity_vec))
            
            # 境界条件作成
            boundary = Boundary(len(node_objects))
            
            # 固定端設定
            for node_id in self.project_data.fixed_nodes:
                boundary.addSPC(node_id, 0.0, 0.0, 0.0)
            
            # 荷重設定
            for force in self.project_data.applied_forces:
                boundary.addForce(force[0], force[1], force[2], force[3])
            
            # LoadManagerからの荷重も適用
            if self.load_manager:
                equivalent_loads = self.load_manager.get_all_equivalent_point_loads()
                for load in equivalent_loads:
                    node_id = load[0] + 1  # ノード番号は0ベースから1ベースに変換
                    fx, fy, fz = load[1], load[2], load[3]
                    boundary.addForce(node_id, fx, fy, fz)
            
            # FEM解析実行
            fem = FEM(node_objects, elements, boundary)
            displacement_vec, _ = fem.analysis()
            
            # 変位を2次元配列に変換
            displacement = fem.outputDisplacement()
            
            # 応力計算
            max_stress, _, _ = fem.calculateMaxStress()
            
            # 安全率計算
            safety_factor = self.project_data.calculate_safety_factor(max_stress, self.current_yield_strength)
            
            # 体積比計算（指定されたノードで）
            volume_ratio = self.calculate_volume_ratio_with_nodes(nodes)
            
            # 変位の最大値計算
            max_displacement = np.max([np.linalg.norm(disp) for disp in displacement])
            
            return max_stress, safety_factor, volume_ratio, displacement, max_displacement
            
        except Exception as e:
            import traceback
            print(f"解析エラー: {e}")
            print(f"詳細: {traceback.format_exc()}")
            return None, None, 1.0, None, None
    
    def calculate_volume_ratio(self):
        """現在の形状の体積比を計算"""
        if not hasattr(self, 'original_volume') or self.original_volume == 0:
            return 1.0
        
        current_volume = self.calculate_mesh_volume()
        return current_volume / self.original_volume
    
    def calculate_mesh_volume(self):
        """メッシュの体積を計算（表示用メッシュを使用）"""
        if self.display_nodes is None or self.elems is None:
            return 0.0
        
        # numpy配列であることを確認
        if not isinstance(self.display_nodes, np.ndarray):
            nodes_array = np.array(self.display_nodes)
        else:
            nodes_array = self.display_nodes
        
        total_volume = 0.0
        for elem in self.elems:
            try:
                # 四面体の体積計算
                tetra = nodes_array[elem]
                v1 = tetra[1] - tetra[0]
                v2 = tetra[2] - tetra[0] 
                v3 = tetra[3] - tetra[0]
                volume = abs(np.dot(v1, np.cross(v2, v3))) / 6.0
                total_volume += volume
            except Exception as e:
                print(f"体積計算エラー (要素 {elem}): {e}")
                continue
        
        return total_volume
    
    def calculate_volume_ratio_with_nodes(self, nodes):
        """指定されたノードで体積比を計算"""
        if not hasattr(self, 'original_volume') or self.original_volume == 0:
            return 1.0
        
        current_volume = self.calculate_mesh_volume_with_nodes(nodes)
        return current_volume / self.original_volume
    
    def calculate_mesh_volume_with_nodes(self, nodes):
        """指定されたノードでメッシュの体積を計算"""
        if nodes is None or self.elems is None:
            return 0.0
        
        # numpy配列であることを確認
        if not isinstance(nodes, np.ndarray):
            nodes_array = np.array(nodes)
        else:
            nodes_array = nodes
        
        total_volume = 0.0
        for elem in self.elems:
            try:
                # 四面体の体積計算
                tetra = nodes_array[elem]
                v1 = tetra[1] - tetra[0]
                v2 = tetra[2] - tetra[0] 
                v3 = tetra[3] - tetra[0]
                volume = abs(np.dot(v1, np.cross(v2, v3))) / 6.0
                total_volume += volume
            except Exception as e:
                print(f"体積計算エラー (要素 {elem}): {e}")
                continue
        
        return total_volume
    
    def display_selected_case(self):
        """選択されたケースを表示"""
        selection = self.param_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "ケースを選択してください。")
            return
        
        # 選択されたケースの情報を取得
        item = self.param_tree.item(selection[0])
        values = item['values']
        case_num = int(values[0])
        
        if hasattr(self, 'parametric_results'):
            result = next((r for r in self.parametric_results if r['case'] == case_num), None)
            if result:
                # 表示メッシュをリセットしてからスケール適用
                self.reset_display_mesh()
                self.apply_scale(result['x_scale']/100, result['y_scale']/100, result['z_scale']/100)
                self.draw_mesh()
                
                # 変形表示が可能な場合は変形も表示
                if result.get('displacement') is not None:
                    # 変形表示スケールの入力ダイアログを表示
                    scale_dialog = tk.Toplevel(self.root)
                    scale_dialog.title("変形表示スケール")
                    scale_dialog.geometry("300x150")
                    scale_dialog.transient(self.root)
                    scale_dialog.grab_set()
                    
                    tk.Label(scale_dialog, text=f"ケース {case_num} の変形表示").pack(pady=10)
                    tk.Label(scale_dialog, text="変形スケール倍率:").pack()
                    
                    scale_entry = tk.Entry(scale_dialog, width=15)
                    scale_entry.pack(pady=5)
                    scale_entry.insert(0, "10000")  # デフォルト値
                    scale_entry.focus()
                    
                    result_ref = [result]  # クロージャ用
                    
                    def apply_deformation():
                        try:
                            deform_scale = float(scale_entry.get())
                            self.draw_deformed_shape(result_ref[0]['displacement'], deform_scale)
                            scale_dialog.destroy()
                        except ValueError:
                            messagebox.showerror("エラー", "有効な数値を入力してください")
                    
                    def skip_deformation():
                        scale_dialog.destroy()
                    
                    button_frame = tk.Frame(scale_dialog)
                    button_frame.pack(pady=10)
                    tk.Button(button_frame, text="変形表示", command=apply_deformation).pack(side=tk.LEFT, padx=5)
                    tk.Button(button_frame, text="スキップ", command=skip_deformation).pack(side=tk.LEFT, padx=5)
                    
                    # Enterキーで適用
                    scale_entry.bind('<Return>', lambda e: apply_deformation())
                    
                    info_message = (f"ケース {case_num} を表示しました。\n"
                                  f"スケール: X={result['x_scale']}%, Y={result['y_scale']}%, Z={result['z_scale']}%\n"
                                  f"最大変位: {result.get('max_displacement', 'N/A'):.6f} m\n"
                                  f"最大応力: {result['max_stress']/1e6:.2f} MPa\n"
                                  f"安全率: {result['safety_factor']:.2f}")
                else:
                    info_message = (f"ケース {case_num} を表示しました。\n"
                                  f"スケール: X={result['x_scale']}%, Y={result['y_scale']}%, Z={result['z_scale']}%")
                
                if result.get('displacement') is None:
                    messagebox.showinfo("表示", info_message)
    
    def export_parametric_results(self):
        """パラメトリック解析結果をCSV出力"""
        if not hasattr(self, 'parametric_results'):
            messagebox.showwarning("警告", "パラメトリック解析結果がありません。")
            return
        
        filename = filedialog.asksaveasfilename(
            title="解析結果をCSV保存",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Case', 'X_Scale[%]', 'Y_Scale[%]', 'Z_Scale[%]', 
                                'Max_Stress[MPa]', 'Safety_Factor', 'Volume_Ratio']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for result in self.parametric_results:
                        writer.writerow({
                            'Case': result['case'],
                            'X_Scale[%]': result['x_scale'],
                            'Y_Scale[%]': result['y_scale'],
                            'Z_Scale[%]': result['z_scale'],
                            'Max_Stress[MPa]': result['max_stress']/1e6 if result['max_stress'] else 'N/A',
                            'Safety_Factor': result['safety_factor'] if result['safety_factor'] else 'N/A',
                            'Volume_Ratio': result['volume_ratio']
                        })
                
                messagebox.showinfo("完了", f"CSV出力が完了しました: {filename}")
            except Exception as e:
                messagebox.showerror("エラー", f"CSV出力に失敗しました: {str(e)}")
    
    def run_vibration_analysis(self):
        """振動解析実行"""
        if self.base_nodes is None or self.elems is None:
            messagebox.showerror("エラー", "メッシュが生成されていません。")
            return
        
        if not self.project_data.fixed_nodes:
            messagebox.showerror("エラー", "固定端が設定されていません。")
            return
        
        # 前回の解析結果をクリア
        self.clear_analysis_results()
        self.clear_vibration_display()
        
        # 通常解析の結果もクリア
        self.project_data.displacement = None
        self.project_data.max_displacement = None
        self.project_data.max_stress = None
        self.project_data.safety_factor = None
        
        try:
            num_modes = int(self.vib_num_modes.get())
            if num_modes <= 0:
                messagebox.showerror("エラー", "モード数は正の整数を入力してください。")
                return
        except ValueError:
            messagebox.showerror("エラー", "モード数に有効な数値を入力してください。")
            return
        
        try:
            # 進捗ダイアログ表示
            progress_window = tk.Toplevel(self.root)
            progress_window.title("振動解析実行中")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            tk.Label(progress_window, text="振動解析を実行中...").pack(pady=20)
            progress_window.update()
            
            # 材料物性を取得
            young = float(self.entry_young.get())
            poisson = float(self.entry_poisson.get())
            density = float(self.entry_density.get())
            
            # FEM解析オブジェクトを作成（解析用メッシュを使用）
            boundary = Boundary(len(self.base_nodes))
            
            # 固定端を設定
            for node_id in self.project_data.fixed_nodes:
                boundary.addSPC(node_id + 1, 0.0, 0.0, 0.0)
            
            # C3D4要素を作成（解析用メッシュを使用）
            elems = []
            for i, elem in enumerate(self.elems):
                nodes = [Node(j + 1, self.base_nodes[j, 0], self.base_nodes[j, 1], self.base_nodes[j, 2]) for j in elem]
                c3d4_elem = C3D4(i + 1, nodes, young, poisson, density)
                elems.append(c3d4_elem)
            
            # ノードオブジェクトを作成（解析用メッシュを使用）
            node_objects = [Node(i + 1, self.base_nodes[i, 0], self.base_nodes[i, 1], self.base_nodes[i, 2]) 
                           for i in range(len(self.base_nodes))]
            
            # FEMオブジェクト作成
            fem = FEM(node_objects, elems, boundary)
            
            # 振動解析実行
            eigenvalues, eigenvectors, frequencies = fem.vibrationAnalysis(num_modes)
            
            # 結果を保存
            self.vibration_results = {
                'eigenvalues': eigenvalues,
                'eigenvectors': eigenvectors,
                'frequencies': frequencies,
                'num_modes': num_modes
            }
            
            # 結果をテーブルに表示
            self.display_vibration_results()
            
            progress_window.destroy()
            messagebox.showinfo("完了", f"振動解析が完了しました。{num_modes}個のモードを計算しました。")
            
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("エラー", f"振動解析に失敗しました: {str(e)}")
    
    def display_vibration_results(self):
        """振動解析結果をテーブルに表示"""
        # テーブルをクリア
        for item in self.vib_tree.get_children():
            self.vib_tree.delete(item)
        
        if not hasattr(self, 'vibration_results'):
            return
        
        frequencies = self.vibration_results['frequencies']
        eigenvalues = self.vibration_results['eigenvalues']
        
        for i, freq in enumerate(frequencies):
            mode_num = i + 1
            freq_hz = freq
            freq_rad = freq * 2 * np.pi
            period = 1.0 / freq if freq > 0 else float('inf')
            
            self.vib_tree.insert("", "end", values=(
                mode_num,
                f"{freq_hz:.3f}",
                f"{freq_rad:.3f}",
                f"{period:.6f}" if period != float('inf') else "∞"
            ))
    
    def display_selected_mode(self):
        """選択された固有モードを可視化"""
        selection = self.vib_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "モードを選択してください。")
            return
        
        if not hasattr(self, 'vibration_results'):
            messagebox.showwarning("警告", "振動解析結果がありません。")
            return
        
        try:
            # 選択されたモードを取得
            item = self.vib_tree.item(selection[0])
            mode_num = int(item['values'][0])
            mode_index = mode_num - 1
            
            if mode_index >= len(self.vibration_results['frequencies']):
                messagebox.showerror("エラー", "無効なモードです。")
                return
            
            # 固有ベクトルを取得
            eigenvector = self.vibration_results['eigenvectors'][:, mode_index]
            
            # 3D表示をクリア
            self.ax.clear()
            
            # 元の形状を描画（半透明）
            self.draw_mesh_with_displacement(np.zeros_like(self.nodes), alpha=0.3, color='lightgray')
            
            # 変形した形状を描画（固有モード）
            scale_factor = self.get_mode_scale_factor(eigenvector)
            displacement = self.eigenvector_to_displacement(eigenvector) * scale_factor
            self.draw_mesh_with_displacement(displacement, alpha=0.8, color='red')
            
            # タイトル設定
            freq = self.vibration_results['frequencies'][mode_index]
            self.ax.set_title(f"固有モード {mode_num}: {freq:.3f} Hz")
            
            self.ax.set_xlabel("X [m]")
            self.ax.set_ylabel("Y [m]")
            self.ax.set_zlabel("Z [m]")
            
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("エラー", f"モード表示に失敗しました: {str(e)}")
    
    def eigenvector_to_displacement(self, eigenvector):
        """固有ベクトルを変位配列に変換"""
        displacement = np.zeros((len(self.nodes), 3))
        for i in range(len(self.nodes)):
            displacement[i, 0] = eigenvector[i * 3]
            displacement[i, 1] = eigenvector[i * 3 + 1]
            displacement[i, 2] = eigenvector[i * 3 + 2]
        return displacement
    
    def get_mode_scale_factor(self, eigenvector):
        """固有モード表示のスケールファクターを計算"""
        # 最大変位を取得
        max_displacement = np.max(np.abs(eigenvector))
        if max_displacement == 0:
            return 1.0
        
        # メッシュサイズを取得
        mesh_size = np.max(self.nodes) - np.min(self.nodes)
        
        # 適切なスケールファクターを計算（メッシュサイズの10%程度）
        return (mesh_size * 0.1) / max_displacement
    
    def draw_mesh_with_displacement(self, displacement, alpha=1.0, color='blue'):
        """変位を考慮したメッシュ描画"""
        if displacement is None:
            displacement = np.zeros_like(self.nodes)
        
        # 変位後の節点座標
        deformed_nodes = self.nodes + displacement
        
        # 要素を描画
        for elem in self.elems:
            tetra = deformed_nodes[elem]
            verts = [
                [tetra[0], tetra[1], tetra[2]],
                [tetra[0], tetra[1], tetra[3]],
                [tetra[0], tetra[2], tetra[3]],
                [tetra[1], tetra[2], tetra[3]]
            ]
            collection = Poly3DCollection(verts, edgecolor="k", alpha=alpha, facecolor=color)
            self.ax.add_collection3d(collection)
        
        # 軸スケールを統一
        self.set_equal_axis_scale(deformed_nodes)
    
    def set_equal_axis_scale(self, nodes):
        """3D表示の軸スケールを統一して実際の形状比率を保つ"""
        if nodes is None or len(nodes) == 0:
            return
        
        # 各軸の範囲を計算
        x_min, x_max = np.min(nodes[:, 0]), np.max(nodes[:, 0])
        y_min, y_max = np.min(nodes[:, 1]), np.max(nodes[:, 1])
        z_min, z_max = np.min(nodes[:, 2]), np.max(nodes[:, 2])
        
        # 各軸の範囲を取得
        x_range = x_max - x_min
        y_range = y_max - y_min
        z_range = z_max - z_min
        
        # 最大範囲を取得
        max_range = max(x_range, y_range, z_range)
        
        # ゼロ除算を避ける
        if max_range == 0:
            max_range = 1.0
        
        # 各軸の中心を計算
        x_center = (x_max + x_min) / 2
        y_center = (y_max + y_min) / 2
        z_center = (z_max + z_min) / 2
        
        # 統一されたスケールで軸範囲を設定
        scale_factor = max_range / 2 * 1.1  # 10%のマージンを追加
        
        self.ax.set_xlim(x_center - scale_factor, x_center + scale_factor)
        self.ax.set_ylim(y_center - scale_factor, y_center + scale_factor)
        self.ax.set_zlim(z_center - scale_factor, z_center + scale_factor)
        
        # アスペクト比を統一
        self.ax.set_box_aspect([1,1,1])
    
    def export_vibration_results(self):
        """振動解析結果をCSV出力"""
        if not hasattr(self, 'vibration_results'):
            messagebox.showwarning("警告", "振動解析結果がありません。")
            return
        
        filename = filedialog.asksaveasfilename(
            title="振動解析結果をCSV保存",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Mode', 'Frequency_Hz', 'Angular_Frequency_rad_s', 'Period_s']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    
                    frequencies = self.vibration_results['frequencies']
                    for i, freq in enumerate(frequencies):
                        mode_num = i + 1
                        freq_hz = freq
                        freq_rad = freq * 2 * np.pi
                        period = 1.0 / freq if freq > 0 else float('inf')
                        
                        writer.writerow({
                            'Mode': mode_num,
                            'Frequency_Hz': f"{freq_hz:.6f}",
                            'Angular_Frequency_rad_s': f"{freq_rad:.6f}",
                            'Period_s': f"{period:.6f}" if period != float('inf') else "infinity"
                        })
                
                messagebox.showinfo("完了", f"CSV出力が完了しました: {filename}")
            except Exception as e:
                messagebox.showerror("エラー", f"CSV出力に失敗しました: {str(e)}")

    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EnhancedFEMTool()
    app.run()