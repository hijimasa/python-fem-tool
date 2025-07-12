import numpy as np
import numpy.linalg as LA
from Dmatrix import Dmatrix
from Node import Node

# 四面体4節点要素のクラス
class C3D4:
    # コンストラクタ
    # no           : 要素番号
    # nodes        : 節点の集合(Node型のリスト)
    # young        : ヤング率
    # poisson      : ポアソン比
    # density      : 密度
    # vecGravity   : 重力加速度のベクトル(np.array型)
    def __init__(self, no, nodes, young, poisson, density, vecGravity = None):
        
        # インスタンス変数を定義する
        self.nodeNum = 4               # 節点の数
        self.nodeDof = 3               # 節点の自由度
        self.no = no                   # 要素番号
        self.nodes = nodes             # nodesは反時計回りの順番になっている前提(Node2d型のリスト形式)
        self.young = young             # ヤング率
        self.poisson = poisson         # ポアソン比
        self.density = density         # 密度
        self.vecGravity = vecGravity   # 重力加速度のベクトル(np.array型)
        self.ipNum = 1                 # 積分点の数
        self.w = 1.0 / 6.0             # 積分点の重み係数
        self.ai = 1.0 / 4.0            # 積分点の座標(a,b,c座標系)
        self.bi = 1.0 / 4.0            # 積分点の座標(a,b,c座標系)
        self.ci = 1.0 / 4.0            # 積分点の座標(a,b,c座標系)

    # 要素剛性マトリクスKeを作成する
    def makeKematrix(self):

        # ヤコビ行列を計算する
        matJ = self.makeJmatrix()

        # Bマトリクスを計算する
        matB = self.makeBmatrix()
        
        # Dマトリクスを計算する
        matD = self.makeDmatrix()

        # Ketマトリクスをガウス積分で計算する
        matKet = self.w * matB.T @ matD @ matB * LA.det(matJ)

        return matKet

    # Dマトリクスを作成する
    def makeDmatrix(self):
        
        matD = Dmatrix(self.young, self.poisson).makeDematrix()
        return matD

    # ヤコビ行列を計算する
    def makeJmatrix(self):
        
        dxda = -self.nodes[0].x + self.nodes[1].x
        dyda = -self.nodes[0].y + self.nodes[1].y
        dzda = -self.nodes[0].z + self.nodes[1].z
        dxdb = -self.nodes[0].x + self.nodes[2].x
        dydb = -self.nodes[0].y + self.nodes[2].y
        dzdb = -self.nodes[0].z + self.nodes[2].z
        dxdc = -self.nodes[0].x + self.nodes[3].x
        dydc = -self.nodes[0].y + self.nodes[3].y
        dzdc = -self.nodes[0].z + self.nodes[3].z

        matJ = np.array([[dxda, dyda, dzda],
                         [dxdb, dydb, dzdb],
                         [dxdc, dydc, dzdc]])        

        # ヤコビアンが負にならないかチェックする
        if LA.det(matJ) < 0:
            raise ValueError("要素の計算に失敗しました")

        return matJ

    # Bマトリクスを作成する
    def makeBmatrix(self):

        # dNi/da, dNi/dbを計算する
        dN1da = -1.0
        dN2da = 1.0
        dN3da = 0.0
        dN4da = 0.0
        dN1db = -1.0
        dN2db = 0.0
        dN3db = 1.0
        dN4db = 0.0
        dN1dc = -1.0
        dN2dc = 0.0
        dN3dc = 0.0
        dN4dc = 1.0

        # dNi/dx, dNi/dyを計算する
        matdNdab = np.matrix([[dN1da, dN2da, dN3da, dN4da],
                              [dN1db, dN2db, dN3db, dN4db],
                              [dN1dc, dN2dc, dN3dc, dN4dc]])

         # ヤコビ行列を計算する
        matJ = self.makeJmatrix()

        #dNdxy = matJinv * matdNdab
        dNdxy = LA.solve(matJ, matdNdab)
        
        # Bマトリクスを計算する
        matB = np.array([[dNdxy[0, 0], 0.0, 0.0, dNdxy[0, 1], 0.0, 0.0, dNdxy[0, 2], 0.0, 0.0, dNdxy[0, 3], 0.0, 0.0],
                         [0.0, dNdxy[1, 0], 0.0, 0.0, dNdxy[1, 1], 0.0, 0.0, dNdxy[1, 2], 0.0, 0.0, dNdxy[1, 3], 0.0],
                         [0.0, 0.0, dNdxy[2, 0], 0.0, 0.0, dNdxy[2, 1], 0.0, 0.0, dNdxy[2, 2], 0.0, 0.0, dNdxy[2, 3]],
                         [0.0, dNdxy[2, 0], dNdxy[1, 0], 0.0, dNdxy[2, 1], dNdxy[1, 1], 0.0, dNdxy[2, 2], dNdxy[1, 2], 0.0, dNdxy[2, 3], dNdxy[1, 3]],
                         [dNdxy[2, 0], 0.0, dNdxy[0, 0], dNdxy[2, 1], 0.0, dNdxy[0, 1], dNdxy[2, 2], 0.0, dNdxy[0, 2], dNdxy[2, 3], 0.0, dNdxy[0, 3]],
                         [dNdxy[1, 0], dNdxy[0, 0], 0.0, dNdxy[1, 1], dNdxy[0, 1], 0.0, dNdxy[1, 2], dNdxy[0, 2], 0.0, dNdxy[1, 3], dNdxy[0, 3], 0.0]])
        
        return matB

    # 等価節点力の荷重ベクトルを作成する
    def makeEqNodeForceVector(self):

        # ヤコビ行列を計算する
        matJ = self.makeJmatrix()

        vecEqNodeForce = np.zeros(self.nodeNum * self.nodeDof)

        # 物体力による等価節点力を計算する
        vecBodyForce = np.zeros(self.nodeNum * self.nodeDof)
        if not self.vecGravity is None:
            vecb = self.density * self.vecGravity   # 単位体積あたりの物体力のベクトル
            N1 = 1 - self.ai - self.bi - self.ci
            N2 = self.ai
            N3 = self.bi
            N4 = self.ci
            matN = np.matrix([[N1, 0.0, 0.0, N2, 0.0, 0.0, N3, 0.0, 0.0, N4, 0.0, 0.0],
                              [0.0, N1, 0.0, 0.0, N2, 0.0, 0.0, N3, 0.0, 0.0, N4, 0.0],
                              [0.0, 0.0, N1, 0.0, 0.0, N2, 0.0, 0.0, N3, 0.0, 0.0, N4]])
            vecBodyForce = self.w * np.array(matN.T @ vecb).flatten() * LA.det(matJ)

        # 表面力と物体力の等価節点力を計算する
        vecEqNodeForce = vecBodyForce
        
        return vecEqNodeForce
    
    def calculateStress(self, displacement_vector):
        """要素の応力を計算
        
        Args:
            displacement_vector: 要素の節点変位ベクトル (12x1)
        
        Returns:
            stress_vector: 応力ベクトル [σxx, σyy, σzz, τxy, τyz, τzx]
            von_mises_stress: von Mises応力
        """
        # D行列（材料構成行列）を作成
        D = self.makeDmatrix()
        
        # B行列（歪-変位関係行列）を作成
        B = self.makeBmatrix()
        
        # 歪を計算 ε = B × u
        strain_vector = B @ displacement_vector
        
        # 応力を計算 σ = D × ε  
        stress_vector = D @ strain_vector
        
        # von Mises応力を計算
        # σ_vm = sqrt(((σxx-σyy)²+(σyy-σzz)²+(σzz-σxx)²)/2 + 3(τxy²+τyz²+τzx²))
        sxx, syy, szz, txy, tyz, tzx = stress_vector
        
        von_mises_stress = np.sqrt(
            ((sxx - syy)**2 + (syy - szz)**2 + (szz - sxx)**2) / 2.0 +
            3.0 * (txy**2 + tyz**2 + tzx**2)
        )
        
        return stress_vector, von_mises_stress

