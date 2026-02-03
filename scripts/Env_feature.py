#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, KFold
from sklearn.metrics import r2_score

from scipy.stats import randint

import shap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("RI.csv", sep=None, engine="python")

y = df.iloc[:, 0].values
X = df.iloc[:, 1:]

feature_names = X.columns.tolist()

n_samples = X.shape[0]
n_features = X.shape[1]

print(f"Sample size: {n_samples}")
print(f"Number of features: {n_features}")

def get_param_dist_by_sample_size(n_samples):
    if n_samples <= 30:
        param_dist = {
            "n_estimators": randint(600, 1201),
            "max_depth": randint(3, 7),
            "min_samples_leaf": randint(3, 9)
        }
        n_iter = 15
        cv = 3

    elif n_samples <= 100:
        param_dist = {
            "n_estimators": randint(400, 1001),
            "max_depth": randint(4, 11),
            "min_samples_leaf": randint(3, 7)
        }
        n_iter = 20
        cv = 5

    elif n_samples <= 500:
        param_dist = {
            "n_estimators": randint(300, 1001),
            "max_depth": [None] + list(range(6, 21)),
            "min_samples_leaf": randint(2, 6)
        }
        n_iter = 25
        cv = 5

    else:
        param_dist = {
            "n_estimators": randint(300, 1501),
            "max_depth": [None] + list(range(8, 31)), 
            "min_samples_leaf": randint(1, 5)
        }
        n_iter = 30
        cv = 5

    return param_dist, n_iter, cv


param_dist, n_iter, cv = get_param_dist_by_sample_size(n_samples)

print("RandomizedSearch config:")
print("n_iter =", n_iter, ", cv =", cv)
print("Parameter space:", param_dist)

rf_base = RandomForestRegressor(
    max_features="sqrt",   
    random_state=42,
    n_jobs=-1
)


search = RandomizedSearchCV(
    estimator=rf_base,
    param_distributions=param_dist,
    n_iter=n_iter,
    cv=cv,
    scoring="r2",
    random_state=42,
    n_jobs=-1
)

search.fit(X, y)

rf_best = search.best_estimator_

print("Best parameters:", search.best_params_)


kf = KFold(n_splits=cv, shuffle=True, random_state=42)
r2_scores = []

for train_idx, test_idx in kf.split(X):
    rf_tmp = RandomForestRegressor(**rf_best.get_params())
    rf_tmp.fit(X.iloc[train_idx], y[train_idx])
    y_pred = rf_tmp.predict(X.iloc[test_idx])
    r2_scores.append(r2_score(y[test_idx], y_pred))

print(f"CV R2 mean = {np.mean(r2_scores):.3f}")

explainer = shap.TreeExplainer(rf_best)
shap_values = explainer.shap_values(X)

shap_importance = np.abs(shap_values).mean(axis=0)

shap_df = pd.DataFrame({
    "Feature": feature_names,
    "MeanAbsSHAP": shap_importance
}).sort_values("MeanAbsSHAP", ascending=False)

print(shap_df)

shap_df.to_csv("SHAP_feature_importance.csv", index=False)


plt.figure()
shap.summary_plot(
    shap_values,
    X,
    feature_names=feature_names,
    show=False
)
plt.tight_layout()
plt.savefig("SHAP_summary_dot.png", dpi=300)
plt.close()


plt.figure()
shap.summary_plot(
    shap_values,
    X,
    feature_names=feature_names,
    plot_type="bar",
    show=False
)
plt.tight_layout()
plt.savefig("SHAP_summary_bar.png", dpi=300)
plt.close()

for feat in feature_names:
    plt.figure()
    shap.dependence_plot(
        feat,
        shap_values,
        X,
        interaction_index=None,
        show=False
    )
    plt.tight_layout()
    plt.savefig(f"SHAP_dependence_{feat}.png", dpi=300)
    plt.close()
