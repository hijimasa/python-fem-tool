import json
import numpy as np
import pickle
from datetime import datetime

class ProjectData:
    """FEM解析プロジェクトのデータを管理するクラス"""
    
    def __init__(self):
        self.project_name = ""
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()
        
        # 形状データ
        self.stl_file_path = ""
        self.nodes = None
        self.elements = None
        
        # 境界条件
        self.fixed_nodes = []  # 固定端ノード番号のリスト
        self.applied_forces = []  # [node_id, fx, fy, fz]の形式
        
        # 材料物性
        self.young_modulus = 210e9  # Pa
        self.poisson_ratio = 0.3
        self.density = 7850.0  # kg/m³
        self.gravity_enabled = False
        
        # 解析設定
        self.display_scale = 10000.0
        
        # 解析結果
        self.displacement = None
        self.stress = None
        self.reaction_forces = None
        self.max_displacement = None
        self.max_stress = None
        self.safety_factor = None
        
    def save_project(self, file_path):
        """プロジェクトをファイルに保存"""
        self.modified_at = datetime.now().isoformat()
        
        project_dict = {
            'project_name': self.project_name,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'stl_file_path': self.stl_file_path,
            'fixed_nodes': self.fixed_nodes,
            'applied_forces': self.applied_forces,
            'young_modulus': self.young_modulus,
            'poisson_ratio': self.poisson_ratio,
            'density': self.density,
            'gravity_enabled': self.gravity_enabled,
            'display_scale': self.display_scale,
            'max_displacement': self.max_displacement,
            'max_stress': self.max_stress,
            'safety_factor': self.safety_factor
        }
        
        # numpyデータは別途pickleで保存
        numpy_data = {
            'nodes': self.nodes,
            'elements': self.elements,
            'displacement': self.displacement,
            'stress': self.stress,
            'reaction_forces': self.reaction_forces
        }
        
        # JSONファイルとPickleファイルで保存
        with open(file_path + '.json', 'w', encoding='utf-8') as f:
            json.dump(project_dict, f, indent=2, ensure_ascii=False)
            
        with open(file_path + '.pkl', 'wb') as f:
            pickle.dump(numpy_data, f)
    
    def load_project(self, file_path):
        """プロジェクトをファイルから読み込み"""
        # JSONファイルから基本データを読み込み
        with open(file_path + '.json', 'r', encoding='utf-8') as f:
            project_dict = json.load(f)
            
        self.project_name = project_dict.get('project_name', "")
        self.created_at = project_dict.get('created_at', "")
        self.modified_at = project_dict.get('modified_at', "")
        self.stl_file_path = project_dict.get('stl_file_path', "")
        self.fixed_nodes = project_dict.get('fixed_nodes', [])
        self.applied_forces = project_dict.get('applied_forces', [])
        self.young_modulus = project_dict.get('young_modulus', 210e9)
        self.poisson_ratio = project_dict.get('poisson_ratio', 0.3)
        self.density = project_dict.get('density', 7850.0)
        self.gravity_enabled = project_dict.get('gravity_enabled', False)
        self.display_scale = project_dict.get('display_scale', 10000.0)
        self.max_displacement = project_dict.get('max_displacement', None)
        self.max_stress = project_dict.get('max_stress', None)
        self.safety_factor = project_dict.get('safety_factor', None)
        
        # Pickleファイルからnumpyデータを読み込み
        try:
            with open(file_path + '.pkl', 'rb') as f:
                numpy_data = pickle.load(f)
                
            self.nodes = numpy_data.get('nodes', None)
            self.elements = numpy_data.get('elements', None)
            self.displacement = numpy_data.get('displacement', None)
            self.stress = numpy_data.get('stress', None)
            self.reaction_forces = numpy_data.get('reaction_forces', None)
        except FileNotFoundError:
            pass
    
    def update_material_properties(self, young=None, poisson=None, density=None, gravity=None):
        """材料物性を更新"""
        if young is not None:
            self.young_modulus = young
        if poisson is not None:
            self.poisson_ratio = poisson
        if density is not None:
            self.density = density
        if gravity is not None:
            self.gravity_enabled = gravity
    
    def add_fixed_node(self, node_id):
        """固定端ノードを追加"""
        if node_id not in self.fixed_nodes:
            self.fixed_nodes.append(node_id)
    
    def remove_fixed_node(self, node_id):
        """固定端ノードを削除"""
        if node_id in self.fixed_nodes:
            self.fixed_nodes.remove(node_id)
    
    def add_force(self, node_id, fx, fy, fz):
        """力点を追加"""
        # 既存の力を削除
        self.applied_forces = [f for f in self.applied_forces if f[0] != node_id]
        self.applied_forces.append([node_id, fx, fy, fz])
    
    def remove_force(self, node_id):
        """力点を削除"""
        self.applied_forces = [f for f in self.applied_forces if f[0] != node_id]
    
    def calculate_results_summary(self, displacement, stress_data=None, material_properties=None):
        """解析結果のサマリーを計算"""
        if displacement is not None:
            # 最大変位を計算
            displacements_magnitude = []
            for disp in displacement:
                magnitude = np.sqrt(disp[0]**2 + disp[1]**2 + disp[2]**2)
                displacements_magnitude.append(magnitude)
            self.max_displacement = max(displacements_magnitude)
        
        if stress_data is not None:
            self.max_stress = max(stress_data) if len(stress_data) > 0 else None
            
            # 安全率を計算
            yield_strength = None
            if material_properties and 'yield_strength' in material_properties:
                yield_strength = material_properties['yield_strength']
            else:
                # デフォルト値（一般的な鋼材）
                yield_strength = 250e6  # Pa
            
            if self.max_stress and self.max_stress > 0 and yield_strength:
                self.safety_factor = yield_strength / self.max_stress
            else:
                self.safety_factor = None
        
        self.displacement = displacement
        self.stress = stress_data
    
    def calculate_safety_factor(self, max_stress, yield_strength):
        """安全率を計算
        
        Args:
            max_stress: 最大応力 [Pa]
            yield_strength: 材料の降伏応力 [Pa]
            
        Returns:
            safety_factor: 安全率
        """
        if max_stress is None or max_stress <= 0:
            return None
        
        if yield_strength is None or yield_strength <= 0:
            return None
        
        return yield_strength / max_stress