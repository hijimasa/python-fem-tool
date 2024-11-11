# 3次元節点格納用のクラス
class Node:

    # コンストラクタ
    # no : 節点番号
    # x  : x座標
    # y  : y座標
    # z  : z座標
    def __init__(self, no, x, y, z):
        self.no = no   # 節点番号
        self.x = x     # x座標
        self.y = y     # y座標
        self.z = z     # z座標

    # 節点の情報を表示する
    def printNode(self):
        print("Node No: %d, x: %f, y: %f, z: %f" % (self.no, self.x, self.y, self.z))

