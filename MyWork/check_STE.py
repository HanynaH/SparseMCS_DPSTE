import numpy as np

class Event():
    def __init__(self,col:int,row:int,P:np.ndarray):


    def createEvent(self,cnum:int,rnum:int,P:np.ndarray):
        (r_len,c_len) = P.shape

        while r_len%rnum or c_len%cnum:
            row = int(r_len / rnum)
            col = int(c_len / cnum)
            event = np.ndarray((rnum, cnum))
            for i in range(rnum):
                for j in range(cnum):
                    event[i,j] = P[i*row:(i+1)*row,j*col:(j+1)*col]
            if r_len%rnum:
                row_last = r_len%rnum
                for j in range(cnum):
                    event[rnum+1,j] = P[rnum:]
            if c_len%cnum:
                col_last = c_len%cnum








