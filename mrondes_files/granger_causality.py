"""
Compute granger causality
(This method is not used during this project)
"""

import numpy as np
from mne_connectivity import spectral_connectivity_epochs

def compute_granger_causality(epochs, fmin=0, fmax=100, gc_n_lags=30):
    """
    Compute granger causality: A signal, x, is said to Granger-cause another signal, 
    y, if information from the past of x improves the prediction of the present of y 
    over the case where only information from the past of y is used

    Parameters:
    # epochs: 
    # fmin (int): 
    # fmax (int):
    # gc_n_lags (int):

    Returns:
    gc_matrix: 
    """
    n_channels = len(epochs.ch_names)

    seeds = []
    targets = []

    for i in range(n_channels):
        for j in range(n_channels):
            if i != j:
                seeds.append([i])
                targets.append([j])

    indices = (
        np.array(seeds),
        np.array(targets)
    )

    rank = (
        np.ones(len(seeds), dtype=int),
        np.ones(len(targets), dtype=int)
    )

    con_gc = spectral_connectivity_epochs(
        epochs,
        method=["gc"],
        indices=indices,
        fmin=fmin,
        fmax=fmax,
        rank=rank,
        gc_n_lags=gc_n_lags,
        verbose=False,
    )

    gc_data = con_gc.get_data()
    freqs = con_gc.freqs
    gc_mean = gc_data.mean(axis=1)

    gc_matrix = np.zeros((n_channels, n_channels))

    for k, (i, j) in enumerate(zip(np.array(seeds).ravel(), np.array(targets).ravel())):
        gc_matrix[i, j] = gc_mean[k]
    
    return gc_matrix