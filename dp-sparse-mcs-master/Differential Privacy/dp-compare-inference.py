from numpy import matrix
import numpy as np
import math 
from numpy.linalg import norm
import random
import re
from time import strftime
import sys, getopt
from scipy.linalg import toeplitz
from sklearn.preprocessing import normalize

NUM_OF_CELLS = 57
IS_PM25 = False

# Following matrices are read from output files from other programs
P = [] #obfuscation matrix P[i,j] is the probability from cell i to cell j (generated by linear programming from GLPK)
T = [] #ground truth sensing matrix: m*n (m cells and n cycles)  (Temperature dataset from EPFL SensorScope)
Coefficient = [] #linear regression: Coefficient[i,j] is the coefficient from cell i to cell j (generated by lm from R)
Intercept = [] #linear regression: Intercept[i,j] is the intercept from cell i to cell j (generated by lm from R)
MeanDiff = []
Uncertainty = [] #uncertainty matrix: Uncertainty[i,j] is the uncertainty from obfuscating cell i to cell j (for linear regression, it is RSE or (1-Rsquared))
SampleWeight = [] #sample weight vector for each region: get from uncertainty matrix, lowest average uncertainty -> 1, highest -> 0.5, others normalized to 0.5~1
MarkTrueData = [] #Mark data which is true (not obfuscated)

# ===================== Help Functions ===================
def read_sensing_matrix(ground_truth_file):
	"""
	Construct the sensing matrix T from the ground truth file
	"""
	global T
	T = matrix(np.loadtxt(ground_truth_file, delimiter = ","))
	print("=========T=========")
	print(T)

def read_linear_gression_result(coefficient_file, intercept_file):
	global Coefficient
	global Intercept
	Coefficient = matrix(np.loadtxt(coefficient_file, delimiter = ","))
	Intercept = matrix(np.loadtxt(intercept_file, delimiter = ","))

def read_uncertainty_matrix(uncertainty_file):
	global Uncertainty
	Uncertainty = matrix(np.loadtxt(uncertainty_file, delimiter = ","))

def create_sample_weight():
	global SampleWeight
	avgUncertainty = list(range(NUM_OF_CELLS))
	for i in range(NUM_OF_CELLS):
		avgUncertainty[i] = P.T[i,:]*Uncertainty[:,i]*1.0/P.T[i,:].sum()
	SampleWeight = list(range(NUM_OF_CELLS))
	maxU = max(avgUncertainty)
	minU = min(avgUncertainty)
	meanU = sum(avgUncertainty)*1.0/len(avgUncertainty)

	print("overall uncertainty:", meanU)

	print("maxU", maxU)
	print("minU", minU)
	for i in range(len(avgUncertainty)):
		SampleWeight[i] = 1 - 0.5 * (avgUncertainty[i]-minU)/(maxU-minU)
	print(SampleWeight)

def read_mean_diff_result(mean_diff_file):
	global MeanDiff
	MeanDiff = matrix(np.loadtxt(mean_diff_file, delimiter = ","))

### Deprecated Method: changing GLPK to CPLEX, see the method read_obfuscation_matrix_cplex
# def read_obfuscation_matrix(obfuscation_file):
# 	"""
# 	Read the obfuscation matrix from the GLPK output file 
# 	(the output file is already simplied to only variable output).
# 	"""
# 	global P
# 	P = matrix(np.zeros(shape=(NUM_OF_CELLS, NUM_OF_CELLS)))
# 	with open(obfuscation_file, "r") as inputFile:
# 		for line in inputFile:
# 			if line[0] == '#':  #skip the first few lines to describe the output
# 				continue
# 			# example line: 1 P[1,1] B 0.0166084 0
# 			words = line.split();
# 			i,j = getIndex(words[1]) # words[1]: "P[1,2]" 1=>i, 2=>j
# 			P[i-1,j-1] = float(words[3]) # words[3] is the probability, note that index in python from 0 start, thus minus 1
# 	print "=======P======="
# 	print P

###不建议使用的方法：将GLPK更改为CPLEX，请参见方法read_obfuscation_matrix_cplex
# def read_obfuscation_matrix（obfuscation_file）：
# “”“
# 从GLPK输出文件中读取混淆矩阵
# （输出文件已经被简化为仅变量输出）。
# “”“
# 全局P
# P =矩阵（np.zeros（shape =（NUM_OF_CELLS，NUM_OF_CELLS）））
# 以open（obfuscation_file，“ r”）作为输入文件：
# 输入文件中的行：
# if line [0] =='＃'：＃跳过前几行以描述输出
# 继续
# 示例行：1 P [1,1] B 0.0166084 0
# 个单词= line.split（）;
# i，j = getIndex（words [1]）＃words [1]：“ P [1,2]” 1 => i，2 => j
# P [i-1，j-1] = float（words [3]）＃words [3]是概率，请注意python中的索引从0开始，因此减去1
# 打印“ ======= P =======”
# 打印P

def read_obfuscation_matrix_cplex(obfuscation_file):
	"""
	Read the obfuscation matrix from CPLEX output
	"""
	global P
	P = matrix(np.loadtxt(obfuscation_file))
	print("=======P=======")
	print(P)

def naive_obfuscation_matrix(e_epsilon):
	"""
	Define a naive obfuscation matrix with a predefined epsilon
	(transfer to self's weight is e_epsilon; otherwise 1)
	"""
	global P
	P = matrix(np.zeros(shape=(NUM_OF_CELLS, NUM_OF_CELLS)))
	for i in range(NUM_OF_CELLS):
		for j in range(NUM_OF_CELLS):
			if (i==j):
				P[i,j]=e_epsilon*1.0/(e_epsilon+NUM_OF_CELLS-1)
			else:
				P[i,j]=1.0/(e_epsilon+NUM_OF_CELLS-1)
	print("=======P=======")
	print(P)
	print(P.sum(axis=1))

