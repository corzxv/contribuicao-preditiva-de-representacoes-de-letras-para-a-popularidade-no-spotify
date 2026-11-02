"""Teste da operação de pooling com hidden states artificiais, sem pesos E5."""

from types import SimpleNamespace

import numpy as np

from tcc_music_popularity.multilingual_embeddings import OfflineEncoder


def test_real_forward_masks_padding_and_normalizes_only_synthetic_states():
    import torch

    class Tokenizer:
        def pad(self, inputs, **kwargs):
            assert kwargs == {
                "padding": True,
                "return_attention_mask": True,
                "return_tensors": "pt",
            }
            assert inputs["input_ids"] == [[1, 2], [1, 2, 3]]
            return {
                "input_ids": torch.tensor([[1, 2, 0], [1, 2, 3]]),
                "attention_mask": torch.tensor([[1, 1, 0], [1, 1, 1]]),
            }

    class SyntheticModel:
        def __call__(self, **batch):
            assert not torch.is_grad_enabled()
            states = torch.zeros((2, 3, 384), dtype=torch.float32)
            states[0, 0, 0] = 3
            states[0, 1, 1] = 4
            states[0, 2, :] = 1e8  # padding jamais pode entrar na média
            states[1, :, 0] = 1
            return SimpleNamespace(last_hidden_state=states)

    engine = OfflineEncoder.__new__(OfflineEncoder)  # Não executa AutoModel/loads.
    engine.torch, engine.tokenizer, engine.model = torch, Tokenizer(), SyntheticModel()
    actual = engine.forward([[1, 2], [1, 2, 3]])
    expected = np.zeros((2, 384), dtype=np.float32)
    expected[0, :2] = [0.6, 0.8]
    expected[1, 0] = 1.0
    assert np.allclose(actual, expected, atol=1e-7)
    assert actual.dtype == np.float32
