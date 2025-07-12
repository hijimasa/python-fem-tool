import json
import os

class MaterialDatabase:
    """材料データベースを管理するクラス"""
    
    def __init__(self):
        self.materials = self._load_default_materials()
    
    def _load_default_materials(self):
        """デフォルトの材料データを定義"""
        return {
            "構造用鋼材": {
                "SS400": {
                    "name": "一般構造用圧延鋼材 SS400",
                    "young_modulus": 205e9,  # Pa
                    "poisson_ratio": 0.3,
                    "density": 7850,  # kg/m³
                    "yield_strength": 245e6,  # Pa
                    "tensile_strength": 400e6,  # Pa
                    "description": "最も一般的な構造用鋼材"
                },
                "S45C": {
                    "name": "機械構造用炭素鋼 S45C",
                    "young_modulus": 206e9,
                    "poisson_ratio": 0.3,
                    "density": 7850,
                    "yield_strength": 370e6,
                    "tensile_strength": 690e6,
                    "description": "中炭素鋼、機械部品に多用"
                },
                "SUS304": {
                    "name": "ステンレス鋼 SUS304",
                    "young_modulus": 200e9,
                    "poisson_ratio": 0.3,
                    "density": 8000,
                    "yield_strength": 205e6,
                    "tensile_strength": 520e6,
                    "description": "最も一般的なオーステナイト系ステンレス鋼"
                }
            },
            "アルミニウム合金": {
                "A5052": {
                    "name": "アルミニウム合金 A5052",
                    "young_modulus": 70e9,
                    "poisson_ratio": 0.33,
                    "density": 2680,
                    "yield_strength": 215e6,
                    "tensile_strength": 260e6,
                    "description": "中程度の強度、耐食性良好"
                },
                "A6061": {
                    "name": "アルミニウム合金 A6061",
                    "young_modulus": 69e9,
                    "poisson_ratio": 0.33,
                    "density": 2700,
                    "yield_strength": 276e6,
                    "tensile_strength": 310e6,
                    "description": "熱処理型合金、構造材として多用"
                },
                "A7075": {
                    "name": "アルミニウム合金 A7075",
                    "young_modulus": 72e9,
                    "poisson_ratio": 0.33,
                    "density": 2810,
                    "yield_strength": 503e6,
                    "tensile_strength": 572e6,
                    "description": "超々ジュラルミン、航空機材料"
                }
            },
            "銅合金": {
                "C1020": {
                    "name": "無酸素銅 C1020",
                    "young_modulus": 110e9,
                    "poisson_ratio": 0.34,
                    "density": 8940,
                    "yield_strength": 60e6,
                    "tensile_strength": 220e6,
                    "description": "高純度銅、電気・電子部品"
                },
                "C2600": {
                    "name": "黄銅 C2600",
                    "young_modulus": 100e9,
                    "poisson_ratio": 0.34,
                    "density": 8530,
                    "yield_strength": 124e6,
                    "tensile_strength": 270e6,
                    "description": "七三黄銅、装飾品・楽器"
                }
            },
            "樹脂材料": {
                "ABS": {
                    "name": "ABS樹脂",
                    "young_modulus": 2.3e9,
                    "poisson_ratio": 0.35,
                    "density": 1050,
                    "yield_strength": 40e6,
                    "tensile_strength": 45e6,
                    "description": "汎用エンジニアリングプラスチック"
                },
                "POM": {
                    "name": "ポリアセタール（POM）",
                    "young_modulus": 3.1e9,
                    "poisson_ratio": 0.35,
                    "density": 1410,
                    "yield_strength": 65e6,
                    "tensile_strength": 70e6,
                    "description": "機械的性質良好、歯車等に使用"
                },
                "PC": {
                    "name": "ポリカーボネート（PC）",
                    "young_modulus": 2.4e9,
                    "poisson_ratio": 0.37,
                    "density": 1200,
                    "yield_strength": 60e6,
                    "tensile_strength": 65e6,
                    "description": "透明性・耐衝撃性優秀"
                }
            },
            "複合材料": {
                "CFRP": {
                    "name": "炭素繊維強化プラスチック（CFRP）",
                    "young_modulus": 150e9,
                    "poisson_ratio": 0.3,
                    "density": 1600,
                    "yield_strength": 1500e6,
                    "tensile_strength": 1800e6,
                    "description": "軽量高強度、航空宇宙分野"
                },
                "GFRP": {
                    "name": "ガラス繊維強化プラスチック（GFRP）",
                    "young_modulus": 40e9,
                    "poisson_ratio": 0.25,
                    "density": 1800,
                    "yield_strength": 500e6,
                    "tensile_strength": 600e6,
                    "description": "コストパフォーマンス良好"
                }
            }
        }
    
    def get_categories(self):
        """材料カテゴリ一覧を取得"""
        return list(self.materials.keys())
    
    def get_materials_in_category(self, category):
        """指定カテゴリの材料一覧を取得"""
        if category in self.materials:
            return list(self.materials[category].keys())
        return []
    
    def get_material_properties(self, category, material_name):
        """指定材料の物性値を取得"""
        if category in self.materials and material_name in self.materials[category]:
            return self.materials[category][material_name]
        return None
    
    def get_all_materials_flat(self):
        """全材料をフラットなリストで取得"""
        flat_list = []
        for category, materials in self.materials.items():
            for material_name, properties in materials.items():
                flat_list.append({
                    'category': category,
                    'name': material_name,
                    'full_name': properties['name'],
                    'properties': properties
                })
        return flat_list
    
    def add_material(self, category, material_name, properties):
        """新しい材料を追加"""
        if category not in self.materials:
            self.materials[category] = {}
        
        self.materials[category][material_name] = properties
    
    def save_to_file(self, filename):
        """材料データベースをファイルに保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.materials, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filename):
        """材料データベースをファイルから読み込み"""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                self.materials = json.load(f)
    
    def search_materials(self, search_term):
        """材料名で検索"""
        results = []
        search_term = search_term.lower()
        
        for category, materials in self.materials.items():
            for material_name, properties in materials.items():
                if (search_term in material_name.lower() or 
                    search_term in properties['name'].lower() or
                    search_term in properties.get('description', '').lower()):
                    
                    results.append({
                        'category': category,
                        'name': material_name,
                        'full_name': properties['name'],
                        'properties': properties
                    })
        
        return results
    
    def get_material_summary(self, category, material_name):
        """材料の簡単な説明文を生成"""
        material = self.get_material_properties(category, material_name)
        if not material:
            return ""
        
        summary = f"""
材料名: {material['name']}
ヤング率: {material['young_modulus']:.2e} Pa
ポアソン比: {material['poisson_ratio']}
密度: {material['density']} kg/m³
降伏強度: {material['yield_strength']:.2e} Pa
引張強度: {material['tensile_strength']:.2e} Pa
説明: {material.get('description', '説明なし')}
        """
        return summary.strip()
    
    def calculate_safety_factor(self, category, material_name, max_stress):
        """安全率を計算"""
        material = self.get_material_properties(category, material_name)
        if not material or not max_stress or max_stress <= 0:
            return None
        
        yield_strength = material.get('yield_strength', 0)
        if yield_strength > 0:
            return yield_strength / max_stress
        return None