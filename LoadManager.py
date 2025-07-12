import numpy as np
from scipy.spatial.distance import cdist

class LoadManager:
    """荷重管理クラス - 面荷重、辺荷重、点荷重を統合管理"""
    
    def __init__(self, nodes, elements):
        self.nodes = nodes
        self.elements = elements
        self.point_loads = []    # [node_id, fx, fy, fz]
        self.edge_loads = []     # [edge_nodes, distributed_force_per_length]
        self.surface_loads = []  # [surface_nodes, distributed_force_per_area]
    
    def add_point_load(self, node_id, fx, fy, fz):
        """点荷重を追加"""
        # 既存の点荷重を削除
        self.point_loads = [load for load in self.point_loads if load[0] != node_id]
        self.point_loads.append([node_id, fx, fy, fz])
    
    def remove_point_load(self, node_id):
        """点荷重を削除"""
        self.point_loads = [load for load in self.point_loads if load[0] != node_id]
    
    def add_edge_load(self, edge_nodes, force_per_length, direction):
        """辺荷重を追加
        
        Args:
            edge_nodes: 辺を構成するノードIDのリスト
            force_per_length: 単位長さあたりの荷重 [N/m]
            direction: 荷重方向ベクトル [fx, fy, fz]
        """
        import copy
        edge_load = {
            'nodes': copy.deepcopy(edge_nodes),  # 深いコピーで参照を切る
            'force_per_length': force_per_length,
            'direction': copy.deepcopy(direction)  # 深いコピーで参照を切る
        }
        self.edge_loads.append(edge_load)
        # デバッグ: 辺荷重追加確認
        print(f"辺荷重追加: ノード{edge_load['nodes']}, 荷重{force_per_length} N/m")
    
    def add_surface_load(self, surface_nodes, force_per_area, direction):
        """面荷重を追加
        
        Args:
            surface_nodes: 面を構成するノードIDのリスト
            force_per_area: 単位面積あたりの荷重 [N/m²]
            direction: 荷重方向ベクトル [fx, fy, fz]
        """
        import copy
        surface_load = {
            'nodes': copy.deepcopy(surface_nodes),  # 深いコピーで参照を切る
            'force_per_area': force_per_area,
            'direction': copy.deepcopy(direction)  # 深いコピーで参照を切る
        }
        self.surface_loads.append(surface_load)
        # デバッグ: 面荷重追加確認
        print(f"面荷重追加: ノード{surface_load['nodes']}, 荷重{force_per_area} N/m²")
    
    def find_coplanar_nodes(self, selected_nodes, tolerance=1e-6):
        """選択されたノードが同一平面上にあるかチェック"""
        if len(selected_nodes) < 4:
            return True  # 3点以下は常に同一平面
        
        # 最初の3点で平面を定義
        p1 = self.nodes[selected_nodes[0]]
        p2 = self.nodes[selected_nodes[1]]
        p3 = self.nodes[selected_nodes[2]]
        
        # 平面の法線ベクトルを計算
        v1 = p2 - p1
        v2 = p3 - p1
        normal = np.cross(v1, v2)
        
        if np.linalg.norm(normal) < tolerance:
            return False  # 最初の3点が一直線上
        
        normal = normal / np.linalg.norm(normal)
        
        # 残りの点が同じ平面上にあるかチェック
        for i in range(3, len(selected_nodes)):
            p = self.nodes[selected_nodes[i]]
            v = p - p1
            distance = abs(np.dot(v, normal))
            if distance > tolerance:
                return False
        
        return True
    
    def find_nodes_on_plane(self, selected_nodes, tolerance=1e-6):
        """選択されたノードからなる平面上にある全てのノードを検出"""
        if len(selected_nodes) < 3:
            return selected_nodes.copy()
        
        # 有効な平面を定義するための3点を探す
        p1 = self.nodes[selected_nodes[0]]
        normal = None
        
        for i in range(1, len(selected_nodes)):
            for j in range(i+1, len(selected_nodes)):
                p2 = self.nodes[selected_nodes[i]]
                p3 = self.nodes[selected_nodes[j]]
                
                # 平面の法線ベクトルを計算
                v1 = p2 - p1
                v2 = p3 - p1
                potential_normal = np.cross(v1, v2)
                
                if np.linalg.norm(potential_normal) > tolerance:
                    # 有効な平面が見つかった
                    normal = potential_normal / np.linalg.norm(potential_normal)
                    break
            
            if normal is not None:
                break
        
        if normal is None:
            # 全ての点が一直線上にある場合
            return selected_nodes.copy()
        
        # 全ノードをチェックして平面上にあるものを見つける
        plane_nodes = []
        for node_id in range(len(self.nodes)):
            p = self.nodes[node_id]
            v = p - p1
            distance = abs(np.dot(v, normal))
            
            if distance <= tolerance:
                plane_nodes.append(node_id)
        
        return sorted(plane_nodes)
    
    def find_collinear_nodes(self, selected_nodes, tolerance=1e-6):
        """選択されたノードが同一直線上にあるかチェック"""
        if len(selected_nodes) < 3:
            return True  # 2点以下は常に一直線
        
        # 最初の2点で直線を定義
        p1 = self.nodes[selected_nodes[0]]
        p2 = self.nodes[selected_nodes[1]]
        direction = p2 - p1
        
        if np.linalg.norm(direction) < tolerance:
            return False  # 最初の2点が同一点
        
        direction = direction / np.linalg.norm(direction)
        
        # 残りの点が同じ直線上にあるかチェック
        for i in range(2, len(selected_nodes)):
            p = self.nodes[selected_nodes[i]]
            v = p - p1
            cross_product = np.cross(v, direction)
            distance = np.linalg.norm(cross_product)
            if distance > tolerance:
                return False
        
        return True
    
    def find_nodes_on_line(self, selected_nodes, tolerance=1e-6):
        """選択されたノードからなる直線上にある全てのノードを検出"""
        if len(selected_nodes) < 2:
            return selected_nodes.copy()
        
        # 最初の2点で直線を定義
        p1 = self.nodes[selected_nodes[0]]
        p2 = self.nodes[selected_nodes[1]]
        direction = p2 - p1
        
        if np.linalg.norm(direction) < tolerance:
            return selected_nodes.copy()  # 2点が同一点の場合
        
        direction = direction / np.linalg.norm(direction)
        
        # 全ノードをチェックして直線上にあるものを見つける
        line_nodes = []
        for node_id in range(len(self.nodes)):
            p = self.nodes[node_id]
            v = p - p1
            
            # 直線からの距離を計算
            cross_product = np.cross(v, direction)
            distance = np.linalg.norm(cross_product)
            
            if distance <= tolerance:
                # 直線の範囲内にあるかもチェック（選択ノードの範囲を超えて拡張）
                line_nodes.append(node_id)
        
        return sorted(line_nodes)
    
    def distribute_edge_load_to_nodes(self, edge_nodes, force_per_length, direction):
        """辺荷重を等価ノード荷重に変換（距離に基づく重み付け）"""
        equivalent_loads = []
        
        print(f"    [DEBUG] distribute_edge_load_to_nodes() 開始")
        print(f"      入力: edge_nodes={edge_nodes}, force_per_length={force_per_length}, direction={direction}")
        
        if len(edge_nodes) < 2:
            print(f"      [DEBUG] エラー: ノード数が不足 ({len(edge_nodes)} < 2)")
            return equivalent_loads
        
        # ノードを線分の順序に並べ替え
        sorted_nodes = self._sort_nodes_along_line(edge_nodes)
        print(f"      [DEBUG] ソート済みノード: {sorted_nodes}")
        
        # 各セグメントの長さを計算
        segment_lengths = []
        total_length = 0
        for i in range(len(sorted_nodes) - 1):
            try:
                p1 = self.nodes[sorted_nodes[i]]
                p2 = self.nodes[sorted_nodes[i + 1]]
                length = np.linalg.norm(p2 - p1)
                segment_lengths.append(length)
                total_length += length
                print(f"      [DEBUG] セグメント{i}: ノード{sorted_nodes[i]}-{sorted_nodes[i+1]}, 長さ={length:.3f}")
            except IndexError as e:
                print(f"      [DEBUG] エラー: ノードインデックス範囲外 - {e}")
                return equivalent_loads
        
        if total_length == 0:
            print(f"      [DEBUG] エラー: 総長さが0")
            return equivalent_loads
        
        total_force = force_per_length * total_length
        force_direction = np.array(direction)
        print(f"      [DEBUG] 総長さ={total_length:.3f}, 総力={total_force:.3f}, 方向={force_direction}")
        
        # 各ノードの荷重配分を距離に基づいて計算
        for i, node_id in enumerate(sorted_nodes):
            weight = 0.0
            
            if i == 0:
                # 最初のノード：隣接セグメントの半分
                weight = segment_lengths[0] / 2.0
            elif i == len(sorted_nodes) - 1:
                # 最後のノード：隣接セグメントの半分
                weight = segment_lengths[i-1] / 2.0
            else:
                # 中間ノード：両隣のセグメントの半分ずつ
                weight = (segment_lengths[i-1] + segment_lengths[i]) / 2.0
            
            # 重みに基づいて力を配分
            weight_ratio = weight / total_length
            node_force = force_direction * total_force * weight_ratio
            
            equivalent_loads.append([node_id, node_force[0], node_force[1], node_force[2]])
            print(f"      [DEBUG] ノード{node_id}: 重み={weight:.3f}, 比率={weight_ratio:.3f}, 力=({node_force[0]:.2f}, {node_force[1]:.2f}, {node_force[2]:.2f})")
        
        print(f"    [DEBUG] distribute_edge_load_to_nodes() 完了, 結果数={len(equivalent_loads)}")
        return equivalent_loads
    
    def distribute_surface_load_to_nodes(self, surface_nodes, force_per_area, direction):
        """面荷重を等価ノード荷重に変換（面積に基づく重み付け）"""
        equivalent_loads = []
        
        if len(surface_nodes) < 3:
            return equivalent_loads
        
        # 多角形の重心を計算
        centroid = np.mean([self.nodes[node_id] for node_id in surface_nodes], axis=0)
        
        # 各ノードに対する寄与面積を計算
        node_areas = {}
        total_area = 0
        
        # 重心を中心とした三角形分割で各ノードの寄与面積を計算
        for i in range(len(surface_nodes)):
            j = (i + 1) % len(surface_nodes)
            
            p1 = self.nodes[surface_nodes[i]]
            p2 = self.nodes[surface_nodes[j]]
            
            # 三角形の面積
            v1 = p1 - centroid
            v2 = p2 - centroid
            triangle_area = 0.5 * np.linalg.norm(np.cross(v1, v2))
            total_area += triangle_area
            
            # 各ノードに面積を配分（三角形の面積の1/3ずつ）
            triangle_contribution = triangle_area / 3.0
            
            for node_id in [surface_nodes[i], surface_nodes[j]]:
                if node_id not in node_areas:
                    node_areas[node_id] = 0
                node_areas[node_id] += triangle_contribution
        
        # 重心への寄与も考慮（全ての三角形の重心部分）
        centroid_area = total_area / 3.0
        for node_id in surface_nodes:
            node_areas[node_id] += centroid_area / len(surface_nodes)
        
        if total_area == 0:
            return equivalent_loads
        
        total_force = force_per_area * total_area
        force_direction = np.array(direction)
        
        # 各ノードの荷重配分を面積比に基づいて計算
        for node_id in surface_nodes:
            area_ratio = node_areas[node_id] / sum(node_areas.values())
            node_force = force_direction * total_force * area_ratio
            
            equivalent_loads.append([node_id, node_force[0], node_force[1], node_force[2]])
        
        return equivalent_loads
    
    def _sort_nodes_along_line(self, node_ids):
        """ノードを直線に沿って並べ替え"""
        if len(node_ids) <= 2:
            return node_ids
        
        # 最初のノードから開始
        sorted_nodes = [node_ids[0]]
        remaining_nodes = node_ids[1:]
        
        while remaining_nodes:
            last_node = sorted_nodes[-1]
            last_pos = self.nodes[last_node]
            
            # 最も近いノードを見つける
            min_distance = float('inf')
            closest_node = None
            
            for node_id in remaining_nodes:
                pos = self.nodes[node_id]
                distance = np.linalg.norm(pos - last_pos)
                if distance < min_distance:
                    min_distance = distance
                    closest_node = node_id
            
            sorted_nodes.append(closest_node)
            remaining_nodes.remove(closest_node)
        
        return sorted_nodes
    
    def _calculate_polygon_area(self, node_ids):
        """多角形の面積を計算（3D空間での投影面積）"""
        if len(node_ids) < 3:
            return 0
        
        # 多角形の重心を計算
        centroid = np.mean([self.nodes[node_id] for node_id in node_ids], axis=0)
        
        # 三角分割して面積を計算
        total_area = 0
        for i in range(len(node_ids)):
            j = (i + 1) % len(node_ids)
            
            p1 = self.nodes[node_ids[i]]
            p2 = self.nodes[node_ids[j]]
            
            # 三角形の面積
            v1 = p1 - centroid
            v2 = p2 - centroid
            triangle_area = 0.5 * np.linalg.norm(np.cross(v1, v2))
            total_area += triangle_area
        
        return total_area
    
    def get_all_equivalent_point_loads(self):
        """全ての荷重を等価点荷重として取得"""
        all_loads = []
        
        print(f"  [DEBUG] get_all_equivalent_point_loads() 開始")
        print(f"  [DEBUG] 点荷重数: {len(self.point_loads)}")
        print(f"  [DEBUG] 辺荷重数: {len(self.edge_loads)}")
        print(f"  [DEBUG] 面荷重数: {len(self.surface_loads)}")
        
        # 点荷重をそのまま追加
        all_loads.extend(self.point_loads)
        print(f"  [DEBUG] 点荷重追加後のall_loads数: {len(all_loads)}")
        
        # 辺荷重を等価点荷重に変換して追加
        for i, edge_load in enumerate(self.edge_loads):
            print(f"  [DEBUG] 辺荷重{i+1}を処理中:")
            print(f"    ノード: {edge_load['nodes']}")
            print(f"    単位長さ荷重: {edge_load['force_per_length']}")
            print(f"    方向: {edge_load['direction']}")
            
            equivalent_loads = self.distribute_edge_load_to_nodes(
                edge_load['nodes'],
                edge_load['force_per_length'],
                edge_load['direction']
            )
            print(f"    等価点荷重数: {len(equivalent_loads)}")
            for j, load in enumerate(equivalent_loads):
                print(f"      {j+1}. ノード{load[0]}: ({load[1]:.2f}, {load[2]:.2f}, {load[3]:.2f}) N")
            
            all_loads.extend(equivalent_loads)
        
        print(f"  [DEBUG] 辺荷重処理後のall_loads数: {len(all_loads)}")
        
        # 面荷重を等価点荷重に変換して追加
        for surface_load in self.surface_loads:
            equivalent_loads = self.distribute_surface_load_to_nodes(
                surface_load['nodes'],
                surface_load['force_per_area'],
                surface_load['direction']
            )
            all_loads.extend(equivalent_loads)
        
        print(f"  [DEBUG] 面荷重処理後のall_loads数: {len(all_loads)}")
        
        # 同一ノードの荷重をマージ
        merged_loads = {}
        for load in all_loads:
            node_id = load[0]
            if node_id in merged_loads:
                merged_loads[node_id][1] += load[1]
                merged_loads[node_id][2] += load[2]
                merged_loads[node_id][3] += load[3]
            else:
                merged_loads[node_id] = [node_id, load[1], load[2], load[3]]
        
        result = list(merged_loads.values())
        print(f"  [DEBUG] マージ後の最終結果数: {len(result)}")
        
        return result
    
    def clear_all_loads(self):
        """全ての荷重をクリア"""
        self.point_loads.clear()
        self.edge_loads.clear()
        self.surface_loads.clear()
    
    def get_load_summary(self):
        """荷重の概要を取得"""
        summary = {
            'point_loads': len(self.point_loads),
            'edge_loads': len(self.edge_loads),
            'surface_loads': len(self.surface_loads),
            'total_equivalent_loads': len(self.get_all_equivalent_point_loads())
        }
        return summary
    
    def update_geometry(self, new_nodes, new_elements):
        """ノードと要素を更新（荷重情報は保持）"""
        self.nodes = new_nodes
        self.elements = new_elements
        # 荷重情報はそのまま保持される
    
    def backup_loads(self):
        """荷重情報をバックアップ"""
        import copy
        backup = {
            'point_loads': copy.deepcopy(self.point_loads),
            'edge_loads': copy.deepcopy(self.edge_loads),
            'surface_loads': copy.deepcopy(self.surface_loads)
        }
        print(f"[DEBUG] backup_loads() 実行:")
        print(f"  点荷重: {len(self.point_loads)}個")
        print(f"  辺荷重: {len(self.edge_loads)}個")
        for i, edge_load in enumerate(self.edge_loads):
            print(f"    辺荷重{i+1}: ノード{edge_load['nodes']}, 荷重{edge_load['force_per_length']}")
        print(f"  面荷重: {len(self.surface_loads)}個")
        return backup
    
    def restore_loads(self, backup):
        """荷重情報を復元"""
        print(f"[DEBUG] restore_loads() 実行:")
        print(f"  復元前 - 点荷重: {len(self.point_loads)}個, 辺荷重: {len(self.edge_loads)}個, 面荷重: {len(self.surface_loads)}個")
        
        self.point_loads = backup['point_loads']
        self.edge_loads = backup['edge_loads']
        self.surface_loads = backup['surface_loads']
        
        print(f"  復元後 - 点荷重: {len(self.point_loads)}個, 辺荷重: {len(self.edge_loads)}個, 面荷重: {len(self.surface_loads)}個")
        for i, edge_load in enumerate(self.edge_loads):
            print(f"    辺荷重{i+1}: ノード{edge_load['nodes']}, 荷重{edge_load['force_per_length']}")