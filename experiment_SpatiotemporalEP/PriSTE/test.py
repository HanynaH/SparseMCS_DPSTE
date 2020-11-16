import pulp as lp
import numpy as np

R=57
p = 1/R
epsilon = 4


U = np.loadtxt("./uncertainty_matrix/temp336cycles/rse_uncertainty_matrix.csv",delimiter=",")
(m,n) = U.shape

flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]

PB = lp.LpProblem(name="Obufuscation_Probility",sense=lp.LpMinimize)

P = lp.LpVariable.matrix("obfuscation_probility",(range(m),range(n)),lowBound=0)

x = flatten(P)

PB += lp.lpSum(lp.lpDot(p*U[:,j],[a[j] for a in P]) for j in range(n))


# PB += lp.lpSum(lp.lpDot(p,lp.lpSum(lp.lpDot(U[i,j],P[i][j]) for j in range(n))) for i in range(n))

# for i in range(m):
#     PB += lp.lpDot(p,lp.lpSum(lp.lpDot(U[i,j],P[i,j]) for j in range(n)))

for i in range(len(x)):
    for j in range(len(x)):
        PB.addConstraint(lp.lpDot(epsilon,x[j])>=x[i])


for j in range(n):
    PB+=(lp.lpSum(lp.lpDot(p,P[:][j]))==1/R)

for i in range(m):
    PB+=(lp.lpSum(P[i][j] for j in range(n))==1)

PB.solve()

res = np.ndarray((57,57))
for i in range(len(P)):
    for j in range(len(P[0])):
        res[i,j] = lp.value(P[i][j])