def dist_laplacian_obfuscation_matrix(e_epsilon, r):
	"""
	Define a distance-relevant laplacian obfuscation matrix with a predefined epsilon and distrance range 
	(ref [CCS'13 "Geo-Indistinguishability"])
	Laplacian Noise:
		P[i,j] ~ e^(-sigma*dist(i,j))
		where sigma = ln(e_epsilon)/r
	"""
	global P
	P = matrix(np.zeros(shape=(NUM_OF_CELLS, NUM_OF_CELLS)))
	for i in range(NUM_OF_CELLS):
		for j in range(NUM_OF_CELLS):
			P[i,j] = math.exp(-1.0 * math.log(e_epsilon)/r * abs(i-j))  #Laplacian distribution [CCS'13]

	# normalize
	P_rowsum = P.sum(axis=1)
	P = P/P_rowsum

	print("=======P=======")
	print(P)
	print(P.sum(axis=1))

def exponential_mechanism_matrix(e_epsilon):
	"""
	Define a exponential mechanism considering Uncertainty matrix
	"""
	max_epsilon = 1
	test_input_epsilon = e_epsilon
	while (max_epsilon < e_epsilon):
		local_P = matrix(np.zeros(shape=(NUM_OF_CELLS, NUM_OF_CELLS)))
		max_uncertainty = Uncertainty.max(1)
		for i in range(NUM_OF_CELLS):
			for j in range(NUM_OF_CELLS):
				local_P[i,j] = math.exp(math.log(test_input_epsilon)/2.0*(1-Uncertainty[i,j]/max_uncertainty[i,0]))
		
		local_P = normalize(local_P, axis=1, norm='l1')

		max_epsilon = 1
		for i in range(NUM_OF_CELLS):
			max_col = np.max(local_P[:,i])
			min_col = np.min(local_P[:,i])
			current_epsilon = max_col * 1.0 / min_col
			if current_epsilon > max_epsilon:
				max_epsilon = current_epsilon

		print("test epsilon {}, actual epsilon {}".format(test_input_epsilon, max_epsilon))

		if (max_epsilon <= e_epsilon):
			global P
			P = local_P

		test_input_epsilon += 0.5

	print("=======P=======")
	print(P)
	print(P.sum(axis=1))

def getIndex(matrixNotion):
	"""
	Get the index from a matrix notion such as "P[1,2]", return (1,2)
	"""
	index = re.findall(r'\d+', matrixNotion) #regular expression to extract numbers (digits)
	return int(index[0]), int(index[1])

def hasTruth(cell_i, cycle_j):
	"""
	check whether cell i and cycle j has ground truth value
	"""
	if T[cell_i, cycle_j] > -100:
		return True
	return False

def truth(cell_i, cycle_j):
	"""
	return the truth value for cell i and cycle j if the truth value exists
	"""
	assert hasTruth(cell_i, cycle_j), "cell {}, cycle {} does not contain truth".format(cell_i, cycle_j)
	return T[cell_i, cycle_j]

def numCycles():
	"""
	return the number of the total cycles
	"""
	m, n = T.shape
	return n

def numCells():
	"""
	return the number of the total cells
	"""
	m, n = T.shape
	return m

# ===================== Error Metrics ====================
def MAE(est_values, cycle_k):
	"""
	mean absolute error
	"""
	true_values = T[:, cycle_k]
	assert est_values.shape == true_values.shape, "estimated value and true value size not equal: {} vs {}".format(est_values.shape, true_values.shape)
	m, n = true_values.shape
	up = 0.0
	down = 0.0
	for i in range(m):
		for j in range(n):
			if true_values[i,j] > -100:
				up += abs(est_values[i,j] - true_values[i,j])
				down += 1
	if down == 0.0:
		return 0
	return up/down

def RMSE(est_values, cycle_k):
	"""
	root mean squared error
	"""
	true_values = T[:, cycle_k]
	assert est_values.shape == true_values.shape, "estimated value and true value size not equal"
	m, n = true_values.shape
	up = 0.0
	down = 0.0
	for i in range(m):
		for j in range(n):
			if true_values[i,j] > -100:
				up += (est_values[i,j] - true_values[i,j])**2
				down += 1
	if down == 0.0:
		return 0
	return math.sqrt(up/down)

def AQI_level_precision(est_values, cycle_k):
	true_values = T[:, cycle_k]
	assert est_values.shape == true_values.shape, "estimated value and true value size not equal"
	m, n = true_values.shape
	up = 0.0
	down = 0.0
	for i in range(m):
		for j in range(n):
			if true_values[i,j] > -100:
				recovered_level = mapAQItoLevel(est_values[i,j])
				true_level = mapAQItoLevel(true_values[i,j])
				if recovered_level == true_level:
					up += 1.0
				down += 1.0
	if down == 0.0:
		return 1
	return up/down

def mapAQItoLevel(aqi_value):
	if aqi_value <= 50:
		return 1
	elif aqi_value <= 100:
		return 2
	elif aqi_value <= 150:
		return 3
	# elif aqi_value <= 200:
		# return 4
	# elif aqi_value <= 300:
		# return 5
	else:
		return 4

# ===================== Matrix Completion/Recovery =====================

MINCOUNT = 5

def calculate_initial_matrix (B, C, r):
	m, n = B.shape
	temp_matrix = np.zeros((m,n))

	average_for_each_cycle = []

	for i in range(n):
		sum_cycle = 0
		count_cycle = 0
		for j in range(m):
			if B[j,i] == 1:
				count_cycle += 1
				sum_cycle += C[j,i]
		if count_cycle != 0:
			avg = sum_cycle*1.0/count_cycle
		else:
			avg = 0
		average_for_each_cycle.append(avg)

	for i in range(m):
		for j in range(n):
			if B[i,j] == 0:
				temp_matrix[i,j] = average_for_each_cycle[j]
			else:
				temp_matrix[i,j] = C[i,j]

	#SVD
	U, s, V = np.linalg.svd(temp_matrix)

	s_matrix = np.zeros((m,r))
	s_matrix2 = np.zeros((r,n))
	U = matrix(U)
	V = matrix(V)


	#square root of s
	for i in range(r):
		s_matrix[i,i] = s[i]**0.5
		s_matrix2[i,i] = s[i]**0.5

	return U*s_matrix, (s_matrix2*V).T

