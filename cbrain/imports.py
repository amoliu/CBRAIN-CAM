"""
Just all the imports for all other scripts and notebooks.
"""


import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import pandas as pd
import pickle
import pdb
import netCDF4 as nc
import xarray as xr
import h5py
from glob import glob
import sys, os
from os import path
from configargparse import ArgParser
import fire
import logging
from ipykernel.kernelapp import IPKernelApp
def in_notebook():
    return IPKernelApp.initialized()

if in_notebook():
    from tqdm import tqdm_notebook as tqdm
else:
    from tqdm import tqdm


def tf():
    import keras
    #from keras.callbacks import *
    import tensorflow as tf



# with open(os.path.join(os.path.dirname(__file__), 'hyai_hybi.pkl'), 'rb') as f:
#     hyai, hybi = pickle.load(f)