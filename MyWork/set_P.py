import numpy as np
from docplex.mp.model import Model

def linear_programming(R:int,epsilon:int,upath:str):
    p = 1/R
    U = np.loadtxt(upath,delimiter=',')
    (m,n) = U.shape
    model = Model(name='obfuscation_res')

    sumtemp = [0]*R
    sum = 0

    P = model.continuous_var_matrix(range(m),range(n),lb=0,name='ob_P')
    for i in range(m):
        for j in range(n):
            model.add_constraint(P[i,j]>=0)

    for k in range(n):
        for i in range(m):
            for j in range(m):
                model.add_constraint(P[i,k]<=epsilon*P[j,k])

    for j in range(n):
        for i in range(m):
            sumtemp[j] += P[i,j]

    for i in range(len(sumtemp)):
        model.add_constraint(p*sumtemp[i]==1/R)

    for i in range(m):
        for j in range(n):
            sum += U[i,j]*P[i,j]

    model.minimize(p*sum)

    model.print_information()

    res = model.solve()

    a = res.get_all_values()

    res_nd = np.ndarray((m,n))
    for i in range(m):
        for j in range(n):
            res_nd[i,j] = a[i*57+j]

    print(res_nd)
    np.savetxt("./linear_programing/res_epsilon_{}.csv".format(epsilon),res_nd,fmt='% .6f',delimiter=',')
    return res_nd

if __name__ == '__main__':
    savepath_i = [1,2,3,4,5,6,7,8]
    R =57
    upath = "./uncertainty_matrix/temp336cycles/rse_uncertainty_matrix.csv"
    for i in savepath_i:
        linear_programming(R,i,upath)