def cs_matrix_recovery_sgd_weighted(C):
	return cs_matrix_recovery_sgd(C, is_weighted=True)

def cs_matrix_recovery_sgd(C, r=4, lamda=0.01, iteration_count = 10, learning_rate=0.01, is_weighted=False):
	"""
	using compressive sensing to reconstruct the matrix by stochastic gradient descent method.
	==========Parameters========= 
 		m locations, n sensing cycles
 		C: collected sensing matrix: C m*n
 		r: rank
 		lamda: a parameter to adjust the trade-off between low-rank and fitness in objective function
 		iteration_count: the maximum iteration count if the algorithm does not converge
	==========Return=============
 		full sensing matrix: F m*n
	"""	
	m, n = C.shape
	# construct binary matrix according to collected matrix
	B = matrix(np.zeros(shape=C.shape))
	W = matrix(np.zeros(shape=C.shape))
	for i in range(m):
		for j in range(n):
			if (C[i,j]<-99):
				B[i,j]=0
				if is_weighted:
					W[i,j]=0
			else:
				B[i,j]=1
				if is_weighted:
					W[i,j]=SampleWeight[i]
					if MarkTrueData[i,j]==1:
						W[i,j]=2 # true data gives 2 times weight than the lowest uncertain data

	L, R = calculate_initial_matrix(B, C, r)
	if is_weighted:
		sample_weights = W.getA1()/W.sum()
	else:
		sample_weights = B.getA1()/B.sum()
	idx = range(len(sample_weights))

	for count in range(iteration_count):
		# randomly select one cell in B whose value = 1
		for i in range(int(B.sum())):
			selected_idx = np.random.choice(idx, p=sample_weights)
			x = int(selected_idx/n)
			y = int(selected_idx - n*x)
			err = C[x,y] - L[x,:]*R.T[:,y]
			L[x,:] = L[x,:] + learning_rate * (err*R[y,:] - lamda*L[x,:])
			R[y,:] = R[y,:] + learning_rate * (err*L[x,:] - lamda*R[y,:])

		F = L * R.T
		if count == 0:
			bestF = F
			bestObj = cs_obj(B, C, L, R, lamda)
		else:
			newObj = cs_obj(B, C, L, R, lamda)
			if newObj < bestObj:
				bestF = F
				oldObj = bestObj
				bestObj = newObj
				if (oldObj - bestObj)*1.0/bestObj < 0.001 and count>=3:
					break
	print("count", count)

	return bestF

def cs_matrix_recovery_als(C, r=4, lamda=0.01, iteration_count = 500):
	"""
	using compressive sensing to reconstruct the matrix using alternative least squares.
	==========Parameters========= 
 		m locations, n sensing cycles
 		C: collected sensing matrix: C m*n
 		r: rank
 		lamda: a parameter to adjust the trade-off between low-rank and fitness in objective function
 		iteration_count: the maximum iteration count if the algorithm does not converge
	==========Return=============
 		full sensing matrix: F m*n
	"""
	m, n = C.shape
	# construct binary matrix according to collected matrix
	B = matrix(np.zeros(shape=C.shape))
	for i in range(m):
		for j in range(n):
			if (C[i,j]<-99):
				B[i,j]=0
			else:
				B[i,j]=1

	L, R = calculate_initial_matrix(B, C, r)

	for count in range(iteration_count):

		# calculate R according to L
		for i in range(n):
			# solve Px=Q, calculate P and Q
			# get P
			Bi = B[:,i] # ith col vector of matrix B: m*1
			DBi = matrix(np.diagflat(Bi)) # convert vector to diag matrix: m*m
			a1 = DBi * L # result matrix: m*r ([m,m]*[m,r])

			Ir = matrix(np.diagflat([1]*r)) # Ir
			a2 = math.sqrt(lamda) * Ir # result matrix r*r
			P = np.concatenate((a1, a2)) # a1 up and a2 down => result matrix: (m+r)*r

			#get Q
			Ci = C[:,i] # ith col vector of matrix C: m*1
			Zr = np.mat([0]*r).T # zero r col vector
			Q = np.concatenate((Ci, Zr)) # result matrix: (m+r)*1
			# Px = Q, least square problems solution
			x = np.linalg.lstsq(P, Q)[0] # r*1
			if i == 0:

				R = x.T
			else:
				R = np.concatenate((R,x.T))

		# calculate L according to R
		for i in range(m):
			#get P
			Bi_t = B.T[:,i] # ith col vector of matrix B_t: n*1
			DBi_t = matrix(np.diagflat(Bi_t)) # diag matrix: n*n
			a1 = DBi_t * R # result matrix: n*r

			Ir = matrix(np.diagflat([1]*r)) # Ir
			a2 = math.sqrt(lamda) * Ir # result matrix r*r

			P = np.concatenate((a1, a2)) # result matrix (n+r)*r

			#get Q
			Ci_t = C.T[:,i] # ith col vector of C_t: n*1
			Zr = np.mat([0]*r).T # zero r col vector
			Q = np.concatenate((Ci_t, Zr)) # result matrix: (n+r) * 1

			x = np.linalg.lstsq(P, Q)[0] # r*1
			if i == 0:
				L = x.T
			else:
				L = np.concatenate((L,x.T))
		# i from 1 to m, then L is obtained
		F = L * R.T # F=L*R.T

		if count == 0:
			bestF = F
			bestObj = cs_obj(B, C, L, R, lamda)
		else:
			newObj = cs_obj(B, C, L, R, lamda)
			if newObj < bestObj:
				bestF = F
				oldObj = bestObj
				bestObj = newObj
				if (oldObj - bestObj)*1.0/bestObj < 0.001 and count>=20:
					break
			
	# print "cs temp best obj round", count, ":", bestObj
	# print bestF
	return bestF

