import numpy as np

filename = "./groundtruth/56_times_30.csv"
T = np.loadtxt(filename,delimiter=",")

class Map():
    def __init__(self):
        self.map = self.setMap()

    def setMap(self):
        map = np.empty((7, 8), int)
        for i in range(7):
            for j in range(8):
                map[i, j] = i * 8 + j
        return map

    def getMap(self):
        return self.map

class S():
    def __init__(self,T:np.ndarray,map:np.ndarray,zb:list):
        self.MD = self.setMD(map,zb)
        self.TD = self.setTD(T,map)
        self.OD = self.setOD(map,zb)

    def setMD(self,map: np.ndarray, zb: list):
        MD = []
        for k in range(map.size):
            md = np.ndarray(map.shape)
            for i in range(map.shape[0]):
                for j in range(map.shape[1]):
                    md[i, j] = int(abs(zb[k][0] - i) + abs(zb[k][1] - j))
            MD.insert(k, md)
        return MD

    def setTD(self,T: np.ndarray, map: np.ndarray):
        mid = []
        TD = np.ndarray((map.size, map.size))
        for i in range(len(T)):
            mid.append(np.median(T[i]))
        for i in range(TD.shape[0]):
            for j in range(TD.shape[1]):
                TD[i, j] = mid[i] / mid[j]
        return TD

    def setOD(map: np.ndarray, zb: list):
        OD = []
        for k in range(map.size):
            od = np.ndarray(map.shape)
            for i in range(map.shape[0]):
                for j in range(map.shape[1]):
                    od[i, j] = int(np.sqrt((zb[k][0] - i) ** 2 + (zb[k][1] - j) ** 2))
            OD.insert(k, od)
        for i in range(len(OD)):
            OD[i] += 1
            OD[i] /= 10
        return OD

    def getMD(self):
        return self.MD

    def getTD(self):
        return self.TD

    def getOD(self):
        return self.OD

def setZb(map:np.ndarray):
    zb = []
    for i in range(len(map[:,0])):
        for j in range(len(map[0])):
            zb.append((i,j))
    return zb

def dSimilarity(S:S):
    od = S.getOD()
    td = S.getTD()
    

Map = Map()
map = Map.getMap()