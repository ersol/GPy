import GPy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

alpha = 1e-5
nsamples = 5000#40
rng = np.random.default_rng(seed=2)
currents = rng.random(nsamples)*1000
I2 = currents**2
Tp = rng.normal(loc=10,scale=5,size=nsamples)
temp_std = 0.1
Tavg = Tp + rng.normal(loc=0,scale=temp_std,size=nsamples) + I2*rng.normal(loc=alpha,scale=alpha*0.5,size=nsamples)

df = pd.DataFrame({'current':currents,'Tp':Tp,'Tavg':Tavg, "deltaT": Tavg-Tp})
df = df.sort_values("current")
X = df["current"].values.reshape(-1,1)
Y = df["deltaT"].values.reshape(-1,1)

k = GPy.kern.Poly(input_dim=1, order=2) + GPy.kern.Poly(input_dim=1, order=2)*GPy.kern.White(input_dim=1)

small_ind = rng.choice(list(range(len(X))), 40)

small_X = X[small_ind]
small_Y = Y[small_ind]
m = GPy.models.GPRegression(small_X,small_Y,k)
m.constrain_positive('*variance')
m['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
m['sum.poly.bias'].constrain_fixed(0)
m['sum.mul.poly.bias'].constrain_fixed(0)
m.optimize()

m.plot()
plt.show()

print("K(X,X):")
print(k.K(np.array([0,4,1.3,2,5,6,3,2]).reshape(-1,1)).diagonal())
print("Kdiag(X):")
print(k.Kdiag(np.array([0,4,1.3,2,5,6,3,2]).reshape(-1,1)))
print("dL_dK * dK_dX:")
print(k.gradients_X(np.identity(4), np.array([1,2,3,4]).reshape(-1,1), X2=np.array([3,5,7,9]).reshape(-1,1)))
print("dL_dKdiag * dKdiag_dX:")
print(k.gradients_X_diag(np.array([1,1,1,1]).reshape(1,-1), np.array([1,2,3,4]).reshape(-1,1)))


num_inducing = 100
SPm = GPy.models.sparse_gp_regression.SparseGPRegression(X,Y,kernel=k,num_inducing=num_inducing)
SPm.constrain_positive('*variance')
SPm['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
SPm['sum.poly.bias'].constrain_fixed(0)
SPm['sum.mul.poly.bias'].constrain_fixed(0)
SPm.optimize()

SPm.plot()
plt.show()