def cs_obj(B, C, L, R, lamda):
	"""
	objective function for compressive sensing.
	"""
	m, n = B.shape

	F = L * R.T
	obj = norm(np.multiply(B, F)-C)**2
	obj += lamda*(norm(L)**2+norm(R.T)**2)
	return obj


def timeMatrix(n):
	col = [0] * n
	col[0] = 1
	raw = [0] * n
	raw[0] = 1
	raw[1] = -1
	return matrix(toeplitz(col, raw))

def stcs_matrix_recovery(C, r=4, lamda=0.5, beta=0.05, iteration_count = 500):
	"""
	Add spatial and temporal correlations into the compressive sensing.
	"""
	m, n = C.shape

	#Time Correlation Matrix
	TM = timeMatrix(n) #n*n

	# construct binary matrix according to collected matrix
	B = matrix(np.zeros(shape=C.shape))
	for i in range(m):
		for j in range(n):
			if (C[i,j]<-99):
				B[i,j]=0
			else:
				B[i,j]=1
	L = matrix(10 * np.random.rand(m, r)) # m*r

	for count in range(iteration_count):
		# calculate R according to L
		for i in range(n):
			# solve Px=Q, calculate P and Q
			# get P
			Bi = B[:,i] # ith col vector of matrix B: m*1
			DBi = matrix(np.diagflat(Bi)) # convert vector to diag matrix: m*m
			a1 = DBi * L # result matrix: m*r ([m,m]*[m,r])

			Ir = matrix(np.diagflat([1]*r)) # Ir
			a2 = math.sqrt(lamda) * Ir # result matrix r*r
			P = np.concatenate((a1, a2)) # a1 up and a2 down => result matrix: (m+r)*r

			#get Q
			Ci = C[:,i] # ith col vector of matrix C: m*1
			Zr = np.mat([0]*r).T # zero r col vector
			Q = np.concatenate((Ci, Zr)) # result matrix: (m+r)*1
			# Px = Q, least square problems solution
			x = np.linalg.lstsq(P, Q)[0] # r*1
			if i == 0:
				R = x.T
			else:
				R = np.concatenate((R,x.T))

		# calculate L according to R
		for i in range(m):
			#get P
			Bi_t = B.T[:,i] # ith col vector of matrix B_t: n*1
			DBi_t = matrix(np.diagflat(Bi_t)) # diag matrix: n*n
			a1 = DBi_t * R # result matrix: n*r

			Ir = matrix(np.diagflat([1]*r)) # Ir
			a2 = math.sqrt(lamda) * Ir # result matrix r*r

			P = np.concatenate((a1, a2)) # result matrix (n+r)*r

			#consier time matrix correlation
			a3 = beta * TM * R #n*r
			P = np.concatenate((P,a3))

			#get Q
			Ci_t = C.T[:,i] # ith col vector of C_t: n*1
			Zr = np.mat([0]*r).T # zero r col vector
			Q = np.concatenate((Ci_t, Zr)) # result matrix: (n+r) * 1
			Zn = np.mat([0]*n).T # zero n col vector (corresponding to TM)
			Q = np.concatenate((Q, Zn)) # (n+r+n)*1


			x = np.linalg.lstsq(P, Q)[0] # r*1
			if i == 0:
				L = x.T
			else:
				L = np.concatenate((L,x.T))
		# i from 1 to m, then L is obtained
		F = L * R.T # F=L*R.T

		if count == 0:
			bestF = F
			bestObj = stcs_obj(B, C, L, R, lamda, beta)
		else:
			newObj = stcs_obj(B, C, L, R, lamda, beta)
			if newObj < bestObj:
				bestF = F
				oldObj = bestObj
				bestObj = newObj
				if (oldObj - bestObj)*1.0/bestObj < 0.001 and count>=MINCOUNT:
					break
		
	return bestF

def stcs_obj(B, C, L, R, lamda, beta):
	m, n = B.shape
	#Time Correlation Matrix
	TM = timeMatrix(n) #n*n

	F = L * R.T
	obj = norm(np.multiply(B, F)-C)**2
	obj += lamda*(norm(L)**2+norm(R.T)**2)
	obj += beta**2*(norm(F*TM.T)**2)
	# obj += beta**2*(norm(SM*F)**2)
	return obj

# ref from sigcomm'09, add local data interpolation method (e.g. KNN) after CS recovery
def local_knn_adjust (F_cs, C, k=3, km=5, onlyAjustLastCycle=True):
	m,n = C.shape
	B = matrix(np.zeros(shape=C.shape))
	for i in range(m):
		for j in range(n):
			if (C[i,j]<-99):
				B[i,j]=0
			else:
				B[i,j]=1

	if onlyAjustLastCycle:
		cycles = [n-1,]
	else:
		cycles = range(n)
	for i in range(m):
		for j in cycles:
			if B[i,j] == 0:
				current_sum = 0.0
				current_weight_sum = 0.0
				for s in range(k):
					left = j-1-s
					right = j+1+s
					if left >=0 and B[i, left] == 1:
						w = 1.0/(s+1)**2
						current_weight_sum += w
						current_sum += w*C[i, left]
					if right <n and B[i, right] == 1:
						w = 1.0/(s+1)**2
						current_weight_sum += w
						current_sum += w*C[i, right]
				if current_weight_sum > 0:
					F_cs[i,j] = current_sum/current_weight_sum #adjust to local interpolation value
	return F_cs

