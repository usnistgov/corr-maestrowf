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

import json
import sys
import pickle

## Binary closing to reveal the Pearlite Phase
remove_small_holes = curry(skimage.morphology.remove_small_holes)

def clean(data):
    data['clean_image'] = ~remove_small_holes(~data['threshold_image'], data['min_size'])
    return data

if __name__ == '__main__':
    filename = sys.argv[1]
    filename_cleaned = filename.split("/")[-1].split(".")[0]
    filename_cleaned = "-".join(filename_cleaned.split("-")[0:-1])
    
    data = None
    with open(filename, "r") as intermediate:
        data = pickle.load(intermediate)

    result = clean(data)
    pickle.dump(result, open("{0}-clean.data".format(filename_cleaned), 'wb'))


    print "{0}-clean.data".format(filename_cleaned)