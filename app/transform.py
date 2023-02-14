from typing import List
import numpy as np

# util code to convert int8 representation to float32
# see https://github.com/satzbeleg/evidence-features
# 


# evf.utils.py
def divide_by_1st_col(feats: List[List[float]]):
    n_feats = feats.shape[-1] - 1
    denom = np.maximum(feats[:, 0], 1)
    return feats[:, 1:] / np.tile(denom.reshape(-1, 1), n_feats)


# evf.utils.py
def divide_by_sum(feats: List[List[float]]):
    n_feats = feats.shape[-1]
    denom = np.maximum(feats.sum(axis=1), 1)
    return feats / np.tile(denom.reshape(-1, 1), n_feats)


# https://github.com/satzbeleg/keras-hrp/blob/main/keras_hrp/serialize.py
def int8_to_bool(serialized: List[np.int8]) -> List[bool]:
    return np.unpackbits(
        serialized.astype(np.uint8),
        bitorder='big').reshape(-1)


# evf.transform_sbert.py
def sbert_i2b(encoded):
    return np.vstack([int8_to_bool(enc) for enc in encoded])


# ev.transform_sqlen.py
def seqlen_i2f(feats):
    return np.log(feats + 1.)


# evf.transform_fasttext176.py
def int8_to_scaledfloat(idx: np.int8) -> float:
    idx = min(127, max(-128, idx))
    x = 1. - (float(idx) + 128.0) / 255.0
    return x


# evf.transform_fasttext176.py
def fasttext176_i2f(encoded):
    pdf = [[int8_to_scaledfloat(i) for i in tmp] for tmp in encoded]
    return np.vstack(pdf).astype(float)



# evf.transform_all.py
def i2f(feats1, feats2, feats3, feats4,
        feats5, feats6, feats7, feats8,
        feats9, feats12, feats13, feats14):
    # convert to numpy
    feats1 = np.array(feats1, dtype=np.int8)
    feats2 = np.array(feats2, dtype=np.int8)
    feats3 = np.array(feats3, dtype=np.int8)
    feats4 = np.array(feats4, dtype=np.int8)
    feats5 = np.array(feats5, dtype=np.int16)
    feats6 = np.array(feats6, dtype=np.int16)
    feats7 = np.array(feats7, dtype=np.int16)
    feats8 = np.array(feats8, dtype=np.int8)
    feats9 = np.array(feats9, dtype=np.int8)
    feats12 = np.array(feats12, dtype=np.int16)
    feats13 = np.array(feats13, dtype=np.int8)
    feats14 = np.array(feats14, dtype=np.int8)
    # convert to floating-point features
    return np.hstack([
        sbert_i2b(feats1),  # sbert
        divide_by_1st_col(feats2),  # trankit
        divide_by_1st_col(feats3),  # trankit
        divide_by_sum(feats4),  # trankit
        divide_by_1st_col(feats5),  # consonant
        divide_by_1st_col(feats6),  # char
        divide_by_1st_col(feats7),  # bigram
        divide_by_1st_col(feats8),  # cow
        divide_by_1st_col(feats9),  # smor
        seqlen_i2f(feats12),  # seqlen
        fasttext176_i2f(feats13),   # fasttext176 langdetect
        divide_by_1st_col(feats14)   # emoji
    ])


def i2dict(feats1, feats2, feats3, feats4,
           feats5, feats6, feats7, feats8,
           feats9, feats12, feats13, feats14):
    return {
        "semantic": np.array(feats1, dtype=np.int8),
        "pos": np.array(feats2, dtype=np.int8),
        "morphfeats": np.array(feats3, dtype=np.int8),
        "syntax": np.array(feats4, dtype=np.int8),
        "phonetic": np.array(feats5, dtype=np.int16),
        "charfreq": np.array(feats6, dtype=np.int16),
        "bigramfreq": np.array(feats7, dtype=np.int16),
        "wordfreq": np.array(feats8, dtype=np.int8),
        "morphamb": np.array(feats9, dtype=np.int8),
        "txtlen": np.array(feats12, dtype=np.int16),
        "dialect": np.array(feats13, dtype=np.int8),
        "emoji": np.array(feats14, dtype=np.int8)
    }