#==============Random Select and Obfuscation========================
def int_weighted_random(pairs):
	"""
	random int-weighted selection.
	========Parameters=========
	pairs: a list of (obj, weight), weight must be integer
	========Return=========
	a random selected obj according to its weight
	"""
	mylist = []
	for pair in pairs:
		assert isinstance(pair[1], int), "weight for object {} is not integer: {}".format(pair[0],pair[1])
		mylist += [pair[0]] * int(pair[1])
	return random.choice(mylist)

def obfuscation(src):
	"""
	obfuscate cell src to another cell according to the obfuscation matrix P
	========Parameters==========
	src: the original cell
	========Return============
	an obfuscated cell
	"""
	pairs = []
	multiply = 10000 #weight might be float, use this change to integer
	for i in range(NUM_OF_CELLS):
		pairs.append((i, int(P[src,i]*multiply)))
	return int_weighted_random(pairs)


def linear_regression_obfuscation(src, dest, src_truth):
	"""
	use linear regression to get the obfuscated value of the obfuscated location.
	=========Parameters===========
	src: the original source cell
	dest: the obfuscated destination cell
	src_truth: the ground truth sensed value for the src cell
	=========Return=========
	the obfuscated "truth" for the obfuscated location:
	"""
	return src_truth * Coefficient[dest, src] + Intercept[dest, src]


def mean_adjust_obfuscation(src, dest, src_truth):
	"""
	use global mean difference to get the obfuscated value 
	=========Parameters===========
	src: the original source cell
	dest: the obfuscated destination cell
	src_truth: the ground truth sensed value for the src cell
	=========Return=========
	the obfuscated "truth" for the obfuscated location:
	"""
	return src_truth + MeanDiff[dest, src]

def no_adjust(src, dest, src_truth):
	return src_truth

def random_cell(cycle_k):
	"""
	random select a cell from all the cells (equal weight) for cycle k
	"""
	pairs = []
	for i in range(numCells()):
		pairs.append((i,1))
	while (True):
		rnd = int_weighted_random(pairs)
		if hasTruth(rnd, cycle_k):
			return rnd, truth(rnd, cycle_k)

#=============DP compressive sensing in a whole MCS task============
def fixed_K_obfuscation(K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod, adjustmentModel, t_value=0):
	"""
	The whole process for a crowdsensing task considering DP-privacy and CS-reconstruction
	=========Parameters==========
	K: the sensed data received for each cycle
	start_cycle: mark the cycle where the CS-reconstruction begins
	outFile: the file path storing the result for the whole crowdsensing process
	outCollectedMatrixFile: the file path storing the result of collected data matrix
	recoverMethod: full sensing matrix inference algorithm
	adjustmentModel: core data adjustment model
	t_value: number of ground truth data
	"""
	create_sample_weight()
	with open(outFile, "w") as outputfile:
		if IS_PM25:
			outputfile.write("cycle,count,mae,accuracy\n")
		else:
			outputfile.write("cycle,count,mae,rmse\n")
	n = numCycles()
	m = numCells()
	C = T[:, 0:start_cycle] #collected sensing matrix
	Zm = matrix([-100]*m).T
	global MarkTrueData
	MarkTrueData = matrix(np.zeros(shape=(m,n)))
	print('process (cycles): ',)
	for cycle_i in range(start_cycle, n):
		print(cycle_i,)
		C = np.concatenate((C,Zm), axis=1) # set new cycle's collected vector to all non-valid values (-100)
		data_num_per_cell = {}
		for each_cell in range(numCells()):
			data_num_per_cell[each_cell] = 0.0
		for j in range(K):
			src_cell, src_truth = random_cell(cycle_i) # random select a cell in cycle i to sense the value
			while (True):
				obfuscated_cell = obfuscation(src_cell)
				# only if the obfuscated cell has not received data in this cycle (i) and the ground truth has its value,
				# then the obfuscation cell will be accepted
				if hasTruth(obfuscated_cell, cycle_i):
				# if C[obfuscated_cell, cycle_i] == -100 and hasTruth(obfuscated_cell, cycle_i): 
					break
			# data adjustment
			params = (src_cell, obfuscated_cell, src_truth)
			obfuscated_truth = adjustmentModel(*params)
			C[obfuscated_cell, cycle_i] = (C[obfuscated_cell, cycle_i]*data_num_per_cell[obfuscated_cell]+obfuscated_truth)/(data_num_per_cell[obfuscated_cell]+1.0)
			data_num_per_cell[obfuscated_cell] += 1.0

		if t_value > 0:
			for j in range(t_value):
				src_cell, src_truth = random_cell(cycle_i)
				C[src_cell, cycle_i] = src_truth
				MarkTrueData[src_cell, cycle_i] = 1  # mark true data for giving higher weights when doing recovery

		# after K sensed values, reconstruct the matrix and measure the errors
		# calibrate sensing cycles to last 100 cycles for recovery
		m_C, n_C = C.shape
		cal_C = C
		# if n_C > 100:
		# 	cal_C = C[:, n_C-100:]

		params = (cal_C,)
		est_F = recoverMethod(*params)
		est_F_lc = est_F[:,-1]
		mae = MAE(est_F_lc, cycle_i)
		rmse = RMSE(est_F_lc, cycle_i)
		outputString = "{},{},{},{}\n".format(cycle_i, K, mae, rmse)
		# print outputString
		with open(outFile, "a") as outputfile:
			outputfile.write(outputString)

	# np.savetxt(outCollectedMatrixFile, C, fmt='%.3f') #saving the collected sensing matrix

def fixed_K_naive_obfuscation(e_epsilon, K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod, adjustmentModel):
	"""
	The whole process for a crowdsensing task considering naive DP-privacy (baseline obfuscation mechanism) 
	and CS-reconstruction
	=========Parameters==========
	e_epsilon: predefined DP-privacy
	K: the sensed data received for each cycle
	start_cycle: mark the cycle where the CS-reconstruction begins
	outFile: the file path storing the result for the whole crowdsensing process
	outCollectedMatrixFile: the file path storing the result of collected data matrix
	"""
	naive_obfuscation_matrix(e_epsilon)
	fixed_K_obfuscation(K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod, adjustmentModel)

