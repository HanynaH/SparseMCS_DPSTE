import numpy as np
import random

def getepsilon(P,e_num:int,ob_num:int):
    map = list(range(57))
    # e2 = []
    ob = []
    p_e1 = 1
    p_none1 = 1
    none1 = []
    count = 0
    epsilon = 4
    e1 = random.sample(map,e_num)
    # e2.append(np.random.randint(57))

    for i in range(len(map)):
        if map[i] in e1:
            continue
        none1.append(map[i])

    ob = np.random.randint(0,57,ob_num).tolist()

    for i in range(len(ob)):
        sum = 0
        for j in range(len(e1)):
            sum += P[e1[j],ob[i]]
            count+=1
        p_e1*=sum

    for i in range(len(ob)):
        sum = 0
        for j in range(len(none1)):
            sum+=P[none1[j],ob[i]]
        p_none1*=sum

    return (p_e1 / p_none1)

if __name__ == '__main__':
    epsilon=5
    P = np.loadtxt("./linear_programing/res_epsilon_{}.csv".format(epsilon), delimiter=',')
    r_list = []
    res = np.ndarray((57,57))
    for i in range(1,58):
        for j in range(1,58):
            res[i-1,j-1] = getepsilon(P,i,j)

    (m,n) = res.shape
    for i in range(m):
        for j in range(n):
            if res[i,j]<=9 and res[i,j]>=epsilon and (j+1)/(i+1)<=1:
                r_list.append((i+1,j+1,res[i,j],(j+1)/(i+1)))



    print(r_list)
    np.savetxt("epsilon_test.csv",res,fmt='% .4f',delimiter=',')


