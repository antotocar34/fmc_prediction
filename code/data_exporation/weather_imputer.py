#%%
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_X_y, check_is_fitted, check_array
from sklearn.utils import column_or_1d
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import LabelEncoder


class ResponseRateEncoder(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.mapping = defaultdict()
        pass
    def check_df(self, df):
        if not isinstance(df, pd.DataFrame):
            return pd.DataFrame(data=df)
        else:
            return df
    def fit(self, X, y):
        y = column_or_1d(y, warn=True)
        self.X_ = X
        X = self.check_df(X)
        sums = defaultdict(int)
        for col in X.columns:
            map = defaultdict()
            counts = Counter(X[col])
            for i, cat in enumerate(X[col]):
                sums[cat] += y[i]
            for cat in X[col]:
                map[cat] = (sums[cat] / counts[cat])
            self.mapping[col] = map
        return self
    def transform(self, X):
        X = X.copy()
        X = self.check_df(X)
        for col in X.columns:
            map = self.mapping[col]
            for each in X[col].unique():
                if each not in map.keys():
                    map[each] = 0.0
            X[col] = X[col].map(map, na_action="ignore")
        return X
