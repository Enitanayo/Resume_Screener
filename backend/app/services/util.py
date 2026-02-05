import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def cos_sim(a, b):
    """
    Compute cosine similarity between two vectors using scikit-learn.
    Returns a numpy array.
    """
    # Ensure inputs are 2D arrays as sklearn expects [n_samples, n_features]
    a = np.asarray(a)
    b = np.asarray(b)

    if a.ndim == 1:
        a = a.reshape(1, -1)
    if b.ndim == 1:
        b = b.reshape(1, -1)

    return cosine_similarity(a, b)
