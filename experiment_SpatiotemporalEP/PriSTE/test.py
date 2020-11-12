import numpy as np

filename = "./groundtruth/56_times_30.csv"
T = np.loadtxt(filename,delimiter=",")

avg = []
mid = []
for i in range(len(T)):
    avg.append(np.mean(T[i]))
    mid.append(np.median(T[i]))



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

def setZb(map:np.ndarray):
    zb = []
    for i in range(len(map[:,0])):
        for j in range(len(map[0])):
            zb.append((i,j))
    return zb

def getMD(map:np.ndarray,zb:list):
    MD = []
    for k in range(map.size):
        md = np.ndarray(map.shape)
        for i in range(map.shape[0]):
            for j in range(map.shape[1]):
                md[i,j] = int(abs(zb[k][0]-i)+abs(zb[k][1]-j))
        MD.insert(k,md)
    return MD

def getTD(T:np.ndarray,map:np.ndarray):
    mid = []
    TD = np.ndarray((map.size,map.size))
    for i in range(len(T)):
        mid.append(np.median(T[i]))
    for i in range(TD.shape[0]):
         for j in range(TD.shape[1]):
             TD[i, j] = mid[i]/mid[j]
    return TD

def getOD(map:np.ndarray,zb:list):
    OD = []
    for k in range(map.size):
        od = np.ndarray(map.shape)
        for i in range(map.shape[0]):
            for j in range(map.shape[1]):
                od[i,j] = np.sqrt((zb[k][0]-i)**2+(zb[k][1]-j)**2)
        OD.insert(k,od)
    return OD

Map = Map()
map = Map.getMap()
zb = setZb(map)
MD = getMD(map,zb)
OD = getOD(map,zb)
# print(1/(OD[0]+1))
for k in range(len(OD)):
    OD[k] = 1/(OD[k]+1)
    # for i in range(OD[k].shape[0]):
    #     s = np.sum(OD[k])
    #     for j in range(OD[k].shape[1]):
    #         OD[k][i,j] /= s


TD = getTD(T,map)