def fixed_K_laplacian_obfuscation(e_epsilon, K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod, adjustmentModel):
	"""
	The whole process for a crowdsensing task considering laplacian DP-privacy (laplacian obfuscation mechanism [CCS'13]) 
	and CS-reconstruction
	=========Parameters==========
	e_epsilon: predefined DP-privacy
	K: the sensed data received for each cycle
	start_cycle: mark the cycle where the CS-reconstruction begins
	outFile: the file path storing the result for the whole crowdsensing process
	outCollectedMatrixFile: the file path storing the result of collected data matrix
	"""
	dist_laplacian_obfuscation_matrix(e_epsilon, NUM_OF_CELLS-1)
	fixed_K_obfuscation(K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod, adjustmentModel)

def fixed_K_exponential_obfuscation(e_epsilon, K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod, adjustmentModel):
	"""
	The whole process for a crowdsensing task considering exponential DP-privacy 
	and CS-reconstruction
	=========Parameters==========
	e_epsilon: predefined DP-privacy
	K: the sensed data received for each cycle
	start_cycle: mark the cycle where the CS-reconstruction begins
	outFile: the file path storing the result for the whole crowdsensing process
	outCollectedMatrixFile: the file path storing the result of collected data matrix
	"""
	exponential_mechanism_matrix(e_epsilon)
	fixed_K_obfuscation(K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod, adjustmentModel)

def fixed_K_no_obfuscation(K, start_cycle, outFile, outCollectedMatrixFile, recoverMethod):
	"""
	The whole process for a crowdsensing task considering CS-reconstruction but no obfuscation
	=========Parameters==========
	K: the sensed data received for each cycle
	start_cycle: mark the cycle where the CS-reconstruction begins
	outFile: the file path storing the result for the whole crowdsensing process
	outCollectedMatrixFile: the file path storing the result of collected data matrix
	"""
	with open(outFile, "w") as outputfile:
		if IS_PM25:
			outputfile.write("cycle,count,mae,accuracy\n")
		else:
			outputfile.write("cycle,count,mae,rmse\n")
	n = numCycles()
	m = numCells()
	C = T[:, 0:start_cycle] #collected sensing matrix
	Zm = matrix([-100]*m).T
	print('process (cycles): ',)
	for cycle_i in range(start_cycle, n):
		print(cycle_i,)
		C = np.concatenate((C,Zm), axis=1) # set new cycle's collected vector to all non-valid values (-100)
		for j in range(K):
			src_cell, src_truth = random_cell(cycle_i) # random select a cell in cycle i to sense the value
			C[src_cell, cycle_i] = src_truth # no obfuscation

		# after K sensed values, reconstruct the matrix and measure the errors
		# calibrate sensing cycles to last 100 cycles for recovery
		m_C, n_C = C.shape
		cal_C = C
		if n_C > 100:
			cal_C = C[:, n_C-100:]

		params = (cal_C,)
		est_F = recoverMethod(*params)
		est_F_lc = est_F[:,-1]
		mae = MAE(est_F_lc, cycle_i)
		rmse = RMSE(est_F_lc, cycle_i)
		if IS_PM25:
			rmse = AQI_level_precision(est_F_lc, cycle_i)
		outputString = "{},{},{},{}\n".format(cycle_i, K, mae, rmse)
		# print outputString
		with open(outFile, "a") as outputfile:
			outputfile.write(outputString)

	# np.savetxt(outCollectedMatrixFile, C, fmt='%.3f')

def fixed_K_average(K, start_cycle, outFile, outCollectedMatrixFile):
	"""
	The whole process for a crowdsensing task considering average and no obfuscation
	=========Parameters==========
	K: the sensed data received for each cycle
	start_cycle: mark the cycle where the CS-reconstruction begins
	outFile: the file path storing the result for the whole crowdsensing process
	outCollectedMatrixFile: the file path storing the result of collected data matrix
	"""
	with open(outFile, "w") as outputfile:
		if IS_PM25:
			outputfile.write("cycle,count,mae,accuracy\n")
		else:
			outputfile.write("cycle,count,mae,rmse\n")
	n = numCycles()
	m = numCells()
	C = T[:, 0:start_cycle] #collected sensing matrix
	Zm = matrix([-100]*m).T
	print('process (cycles): ',)
	for cycle_i in range(start_cycle, n):
		print(cycle_i,)
		C = np.concatenate((C,Zm), axis=1) # set new cycle's collected vector to all non-valid values (-100)
		sensed_data = []
		for j in range(K):
			src_cell, src_truth = random_cell(cycle_i) # random select a cell in cycle i to sense the value
			sensed_data.append(src_truth) # no obfuscation

		# after K sensed values, reconstruct the matrix and measure the errors
		est_F_lc = matrix([np.mean(sensed_data)]*m).T
		mae = MAE(est_F_lc, cycle_i)
		if IS_PM25:
			rmse = AQI_level_precision(est_F_lc, cycle_i)
		else:
			rmse = RMSE(est_F_lc, cycle_i)
		outputString = "{},{},{},{}\n".format(cycle_i, K, mae, rmse)
		# print outputString
		with open(outFile, "a") as outputfile:
			outputfile.write(outputString)

	# np.savetxt(outCollectedMatrixFile, C, fmt='%.3f')

