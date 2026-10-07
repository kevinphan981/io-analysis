import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import random

'''
Assumptions
-----------
    Things are normally distributed, with presets for triangular or uniform distributions. Possible lognormal options for disaster events.

Overview
--------
    I have to modify some of the code in main.py so that every value of the shock computes with every index rather than for-looping everything.

    
TODO:
----
    1. Needs to actually have the industry within the shock_params, will have to reconsider when the other shocks are developed.
    2. Hmmmm.... this will be harder to consider
    
'''



def monte_carlo(A_matrix: pd.DataFrame, shock_params: dict, n_iterations: int = 10000):
    n_sectors = A_matrix.shape[0] # should be square anyway
    leontief = np.linalg.inv(np.eye(n_sectors) - A_matrix)

    # build a sample of shocks with the iterations we input
    shock_samples = np.zeroes((n_sectors, n_iterations))

    for i, params in enumerate(shock_samples):
        if params is None:
            continue

        dist_type = params.get('dist', 'uniform')

        if dist_type == 'triangular':
            low, mode, high = params['low'], params['mode'], params['high']
            # we take the 'c' for the triangular distribution
            c = (mode - low) / (high - low) if high > low else 0.5
            loc = low
            scale = high - low
            shock_samples[i, :] = stats.triang.rvs(c, loc = loc, scale = scale, size = n_iterations)

        elif dist_type == 'uniform':
            low, high = params['low'], params['high']
            shock_samples[i, :] = np.random.uniform(low, high, n_iterations)

        elif dist_type == 'normal':
            mean, std = params['mean'], params['std']
            # we could clip here so that there is no such thing as a loss, but we'd have to see in future iterations.
            # in other words, i feel like its biased to not include negative cases
            draws = np.random.normal(mean, std, n_iterations)
            # shock_samples[i, :] = np.clip(draws, a_min = 0, a_max = None)
            shock_samples = draws




        

        
    return
