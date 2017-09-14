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

## Volume function
frac1 = lambda image: float(image.sum()) / image.size
frac0 = lambda image: 1 - frac1(image)

def ferrite(data):
    data['ferrite_fraction'] = frac0(data['clean_image'])
    return data

if __name__ == '__main__':
    filename = sys.argv[1]
    filename_cleaned = filename.split("/")[-1].split(".")[0]
    filename_cleaned = "-".join(filename_cleaned.split("-")[0:-1])
    
    data = None
    with open(filename, "r") as intermediate:
        data = pickle.load(intermediate)

    result = ferrite(data)
    pickle.dump(result, open("{0}-ferrite.data".format(filename_cleaned), 'wb'))


    print "{0}-ferrite.data".format(filename_cleaned)