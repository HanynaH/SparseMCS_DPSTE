import numpy as np
import pandas as pd

file_name = "fast_approximation_epsilon8_delta1.out_cplex"

file_str = ""
with open (file_name, "r") as inputfile:
	for line in inputfile:
		file_str += " " + line.strip()
		# print(file_str)

file_str = file_str.replace("[", "").replace("]", "\n")
file = open("test.txt","w")
file.write(file_str)
file.close()

txt = np.loadtxt("test.txt")
txtDF = pd.DataFrame(txt)
txtDF.to_csv("test.csv",index=False)
#
# with open (file_name+"_new", "w") as outputfile:
# 	outputfile.write(file_str)