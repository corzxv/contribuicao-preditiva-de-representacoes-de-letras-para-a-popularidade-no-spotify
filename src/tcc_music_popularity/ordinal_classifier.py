"""Logística ordinal de três classes: chances proporcionais e penalização L2."""

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit, logit
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_is_fitted

from .popularity_levels import require


def log_probabilities(parameters, x):
    """P(Y≤j)=sigmoid(theta_j−xβ); limiares ordenados por gap=exp(d)."""
    beta, first, log_gap = parameters[:-2], parameters[-2], parameters[-1]
    gap = np.exp(log_gap)
    low = first - x @ beta
    high = low + gap
    return np.column_stack(
        (
            log_expit(low),
            log_expit(high) + log_expit(-low) + np.log(-np.expm1(-gap)),
            log_expit(-high),
        )
    )


def objective(parameters, x, y, alpha):
    """Média da log-verossimilhança negativa + alpha ||β||²/2; gradiente analítico."""
    beta, first, log_gap = parameters[:-2], parameters[-2], parameters[-1]
    gap = np.exp(log_gap)
    low = first - x @ beta
    high = low + gap
    f_low, f_high = expit(low), expit(high)
    logp = log_probabilities(parameters, x)
    loss = -np.mean(logp[np.arange(len(y)), y]) + alpha * np.dot(beta, beta) / 2
    eta_gradient = np.where(y == 0, 1 - f_low, np.where(y == 2, -f_high, 1 - f_high - f_low))
    gap_gradient = np.where(
        y == 0, 0.0, np.where(y == 2, f_high, f_high - 1 - np.exp(-gap) / (-np.expm1(-gap)))
    )
    gradient = np.concatenate(
        (
            x.T @ eta_gradient / len(y) + alpha * beta,
            [-np.mean(eta_gradient), gap * np.mean(gap_gradient)],
        )
    )
    require(np.isfinite(loss) and np.isfinite(gradient).all(), "Objetivo ordinal não finito.")
    return float(loss), gradient


class OrdinalLogit(ClassifierMixin, BaseEstimator):
    """Sem intercepto em X, com dois limiares livres não penalizados; pesos iguais."""

    def __init__(self, alpha=0.01, max_iter=1000, gradient_tolerance=1e-6):
        self.alpha = alpha
        self.max_iter = max_iter
        self.gradient_tolerance = gradient_tolerance

    def fit(self, x, y):
        x, y = np.asarray(x, dtype=float), np.asarray(y)
        require(
            x.ndim == 2 and len(x) == len(y) and np.isfinite(x).all(), "Matriz ordinal inválida."
        )
        require(
            y.ndim == 1 and set(y.tolist()) == {0, 1, 2}, "Treino ordinal exige as três classes."
        )
        require(self.alpha > 0 and self.max_iter > 0, "Penalização/iterações inválidas.")
        y = y.astype(int)
        proportions = np.bincount(y, minlength=3) / len(y)
        thresholds = logit(np.cumsum(proportions)[:2])
        initial = np.r_[np.zeros(x.shape[1]), thresholds[0], np.log(thresholds[1] - thresholds[0])]
        result = minimize(
            objective,
            initial,
            args=(x, y, self.alpha),
            jac=True,
            method="L-BFGS-B",
            bounds=[(None, None)] * (x.shape[1] + 1) + [(-8, 8)],
            options={
                "maxiter": self.max_iter,
                "gtol": self.gradient_tolerance,
                "ftol": 1e-12,
                "maxls": 40,
            },
        )
        require(result.success, "Otimizador ordinal não convergiu: " + str(result.message))
        require(-8 + 1e-6 < result.x[-1] < 8 - 1e-6, "Gap ordinal atingiu limite numérico.")
        require(np.max(np.abs(result.jac)) <= 1e-4, "Gradiente final ordinal acima da tolerância.")
        self.parameters_ = result.x
        self.coef_ = result.x[:-2][None, :]
        self.thresholds_ = np.array([result.x[-2], result.x[-2] + np.exp(result.x[-1])])
        self.classes_ = np.arange(3)
        self.n_features_in_ = x.shape[1]
        self.n_iter_ = result.nit
        self.max_abs_gradient_ = float(np.max(np.abs(result.jac)))
        self.objective_ = float(result.fun)
        return self

    def predict_proba(self, x):
        check_is_fitted(self, "parameters_")
        x = np.asarray(x, dtype=float)
        require(
            x.ndim == 2 and x.shape[1] == self.n_features_in_ and np.isfinite(x).all(),
            "Matriz de previsão ordinal inválida.",
        )
        probabilities = np.exp(log_probabilities(self.parameters_, x))
        require(
            np.isfinite(probabilities).all()
            and (probabilities >= 0).all()
            and np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-12),
            "Probabilidades ordinais incoerentes.",
        )
        return probabilities

    def predict(self, x):
        return self.predict_proba(x).argmax(axis=1)
