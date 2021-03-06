import numpy as np
import pandas as pd
import pickle
import statsmodels.api as sm
from sklearn import linear_model, neural_network
from sklearn import model_selection, metrics
from sklearn.ensemble import RandomForestRegressor

# Get data
filename = "./data/aggregated_2008-2009.pkl"
with open(filename, "rb") as f:
	dataset = pickle.load(f)
	f.close()

#print(dataset.shape)

# May need to impute blank data
# Finding a "--" implies missing data
dataset = dataset[(dataset[dataset.columns] != "--").all(axis=1)]

# Remove all string features
# dataset = dataset.loc[:, dataset.dtypes != str]
# print(dataset.shape)

# Try forcing to numeric
dataset = dataset.apply(lambda row: pd.to_numeric(row, errors='coerce', downcast='float'))
#g = dataset.columns.to_series().groupby(dataset.dtypes).groups
#print(g)

# Remove all columns with NAs
dataset = dataset.dropna(axis = 1)

# Remove all columns that are not numeric
dataset = dataset._get_numeric_data()
print("Final dataset shape = " + str(dataset.shape))

# Label cols
label = "Points"
label_ref = "OU"
labels = [1 if row[label] - row[label_ref] > 0 else -1 for i, row in dataset.iterrows()]
labels = np.array(labels)
label_cols = ["Points", "Win Margin", "2H Points", "2H Win Margin"]

print("Average label of our dataset: {} (should be close to 0).".format(sum(labels)/len(labels)))

# Remove anything involving team name
stripped_cols = [c for c in dataset.columns if "Team" not in c and c != "Home" and c != "Away"]
dataset = dataset[stripped_cols]

# Let's model over-under using a GLM with a Negative Binomial distribution
#labels = dataset[label]
data = dataset[dataset.columns.difference(label_cols)]
dataWithConst = sm.add_constant(data)

# Train/test split
X_train, X_test, y_train, y_test = model_selection.train_test_split(data, labels, test_size=0.20, random_state=42) # 20% test

X_train, X_val, y_train, y_val = model_selection.train_test_split(X_train, y_train, test_size=0.25, random_state=42) # 20% val, 60% train

X_train_wConst = sm.add_constant(X_train)
X_val_wConst = sm.add_constant(X_val)
X_test_wConst = sm.add_constant(X_test)

'''
# Model may need interaction terms
print(y_train)
print(X_train_wConst)
neg_binom_model = sm.GLM(y_train.values, X_train_wConst.values, family=sm.families.NegativeBinomial()) # First pass responding variable, then matrix of features
neg_binom_results = neg_binom_model.fit()
print(neg_binom_results.summary)

# Can also try poisson regression
poisson_model = sm.GLM(y_train, X_train_wConst, family=sm.families.Poisson()) # First pass responding variable, then matrix of features
poisson_results = poisson_model.fit()
print(poisson_results.summary)
'''

# SKLEARN: INTERCEPT CALCULATED BY DEFAULT, NO NEED TO ADD IN COLUMN OF ONES

# # Create linear regression object
# regr = linear_model.LinearRegression()
# # Train the model using the training sets
# regr.fit(X_train, y_train)
# # Make predictions using the testing set
# y_pred = regr.predict(X_val)
# # The coefficients
# #print('Linreg Coefficients: \n', regr.coef_)
# # The mean squared error
# print("Linreg Mean squared error: %.2f"
#       % metrics.mean_squared_error(y_val, y_pred))
# # Explained variance score: 1 is perfect prediction
# print('Linreg Variance score: %.2f' % metrics.r2_score(y_val, y_pred))

alphas = [10]
mses = []
r2s = []
for a in alphas:
	# Create LASSO
	regr = linear_model.Lasso(alpha = a)
	# Train the model using the training sets
	regr.fit(X_train, y_train)
	# Make predictions using the testing set
	y_pred = regr.predict(X_val)
	# The coefficients
	# print('Linreg Coefficients: \n', regr.coef_)
	# The mean squared error
	print("Linreg Mean squared error: %.2f"
	      % metrics.mean_squared_error(y_val, y_pred))
	mses.append(metrics.mean_squared_error(y_val, y_pred))
	# Explained variance score: 1 is perfect prediction
	print('Linreg Variance score: %.2f' % metrics.r2_score(y_val, y_pred))
	r2s.append(metrics.r2_score(y_val, y_pred))

# Try random forests

#####################
# FEATURE SELECTION #
#####################

# Try PCA
from sklearn.decomposition import PCA
pca = PCA(n_components=15)
pca.fit(X_train)
print(pca.explained_variance_ratio_)
X_train = pca.transform(X_train)
X_val = pca.transform(X_val)
X_test = pca.transform(X_test)

'''
# Try features with nonzero coefficients from lasso

# filter = (regr.coef_ != 0)
print(X_train.shape)
X_train = X_train[:,[i for i in range(len(regr.coef_)) if regr.coef_[i] != 0 ]]
print(X_train.shape)
X_val = X_val[:,[i for i in range(len(regr.coef_)) if regr.coef_[i] != 0]]
'''

from sklearn.preprocessing import StandardScaler  
scaler = StandardScaler()  
scaler2 = StandardScaler()
# Don't cheat - fit only on training data
scaler.fit(X_train)  
scaler2.fit(y_train[:,np.newaxis])
X_train = scaler.transform(X_train)  
y_train = scaler2.transform(y_train[:,np.newaxis]).squeeze()
# apply same transformation to test data
X_val = scaler.transform(X_val)
y_val = scaler2.transform(y_val[:,np.newaxis]).squeeze()
X_test = scaler.transform(X_test)  
y_test = scaler2.transform(y_test[:,np.newaxis]).squeeze()

# Create linear regression object
regr = neural_network.MLPRegressor(solver='lbfgs', alpha=1e-5, activation = 'logistic', hidden_layer_sizes=(7,5), random_state=1)
# Train the model using the training sets
regr.fit(X_train, y_train)
# Make predictions using the testing set
y_pred = regr.predict(X_val)
# The mean squared error
print("Mean squared error: %.2f"
      % metrics.mean_squared_error(y_val, y_pred))
# Explained variance score: 1 is perfect prediction
print('Variance score: %.2f' % metrics.r2_score(y_val, y_pred))



