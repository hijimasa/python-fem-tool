import numpy as np
import tetgen
from stl import mesh
import tempfile
import os

class GeometryGenerator:
    """基本的な3D形状を生成するクラス"""
    
    @staticmethod
    def create_rectangular_block(length, width, height, mesh_size=None):
        """直方体を生成
        
        Args:
            length: 長さ (X方向)
            width: 幅 (Y方向) 
            height: 高さ (Z方向)
            mesh_size: メッシュサイズ (Noneの場合は自動)
        
        Returns:
            nodes, elements: ノード座標とテトラヘドロン要素
        """
        # 直方体の8つの頂点を定義
        vertices = np.array([
            [0, 0, 0],          # 0: 原点
            [length, 0, 0],     # 1: X方向
            [length, width, 0], # 2: XY平面
            [0, width, 0],      # 3: Y方向
            [0, 0, height],     # 4: Z方向
            [length, 0, height],# 5: XZ平面
            [length, width, height], # 6: 対角
            [0, width, height]  # 7: YZ平面
        ])
        
        # 直方体の面を三角形で定義（各面を2つの三角形に分割）
        faces = np.array([
            # 底面 (Z=0)
            [0, 1, 2], [0, 2, 3],
            # 上面 (Z=height)
            [4, 7, 6], [4, 6, 5],
            # 前面 (Y=0)
            [0, 4, 5], [0, 5, 1],
            # 後面 (Y=width)
            [2, 6, 7], [2, 7, 3],
            # 左面 (X=0)
            [0, 3, 7], [0, 7, 4],
            # 右面 (X=length)
            [1, 5, 6], [1, 6, 2]
        ])
        
        # TetGenでテトラヘドロンメッシュを生成
        tet = tetgen.TetGen(vertices, faces)
        
        # メッシュサイズの設定
        if mesh_size:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5, 
                                               maxvolume=mesh_size**3)
        else:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5)
        
        return nodes, elements
    
    @staticmethod
    def create_cylinder(radius, height, divisions=16, mesh_size=None):
        """円柱を生成
        
        Args:
            radius: 半径
            height: 高さ
            divisions: 円周方向の分割数
            mesh_size: メッシュサイズ
        
        Returns:
            nodes, elements: ノード座標とテトラヘドロン要素
        """
        vertices = []
        faces = []
        
        # 円柱の上面と下面の中心点
        vertices.append([0, 0, 0])        # 下面中心 (index 0)
        vertices.append([0, 0, height])   # 上面中心 (index 1)
        
        # 円周上の点を生成
        for i in range(divisions):
            angle = 2 * np.pi * i / divisions
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            vertices.append([x, y, 0])      # 下面の円周上の点
            vertices.append([x, y, height]) # 上面の円周上の点
        
        vertices = np.array(vertices)
        
        # 面を定義
        for i in range(divisions):
            next_i = (i + 1) % divisions
            
            # 下面の三角形
            bottom_1 = 2 + i * 2
            bottom_2 = 2 + next_i * 2
            faces.append([0, bottom_1, bottom_2])
            
            # 上面の三角形
            top_1 = 2 + i * 2 + 1
            top_2 = 2 + next_i * 2 + 1
            faces.append([1, top_2, top_1])
            
            # 側面の四角形（2つの三角形に分割）
            faces.append([bottom_1, top_1, top_2])
            faces.append([bottom_1, top_2, bottom_2])
        
        faces = np.array(faces)
        
        # TetGenでメッシュ生成
        tet = tetgen.TetGen(vertices, faces)
        
        if mesh_size:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5,
                                               maxvolume=mesh_size**3)
        else:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5)
        
        return nodes, elements
    
    @staticmethod
    def create_hollow_cylinder(outer_radius, inner_radius, height, divisions=16, mesh_size=None):
        """円筒（中空円柱）を生成
        
        Args:
            outer_radius: 外径
            inner_radius: 内径
            height: 高さ
            divisions: 円周方向の分割数
            mesh_size: メッシュサイズ
        
        Returns:
            nodes, elements: ノード座標とテトラヘドロン要素
        """
        vertices = []
        faces = []
        
        # 外側の円周上の点
        for i in range(divisions):
            angle = 2 * np.pi * i / divisions
            x_outer = outer_radius * np.cos(angle)
            y_outer = outer_radius * np.sin(angle)
            x_inner = inner_radius * np.cos(angle)
            y_inner = inner_radius * np.sin(angle)
            
            # 下面
            vertices.append([x_outer, y_outer, 0])      # 外側下
            vertices.append([x_inner, y_inner, 0])      # 内側下
            # 上面
            vertices.append([x_outer, y_outer, height]) # 外側上
            vertices.append([x_inner, y_inner, height]) # 内側上
        
        vertices = np.array(vertices)
        
        # 面を定義
        for i in range(divisions):
            next_i = (i + 1) % divisions
            
            # 各点のインデックス
            outer_bottom = i * 4
            inner_bottom = i * 4 + 1
            outer_top = i * 4 + 2
            inner_top = i * 4 + 3
            
            next_outer_bottom = next_i * 4
            next_inner_bottom = next_i * 4 + 1
            next_outer_top = next_i * 4 + 2
            next_inner_top = next_i * 4 + 3
            
            # 下面（環状）
            faces.append([outer_bottom, inner_bottom, next_inner_bottom])
            faces.append([outer_bottom, next_inner_bottom, next_outer_bottom])
            
            # 上面（環状）
            faces.append([outer_top, next_inner_top, inner_top])
            faces.append([outer_top, next_outer_top, next_inner_top])
            
            # 外側面
            faces.append([outer_bottom, outer_top, next_outer_top])
            faces.append([outer_bottom, next_outer_top, next_outer_bottom])
            
            # 内側面
            faces.append([inner_bottom, next_inner_top, inner_top])
            faces.append([inner_bottom, next_inner_bottom, next_inner_top])
        
        faces = np.array(faces)
        
        # TetGenでメッシュ生成
        tet = tetgen.TetGen(vertices, faces)
        
        if mesh_size:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5,
                                               maxvolume=mesh_size**3)
        else:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5)
        
        return nodes, elements
    
    @staticmethod
    def create_l_shape(width, height, thickness, length, mesh_size=None):
        """L字断面を生成
        
        Args:
            width: 幅
            height: 高さ
            thickness: 厚さ
            length: 長さ（押し出し方向）
            mesh_size: メッシュサイズ
        
        Returns:
            nodes, elements: ノード座標とテトラヘドロン要素
        """
        # L字断面の頂点を定義（Z方向に押し出し）
        vertices = []
        
        # Z=0 の断面
        z0_points = [
            [0, 0],                      # 0: 原点
            [width, 0],                  # 1: 底辺右端
            [width, thickness],          # 2: 底辺内側右端
            [thickness, thickness],      # 3: 内側角
            [thickness, height],         # 4: 縦辺内側上端
            [0, height]                  # 5: 縦辺外側上端
        ]
        
        # Z=0 と Z=length の両方の面に頂点を追加
        for z in [0, length]:
            for point in z0_points:
                vertices.append([point[0], point[1], z])
        
        vertices = np.array(vertices)
        
        faces = []
        
        # 前面（Z=0）と後面（Z=length）
        front_face = [0, 1, 2, 3, 4, 5]  # Z=0の頂点
        back_face = [6, 7, 8, 9, 10, 11] # Z=lengthの頂点
        
        # 前面を三角形に分割
        faces.extend([
            [0, 1, 2], [0, 2, 5],
            [2, 3, 4], [2, 4, 5]
        ])
        
        # 後面を三角形に分割（法線方向を逆に）
        faces.extend([
            [6, 8, 7], [6, 11, 8],
            [8, 10, 9], [8, 11, 10]
        ])
        
        # 側面
        for i in range(6):
            next_i = (i + 1) % 6
            # 側面の四角形を2つの三角形に分割
            faces.append([i, i + 6, next_i + 6])
            faces.append([i, next_i + 6, next_i])
        
        faces = np.array(faces)
        
        # TetGenでメッシュ生成
        tet = tetgen.TetGen(vertices, faces)
        
        if mesh_size:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5,
                                               maxvolume=mesh_size**3)
        else:
            nodes, elements = tet.tetrahedralize(order=1, mindihedral=20, minratio=1.5)
        
        return nodes, elements
    
    @staticmethod
    def save_as_stl(nodes, faces, filename):
        """生成した形状をSTLファイルとして保存
        
        Args:
            nodes: 頂点座標
            faces: 面の定義
            filename: 保存するファイル名
        """
        # STLメッシュオブジェクトを作成
        stl_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
        
        for i, face in enumerate(faces):
            for j in range(3):
                stl_mesh.vectors[i][j] = nodes[face[j]]
        
        # ファイルに保存
        stl_mesh.save(filename)
    
    @staticmethod
    def get_geometry_info(geometry_type, **params):
        """形状の情報を取得"""
        info = {
            'type': geometry_type,
            'parameters': params
        }
        
        if geometry_type == 'rectangular_block':
            volume = params['length'] * params['width'] * params['height']
            surface_area = 2 * (params['length'] * params['width'] + 
                               params['width'] * params['height'] + 
                               params['height'] * params['length'])
            info.update({
                'volume': volume,
                'surface_area': surface_area
            })
        
        elif geometry_type == 'cylinder':
            volume = np.pi * params['radius']**2 * params['height']
            surface_area = 2 * np.pi * params['radius'] * (params['radius'] + params['height'])
            info.update({
                'volume': volume,
                'surface_area': surface_area
            })
        
        elif geometry_type == 'hollow_cylinder':
            volume = np.pi * (params['outer_radius']**2 - params['inner_radius']**2) * params['height']
            outer_surface = 2 * np.pi * params['outer_radius'] * params['height']
            inner_surface = 2 * np.pi * params['inner_radius'] * params['height']
            end_surface = 2 * np.pi * (params['outer_radius']**2 - params['inner_radius']**2)
            surface_area = outer_surface + inner_surface + end_surface
            info.update({
                'volume': volume,
                'surface_area': surface_area
            })
        
        return info