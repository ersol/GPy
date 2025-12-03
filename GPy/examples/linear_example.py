import GPy
import numpy as np
import pandas as pd
from copy import deepcopy

k = GPy.kern.Linear(input_dim=1) + GPy.kern.Linear(input_dim=1)*GPy.kern.White(input_dim=1)

alpha = 1
nsamples = 5000#40
np.random.seed(2)
rng = np.random.default_rng(seed=2)
currents = rng.random(nsamples)*1000
Tp = rng.normal(loc=10,scale=5,size=nsamples)
temp_std = 0.1
Tavg = Tp + rng.normal(loc=0,scale=temp_std,size=nsamples) + currents*rng.normal(loc=alpha,scale=alpha*0.5,size=nsamples)

df = pd.DataFrame({'current':currents,'Tp':Tp,'Tavg':Tavg, "deltaT": Tavg-Tp})
df = df.sort_values("current")
X = df["current"].values.reshape(-1,1)
Y = df["deltaT"].values.reshape(-1,1)

dL_dK = np.identity(4)
dL_dK_pert = deepcopy(dL_dK)
dL_dK_pert[2,3] = 1
dL_dKdiag = np.array([1,1,1,1])
X_test = np.array([1,2,3,4]).reshape(-1,1)
X2_test = np.array([3,5,7,9]).reshape(-1,1)

print("K(X,X):")
print(k.K(X_test).diagonal())
print("Kdiag(X):")
print(k.Kdiag(X_test))
print("dL_dK * dK_dX:")
print(k.gradients_X(dL_dK, X_test, X2=X2_test))
print("dL_dK_pert * dK_dX:")
print(k.gradients_X(dL_dK_pert, X_test, X2=X2_test))
print("dL_dKdiag * dKdiag_dX:")
print(k.gradients_X_diag(dL_dKdiag, X_test))

small_ind = rng.choice(list(range(len(X))), 40)

small_X = X[small_ind]
small_X_std = np.std(X[small_ind], axis=0)
small_X_scaled = X[small_ind]/small_X_std
small_Y = Y[small_ind]
m = GPy.models.GPRegression(small_X_scaled,small_Y,k)
print(m)
m.constrain_positive('*variance')
m['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
m.optimize()
print("1D vanilla GP:")
print(m)

plt = GPy.plotting.plotly_dep.plot_definitions.PlotlyPlotsBase()
plots = m.plot(xscale=small_X_std)
plt.show_canvas(plots)

num_inducing = 20
X_std = np.std(X,axis=0)
print(f"1D X_std: {X_std}")
X_scaled = X/X_std
#normalizer = GPy.util.normalizer.Standardize(subtract_mean=False)
SPm = GPy.models.sparse_gp_regression.SparseGPRegression(X_scaled,Y,kernel=k,num_inducing=num_inducing)
SPm.constrain_positive('*variance')
SPm['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
SPm.optimize('adadelta')
print("Sparse 1D model:")
print(SPm)
#print(f"Inducing values:\n{SPm.Z.values}")
#print(f"X_scaling:\n{X_std}")
#print(f"Scaled inducing values:\n{SPm.Z.values*X_std}")

plt = GPy.plotting.plotly_dep.plot_definitions.PlotlyPlotsBase()
plots = SPm.plot()
plt.show_canvas(plots)
