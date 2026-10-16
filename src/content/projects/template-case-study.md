---
title: "Template: Case Study Title"
domain: "Supply chain"
data_source:
  name: "Kaggle: dataset name"
  url: "https://www.kaggle.com/datasets"
  license: "CC0 / check the dataset page"
methods: ["MIP", "Forecasting"]
solver: "HiGHS via Pyomo"
tags: ["template", "inventory"]
repo: "https://github.com/"
date: 2026-10-16
---

Copy this file, rename it, and replace every section. Delete this line.

## 1. Business problem

Who decides what, how often, and what does a bad decision cost? One paragraph, in the decision-maker's words.

## 2. Data

Source, link, license, row counts, and what you had to clean. State which columns become parameters of the model.

## 3. EDA

Three to five plots that change a modeling choice (not decoration). Say what each one changed.

## 4. Prediction / forecasting

Only if the optimization needs a forecast. Report the error metric and how forecast error flows into the model.

## 5. Optimization model

Decision variables, objective, constraints. For example:

$$
\min_{x,\,y}\ \sum_{t=1}^{T}\left(c\,x_t + h\,I_t\right)
\quad\text{s.t.}\quad I_t = I_{t-1} + x_t - d_t,\ \ x_t \le M\,y_t,\ \ x_t, I_t \ge 0,\ y_t \in \{0,1\}.
$$

Inline math works too: $I_t$ is end-of-period inventory. Name the solver, the model size and the solve time.

## 6. Results & sensitivity

Compare against a baseline policy. Show how the answer moves when the key parameter changes by ±20%.

## 7. Limitations

What the model ignores, where the data is thin, and what would change your recommendation.

## 8. Reproduce

Link the repository, the environment file, and the single command that regenerates the results.
