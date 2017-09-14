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

fcompose = lambda *args: compose(*args[::-1])

## Binary closing to reveal the Pearlite Phase
closing = curry(flip(skimage.morphology.closing))
remove_small_holes = curry(skimage.morphology.remove_small_holes)

reveal_pearlite = fcompose(
    closing(skimage.morphology.square(5)),
    remove_small_holes(min_size=1000)
)

def reveal(data):
    data['pearlite_image'] = reveal_pearlite(data['clean_image'])
    return data

if __name__ == '__main__':
    filename = sys.argv[1]
    filename_cleaned = filename.split("/")[-1].split(".")[0]
    filename_cleaned = "-".join(filename_cleaned.split("-")[0:-1])

    data = None
    with open(filename, "r") as intermediate:
        data = pickle.load(intermediate)

    result = reveal(data)
    pickle.dump(result, open("{0}-reveal.data".format(filename_cleaned), 'wb'))

    print "{0}-reveal.data".format(filename_cleaned)