#============== passing CMD parameters =============
def main(argv):
	#defaut values
	e_epsilon = 4
	delta = 1
	K = 15
	obfuscation_style = "optimal"
	loss_function = "rse"
	dataset = "temp336cycles" #temp900cycles
	recoverMethodStr = "cs_sgd"
	adjustmentModelStr = "lr"
	repeat = 5
	t_value = 0

	try:
		opts, args = getopt.getopt(argv,"hk:e:d:s:l:t:i:a:r:g:")
	except getopt.GetoptError:
		print('dp.py -h for help')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('usage: dp.py -k <sensed cell/cycle> -s <obfuscation style> -e <e^epsilon> -d <delta> -l <loss function> -t <dataset>')
			print('example: dp.py -s "optimal" -k 10 -e 4 -d 4 -l "rsquared" -t "temp336cycles"')
			print('parameters:')
			print('  -s: (default: "optimal") obfuscation style "optimal", "fastoptimal", "exponential", "naive", "laplacian", "average" and "no"')
			print('  -k: (default: 15) sensed cell number per cycle')
			print('  -e: (default: 4) threshold for differential privacy (valid for -s "optimal", "fastoptimal", "exponential", "naive" or "laplacian")')
			print('  -d: (default: 1) threshold for skewness constraint after obfuscation (valid for -s "optimal", "fastoptimal")')
			print('  -l: (default: "rse") loss function "rsquared" or "rse" (only valid for -s "optimal", "fastoptimal", "exponential")')
			print('  -t: (default: "temp336cycles") dataset "temp336cycles", "temp900cycles", "humidity", "traffic100", "traffic500", or "pm25"')
			print('  -i: (default: "cs_sgd") inference algorithms "stcs" or "cs_als" or "cs_sgd" (valid for -s "optimal", "fastoptimal", "naive", "laplacian", or "no")')
			print('  -a: (default: "lr") core data adjustment model "lr" (linear regression), "mean" (difference between average) or "no" (no adjust)')
			print('  -r: (default: 5) repeating times')
			print('  -g: (default: 0) ground truth data, only valid for "optimal"')
			sys.exit()
		elif opt in ("-k",):
			K = int(arg)
		elif opt in ("-e"):
			e_epsilon = int(arg)
		elif opt in ("-d"):
			delta = arg
		elif opt in ("-s"):
			obfuscation_style = arg
		elif opt in ("-l"):
			loss_function = arg
		elif opt in ("-t"):
			dataset = arg
		elif opt in "-i":
			recoverMethodStr = arg
		elif opt in "-a":
			adjustmentModelStr = arg
		elif opt in "-r":
			repeat = int(arg)
		elif opt in "-g":
			t_value = int(arg)

	if recoverMethodStr == "stcs":
		recoverMethod = stcs_matrix_recovery
	elif recoverMethodStr == "cs_als":
		recoverMethod = cs_matrix_recovery_als
	elif recoverMethodStr == "cs_sgd":
		recoverMethod = cs_matrix_recovery_sgd
	elif recoverMethodStr == "cs_sgdw":
		recoverMethod = cs_matrix_recovery_sgd_weighted
	else: #default stcs
		recoverMethod = cs_matrix_recovery_sgd
	

	if adjustmentModelStr == "lr":
		adjustmentModel = linear_regression_obfuscation
	elif adjustmentModelStr == "mean":
		adjustmentModel = mean_adjust_obfuscation
	elif adjustmentModelStr == "no":
		adjustmentModel = no_adjust
	else:
		adjustmentModel = linear_regression_obfuscation

	print('dataset is: ', dataset)
	print('K is: ', K)
	print('obfuscation style is: ', obfuscation_style)
	if not (obfuscation_style == "average"):
		print('inference algorithm is: ', recoverMethodStr)
	if obfuscation_style == "optimal" or obfuscation_style == "fastoptimal":
		print('fitness function is: ', loss_function)
		print('e_epsilon is: ', e_epsilon)
		print('delta is: ', delta)
		print('adjustment model is: ', adjustmentModelStr)
	elif obfuscation_style == "naive" or obfuscation_style == "laplacian" or obfuscation_style == "exponential":
		print('e_epsilon is: ', e_epsilon)
		print('adjustment model is: ', adjustmentModelStr)
	
	lm_coefficient_file = "./linear_regression_results/{}/coefficient_lm_matrix.csv".format(dataset)
	lm_intercept_file = "./linear_regression_results/{}/intercept_lm_matrix.csv".format(dataset)
	mean_diff_file = "./linear_regression_results/{}/mean_diff.csv".format(dataset)

	start_cycle = 5 # start recovery from this cycle

	global NUM_OF_CELLS
	global IS_PM25
	if dataset == "temp336cycles":
		NUM_OF_CELLS = 57
		ground_truth_file = "./ground_truth/temp_57loc_30min_070101_070107.csv"
		read_mean_diff_result(mean_diff_file)
	elif dataset == "temp900cycles":
		NUM_OF_CELLS = 57
		ground_truth_file = "./ground_truth/temp_57loc_0.5hour_900cycles.csv"
	elif dataset == "humidity":
		NUM_OF_CELLS = 57
		ground_truth_file = "./ground_truth/humidity_57loc_30min_070101_070107.csv"
	elif dataset == "pm25":
		IS_PM25 = True
		NUM_OF_CELLS = 36
		ground_truth_file = "./ground_truth/PM25_131109_131120.csv"
	elif dataset == "traffic100":
		NUM_OF_CELLS = 100
		ground_truth_file = "./ground_truth/traffic_time_matrix_1hour_100.csv"
		start_cycle = 5
	elif dataset == "traffic500":
		NUM_OF_CELLS = 500
		ground_truth_file = "./ground_truth/traffic_time_matrix_1hour_500.csv"
		start_cycle = 5

	read_linear_gression_result(lm_coefficient_file, lm_intercept_file)
	read_sensing_matrix(ground_truth_file)

	uncertainty_file = "./uncertainty_matrix/{}/{}_uncertainty_matrix.csv".format(dataset, loss_function)
	read_uncertainty_matrix(uncertainty_file)
	
	for count in range(repeat):

		print("\n=============Run {}==============".format(count + 1))
		
		current_time = strftime("%Y-%m-%d-%H-%M-%S") #current time

		if obfuscation_style == "optimal": #optimal linear programming obfuscation matrix
			obfuscation_file = "./obfuscation_output_GLPK/{}/{}/optimal_epsilon{}_delta{}.out".format(dataset, loss_function, e_epsilon, delta)
			read_obfuscation_matrix_cplex(obfuscation_file)
			outputfile = "./output/{}/optimal/{}/optimal_obfuscation_K{}_s{}_e{}_d{}_g{}_{}_{}_{}.out".format(dataset, loss_function, K, start_cycle, e_epsilon, delta, t_value, recoverMethodStr, adjustmentModelStr, current_time)
			outputCollectedMatrixFile = "./output/{}/optimal/{}/optimal_obfuscation_collected_matrix_K{}_s{}_e{}_d{}_g{}_{}_{}_{}.out".format(dataset, loss_function, K, start_cycle, e_epsilon, delta, t_value, recoverMethodStr, adjustmentModelStr, current_time)
			# running the whole crowdsensing process
			fixed_K_obfuscation(K, start_cycle, outputfile, outputCollectedMatrixFile, recoverMethod, adjustmentModel, t_value)
		elif obfuscation_style == "fastoptimal":
			obfucation_file = "./obfuscation_output_GLPK/{}/{}/fast_approximation_epsilon{}_delta{}.out".format(dataset, loss_function, e_epsilon, delta)
			read_obfuscation_matrix_cplex(obfucation_file)
			outputfile = "./output/{}/fastoptimal/{}/fastoptimal_obfuscation_K{}_s{}_e{}_d{}_{}_{}_{}.out".format(dataset, loss_function, K, start_cycle, e_epsilon, delta, recoverMethodStr, adjustmentModelStr, current_time)
			outputCollectedMatrixFile = "./output/{}/fastoptimal/{}/matrix/fastoptimal_obfuscation_collected_matrix_K{}_s{}_e{}_d{}_{}_{}_{}.out".format(dataset, loss_function, K, start_cycle, e_epsilon, delta, recoverMethodStr, adjustmentModelStr, current_time)
			# running the whole crowdsensing process
			fixed_K_obfuscation(K, start_cycle, outputfile, outputCollectedMatrixFile, recoverMethod, adjustmentModel)

		elif obfuscation_style == "naive": #baseline obfuscation matrix
			outputfile = "./output/{}/naive/naive_obfuscation_K{}_s{}_e{}_{}_{}_{}.out".format(dataset, K, start_cycle, e_epsilon, recoverMethodStr, adjustmentModelStr, current_time)
			outputCollectedMatrixFile = "./output/{}/naive/naive_obfuscation_collected_matrix_K{}_s{}_e{}_{}_{}_{}.out".format(dataset, K, start_cycle, e_epsilon, recoverMethodStr, adjustmentModelStr, current_time)
			fixed_K_naive_obfuscation(e_epsilon, K, start_cycle, outputfile, outputCollectedMatrixFile, recoverMethod, adjustmentModel)
		
		elif obfuscation_style == "laplacian": #Laplacian obfuscation matrix (CCS'13)
			outputfile = "./output/{}/laplacian/laplacian_obfuscation_K{}_s{}_e{}_{}_{}_{}.out".format(dataset, K, start_cycle, e_epsilon, recoverMethodStr, adjustmentModelStr, current_time)
			outputCollectedMatrixFile = "./output/{}/laplacian/laplacian_obfuscation_collected_matrix_K{}_s{}_e{}_{}_{}_{}.out".format(dataset, K, start_cycle, e_epsilon, recoverMethodStr, adjustmentModelStr, current_time)
			fixed_K_laplacian_obfuscation(e_epsilon, K, start_cycle, outputfile, outputCollectedMatrixFile, recoverMethod, adjustmentModel)
		elif obfuscation_style == "exponential": #exponential mechanism considering the uncertainty matrix

			outputfile = "./output/{}/exponential/{}/exponential_obfuscation_K{}_s{}_e{}_{}_{}_{}.out".format(dataset, loss_function, K, start_cycle, e_epsilon, recoverMethodStr, adjustmentModelStr, current_time)
			outputCollectedMatrixFile = "./output/{}/exponential/{}/exponential_obfuscation_collected_matrix_K{}_s{}_e{}_{}_{}_{}.out".format(dataset, loss_function, K, start_cycle, e_epsilon, recoverMethodStr, adjustmentModelStr, current_time)
			fixed_K_exponential_obfuscation(e_epsilon, K, start_cycle, outputfile, outputCollectedMatrixFile, recoverMethod, adjustmentModel)
		elif obfuscation_style == "no": #no obfuscation (no privacy protection)
			outputfile = "./output/{}/no/no_obfuscation_K{}_s{}_{}_{}.out".format(dataset, K, start_cycle, recoverMethodStr, current_time)
			outputCollectedMatrixFile = "./output/{}/no/no_obfuscation_collected_matrix_K{}_s{}__{}_{}.out".format(dataset, K, start_cycle, recoverMethodStr, current_time)
			fixed_K_no_obfuscation(K, start_cycle, outputfile, outputCollectedMatrixFile, recoverMethod)

		elif obfuscation_style == "average": #no obfuscation and use average
			outputfile = "./output/{}/average/avg_obfuscation_K{}_s{}_{}.out".format(dataset, K, start_cycle, current_time)
			outputCollectedMatrixFile = "./output/{}/average/avg_obfuscation_collected_matrix_K{}_s{}_{}.out".format(dataset, K, start_cycle, current_time)
			fixed_K_average(K, start_cycle, outputfile, outputCollectedMatrixFile)

if __name__ == '__main__':
	#read from CMD parameters
	main(sys.argv[1:])

	