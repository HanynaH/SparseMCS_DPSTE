import numpy as np
import pandas as pd
import  math

class P_code():
    def __init__(self):
        n = {0: [[0, 0], [1, 0]], 1: [[0, 1], [1, 1]]}
        # self.Map = pd.DataFrame()
        self.temp = pd.DataFrame(data=n)
        self.temp = self.temp.append(self.temp, ignore_index=True)
        self.temp.iloc[2] = self.temp.iloc[1]
        self.temp.iloc[3] = self.temp.iloc[0]
        self.temp[2] = self.temp[1]
        self.temp[3] = self.temp[0]

    def create_Map(self):
        Map = self.temp
        for i in range(4):
            for j in range(4):
                if i<2 and j<2:
                    Map[i][j] = [0,0]+Map[i][j]
                elif i<2 and 1<j<4:
                    Map[i][j] = [1,0]+Map[i][j]
                elif 1<i<4 and j<2:
                    Map[i][j] = [0,1]+Map[i][j]
                else:
                    Map[i][j] = [1,1]+Map[i][j]
        self.Map = Map
        return self.Map

    def create_truePlace(self,num:int):
        place = list()
        for k in range(num):
            i = np.random.randint(3)
            j = np.random.randint(3)
            place.append(self.Map[i][j])
        return place

    def create_randomPlace(self,num:int):
        randomPlace = list()
        for k in range(num):
            i = np.random.randint(3)
            j = np.random.randint(3)
            randomPlace.append(self.Map[i][j])
        return randomPlace

class Event():
    def __init__(self,Map:pd.DataFrame,place:list):
        self.place = place
        self.Map = Map

    def getPrecense(self):
        return self.place

    def getNonPrecense(self):
        length = int(math.sqrt(Map.size))
        NonPrecense = []
        for i in range(length):
            for j in range(length):
                if Map[i][j] not in self.place:
                    NonPrecense.append(Map[i][j])
        return NonPrecense

    def getNonEventP(self,time:int):
        size = self.Map.size
        num = size-len(self.place)
        self.NonEventP = (num/size)**time
        return self.NonEventP

    def getEventP(self,time:int):
        self.EventP = 1-self.getNonEventP(time)
        return self.EventP

def changebit(bit_array: list, p, q=None):
    q = 1 - p if q is None else q
    for i in range(len(bit_array)):
        bit = bit_array[i]
        g = np.random.randint(4)
        if bit[g] == 1:
            bit[g] = bit[g] if np.random.binomial(1,p)== bit[g] else (1-bit[g])
        else:
            bit[g] = bit[g] if np.random.binomial(1,q) == bit[g] else (1 - bit[g])
        bit_array[i] = bit
    return bit_array

def eps2p(epsilon, n):
    return np.e ** (epsilon/n) / (np.e ** (epsilon/n) + 1)

def P_observe(true_place:list,ob_place:list,p:float):
    q = 1-p ;  P = 1.0
    for i in range(len(true_place)):
        if true_place[i] == ob_place[i]:
            P *= p
        else:
            P = P*q/len(true_place[0])
    return P

# def check_SEP(p_ob:float,p_e:float,p_non:float):






time = 3
event_long = 2
P = P_code()
Map = P.create_Map()
true_place = P.create_truePlace(3)
epsilon = eps2p(2,len(true_place[0]))
r_place = P.create_randomPlace(2)
ob_place = changebit(true_place,epsilon)
Event = Event(Map,r_place)
p_non = Event.getNonEventP(event_long)
p_e = Event.getEventP(event_long)
p_ob = P_observe(true_place,ob_place,epsilon)

print("——————————地图——————————")
print(Map)

print("——————————地点——————————")
print(true_place)

print("——————————混淆后——————————")
print(ob_place)

print("——————————事件——————————")
print(r_place)

print("——————————发生事件概率——————————")
print(Event.getEventP(event_long))
print("——————————发生非事件概率——————————")
print(Event.getNonEventP(event_long))


