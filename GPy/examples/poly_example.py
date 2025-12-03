import GPy
import numpy as np
import pandas as pd
from copy import deepcopy

alpha = 1e-5
nsamples = 5000#40
np.random.seed(2)
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
small_X_std = np.std(X[small_ind], axis=0)
small_X_scaled = X[small_ind]/small_X_std
small_Y = Y[small_ind]
m = GPy.models.GPRegression(small_X_scaled,small_Y,k)
m.constrain_positive('*variance')
m['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
m['sum.poly.bias'].constrain_fixed(0)
m['sum.mul.poly.bias'].constrain_fixed(0)
m.optimize()
print("1D vanilla GP:")
print(m)

plt = GPy.plotting.plotly_dep.plot_definitions.PlotlyPlotsBase()
plots = m.plot(xscale=small_X_std)
plt.show_canvas(plots)

dL_dK = np.identity(4)
dL_dK_pert = deepcopy(dL_dK)
dL_dK_pert[2,3] = 1
dL_dKdiag = np.array([1,1,1,1])
X_test = np.array([1,2,3,4]).reshape(-1,1)
X2_test = np.array([3,5,7,9]).reshape(-1,1)

print("K(X,X):")
print(k.K(X_test))
print("Kdiag(X):")
print(k.Kdiag(X_test))
print("dL_dK * dK_dX:")
print(k.gradients_X(dL_dK, X_test, X2=X2_test))
print("dL_dK_pert * dK_dX:")
print(k.gradients_X(dL_dK_pert, X_test, X2=X2_test))
print("dL_dKdiag * dKdiag_dX:")
print(k.gradients_X_diag(dL_dKdiag, X_test))

num_inducing = 20
X_std = np.std(X,axis=0)
print(f"1D X_std: {X_std}")
X_scaled = X/X_std
#normalizer = GPy.util.normalizer.Standardize(subtract_mean=False)
SPm = GPy.models.sparse_gp_regression.SparseGPRegression(X_scaled,Y,kernel=k,num_inducing=num_inducing)
SPm.constrain_positive('*variance')
SPm['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
SPm['sum.poly.bias'].constrain_fixed(0)
SPm['sum.mul.poly.bias'].constrain_fixed(0)
SPm.optimize()
print("Sparse 1D model:")
print(SPm)
print(f"Inducing values:\n{SPm.Z.values}")
print(f"X_scaling:\n{X_std}")
print(f"Scaled inducing values:\n{SPm.Z.values*X_std}")

plt = GPy.plotting.plotly_dep.plot_definitions.PlotlyPlotsBase()
plots = SPm.plot()
plt.show_canvas(plots)


#Multivariate kernel
alpha = 1e-5
beta = 1.5/630
nsamples = 5000
rng = np.random.default_rng(seed=2)
currents = rng.random(nsamples)*1000
I_T = rng.random(nsamples)*1000
I2 = currents**2
Tp = rng.normal(loc=10,scale=5,size=nsamples)
temp_std = 0.1
Tavg = Tp + rng.normal(loc=0,scale=temp_std,size=nsamples) + I2*rng.normal(loc=alpha,scale=alpha*0.5,size=nsamples) + I_T*rng.normal(loc=beta,scale=beta*0.4,size=nsamples)

df = pd.DataFrame({'current':currents,'I_T':I_T,'Tp':Tp,'Tavg':Tavg, "deltaT": Tavg-Tp})
X = df[["current", "I_T"]].values#.reshape(-1,1)
Y = df["deltaT"].values.reshape(-1,1)

current_kernel = GPy.kern.src.add.Add([GPy.kern.Poly(input_dim=1, order=2, active_dims=[0],name="current_poly"), GPy.kern.Poly(input_dim=1, order=2, active_dims=[0],name="current_poly")*GPy.kern.White(input_dim=1, active_dims=[0],name="current_white")])
solar_irradiation_kernel = GPy.kern.src.add.Add([GPy.kern.Linear(input_dim=1, active_dims=[1],name="I_T_linear"), GPy.kern.Linear(input_dim=1, active_dims=[1],name="I_T_linear")*GPy.kern.White(input_dim=1, active_dims=[1],name="I_T_white")])
k =  GPy.kern.src.add.Add([current_kernel, solar_irradiation_kernel])

small_ind = rng.choice(list(range(len(X))), 40)
small_X = X[small_ind]
small_X_mean = np.mean(small_X,axis=0)
print(f"small_X_mean: {small_X_mean}")
small_X_std = np.std(small_X,axis=0)
print(f"small_X_std: {small_X_std}")
small_X_scaled = small_X/small_X_std
small_Y = Y[small_ind]

m_prescaled = GPy.models.GPRegression(small_X_scaled,small_Y,k)
m_prescaled.constrain_positive('*variance')
m_prescaled['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
m_prescaled['sum.current_poly.bias'].constrain_fixed(0)
m_prescaled['sum.mul.current_poly.bias'].constrain_fixed(0)
m_prescaled.optimize()
print(m_prescaled)

plots = m_prescaled.plot(projection="3d", xscale=small_X_std)
plots[0].update_layout(
    scene_xaxis_title="Current [A]",
    scene_yaxis_title="Solar irradiation [W/m^2]"
)
plt.show_canvas(plots)

num_inducing = 9
X_std = np.std(X,axis=0)
X_scaled = X/X_std
SPm = GPy.models.sparse_gp_regression.SparseGPRegression(X_scaled,Y,kernel=k,num_inducing=num_inducing)
SPm.constrain_positive('*variance')
SPm['Gaussian_noise.variance'].constrain_fixed(temp_std**2)
SPm['sum.current_poly.bias'].constrain_fixed(0)
SPm['sum.mul.current_poly.bias'].constrain_fixed(0)
SPm.optimize()
print(SPm)

#print(f"Inducing values before ploting:\n{SPm.Z.values}")
plots = SPm.plot(projection="3d", plot_inducing=False)
print(f"Inducing values:\n{SPm.Z.values}")
print(f"X_scaling:\n{X_std}")
print(f"Scaled inducing values:\n{SPm.Z.values*X_std}")
plots[0].update_layout(
    scene_xaxis_title="Current [A]",
    scene_yaxis_title="Solar irradiation [W/m^2]"
)
plt.show_canvas(plots)"""
