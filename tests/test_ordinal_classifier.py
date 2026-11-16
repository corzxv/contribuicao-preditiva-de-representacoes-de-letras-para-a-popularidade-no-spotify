import numpy as np
import pytest
from scipy.optimize import approx_fprime, minimize
from scipy.special import expit
from threadpoolctl import threadpool_limits

from tcc_music_popularity import ordinal_classifier as mod


def test_gradiente_confere_com_diferencas_finitas():
    rng = np.random.default_rng(71)
    x = rng.normal(size=(21, 4))
    y = np.arange(21) % 3
    parameters = np.array([0.4, -0.2, 0.7, 0.1, -0.5, 0.3])
    value, analytic = mod.objective(parameters, x, y, 0.05)
    numerical = approx_fprime(parameters, lambda p: mod.objective(p, x, y, 0.05)[0], epsilon=1e-7)
    assert np.isfinite(value)
    assert np.max(np.abs(analytic - numerical)) < 1e-6


def test_probabilidades_e_ajuste_conferem_com_verossimilhanca_independente():
    rng = np.random.default_rng(82)
    x = rng.normal(size=(90, 2))
    latent = x[:, 0] * 0.8 - x[:, 1] * 0.3 + rng.logistic(size=90)
    y = np.searchsorted([-0.6, 0.9], latent)
    model = mod.OrdinalLogit(alpha=0.05).fit(x, y)

    def independent(parameters):
        eta = x @ parameters[:-2]
        first = expit(parameters[-2] - eta)
        second = expit(parameters[-2] + np.exp(parameters[-1]) - eta)
        probability = np.column_stack((first, second - first, 1 - second))
        return (
            -np.log(probability[np.arange(len(y)), y]).mean()
            + 0.05 * np.sum(parameters[:-2] ** 2) / 2
        )

    reference = minimize(independent, np.zeros(4), method="BFGS", options={"gtol": 1e-7})
    assert independent(model.parameters_) == pytest.approx(reference.fun, abs=1e-8)
    assert model.parameters_ == pytest.approx(reference.x, abs=1e-4)
    assert np.allclose(model.predict_proba(x).sum(axis=1), 1, atol=1e-12)
    assert model.thresholds_[0] < model.thresholds_[1]


def test_modelo_sem_preditores_reproduz_frequencias():
    y = np.array([0] * 12 + [1] * 6 + [2] * 2)
    model = mod.OrdinalLogit().fit(np.zeros((20, 0)), y)
    assert model.predict_proba(np.zeros((1, 0)))[0] == pytest.approx([0.6, 0.3, 0.1])


def test_extremos_numericos_nao_produzem_log_infinito():
    logp = mod.log_probabilities(np.array([1.0, -0.4, 0.2]), np.array([[-1000.0], [1000.0]]))
    assert np.isfinite(logp).all()
    assert np.exp(logp).sum(axis=1) == pytest.approx([1, 1])
    with pytest.raises(ValueError, match="três classes"):
        mod.OrdinalLogit().fit(np.ones((4, 1)), [0, 0, 1, 1])


def test_falha_de_convergencia_nao_e_aceita():
    rng = np.random.default_rng(71)
    x = rng.normal(size=(60, 3))
    with pytest.raises(ValueError, match="não convergiu"):
        mod.OrdinalLogit(max_iter=1).fit(x, np.arange(60) % 3)


def test_384_dimensoes_sinteticas_com_penalizacao_minima():
    rng = np.random.default_rng(91)
    x = rng.normal(size=(72, 384))
    y = np.arange(72) % 3
    with threadpool_limits(limits=2):
        model = mod.OrdinalLogit(alpha=0.001).fit(x, y)
    assert model.max_abs_gradient_ <= 1e-4
    assert model.predict_proba(x[:4]).sum(axis=1) == pytest.approx(np.ones(4))
