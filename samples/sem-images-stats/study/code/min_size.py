import glob
import numpy
import matplotlib.pyplot
import scipy.ndimage
import pytesseract
import PIL.Image
from toolz.curried import map, pipe, compose, get, do, curry, count, pluck, juxt, flip
import pandas
import skimage
import skimage.measure
import skimage.filters
import skimage.morphology

import sys
import json
import pickle

## Remove white specs
def f_min_size(scale_microns, scale_pixels, island_size=0.2):
    return (island_size * scale_pixels / scale_microns)**2

def min_size(data):
    data['min_size'] = f_min_size(data['scale_microns'], data['scale_pixels'])
    return data

if __name__ == '__main__':
    filename = sys.argv[1]
    filename_cleaned = filename.split("/")[-1].split(".")[0]
    filename_cleaned = "-".join(filename_cleaned.split("-")[0:-1])

    data = None
    with open(filename, "r") as intermediate:
        data = pickle.load(intermediate)

    result = min_size(data)
    pickle.dump(result, open("{0}-min_size.data".format(filename_cleaned), 'wb'))

    print "{0}-min_size.data".format(filename_cleaned)