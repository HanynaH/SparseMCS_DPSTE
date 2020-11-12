import numpy as np
from itertools import combinations,permutations

time = 2
class Map():
    def __init__(self):
        self.map = self.setMap()

    def setMap(self):
        map = np.empty((4, 4), int)
        for i in range(4):
            for j in range(4):
                map[i, j] = i * 4 + j
        return map

    def getMap(self):
        return self.map

class Event():
    def __init__(self,emap:list,flag:str,index:list):
        self.map = emap
        if flag=="l":
            self.event = self.setlEvent(index)
        else:
            self.event = self.setfEvent(index)

    def setlEvent(self,index:list):
        event = []
        for i in range(len(index)):
            event.append(self.map[index[i]])
        return event

    def setfEvent(self,index:list):
        event = index
        return event

    def getEvent(self):
        return self.event

class O_loc():
    def __init__(self,time:int,map:np.ndarray):
        self.map = []
        temp = map.tolist()
        for i in range(len(temp)):
            self.map.extend(temp[i])
        self.cloc = self.com_loc(time)
        self.ploc = self.per_loc(time)

    def com_loc(self,time:int):
        comloc = list(combinations(self.map,time))
        return comloc

    def per_loc(self,time:int):
        perloc = list(permutations(self.map,time))
        return perloc

    def getcloc(self):
        return self.cloc

    def getploc(self):
        return self.ploc

def splitMap(map:np.ndarray,rlen=None,clen=None):
    if rlen is None and clen is None:
        return map
    if clen is None:
        smap = np.array_split(map,rlen,axis=0)
    elif rlen is None:
        smap = np.array_split(map,clen,axis=1)
    else:
        smap = []
        temp = np.array_split(map,rlen,axis=0)
        for i in range(len(temp)):
            smap.extend(np.array_split(temp[i],clen,axis=1))
    return smap

Map = Map()
O_loc = O_loc(2,Map.map)
lindex = [0,3]
findex = [0,15]
lEvent = Event(splitMap(Map.map,2,2),"l",lindex)
fEvent = Event(splitMap(Map.map),"f",findex)
oloc_c = O_loc.getcloc()
oloc_p = O_loc.getploc()



print("------------------地图------------------")
print(Map.map)
print("----------------fevent----------------")
print(fEvent.getEvent())
print("----------------levent----------------")
print(lEvent.getEvent())