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

def save(data):
    clean_name = data['filename'].split("/")[-1].split(".")[0]
    file_path = "{0}.json".format(clean_name)
    filtered_data = {}
    filtered_data['filename'] = clean_name
    filtered_data['pearlite_fraction'] = data['pearlite_fraction']
    filtered_data['ferrite_fraction'] = data['ferrite_fraction']
    filtered_data['cemmentite_fraction'] = data['cemmentite_fraction']
    with open(file_path, "w") as save_file:
        save_file.write(json.dumps(filtered_data, sort_keys=True, indent=4, separators=(',', ': ')))

if __name__ == '__main__':
    filename = sys.argv[1]
    filename_cleaned = filename.split("/")[-1].split(".")[0]
    filename_cleaned = "-".join(filename_cleaned.split("-")[0:-1])

    data = None
    with open(filename, "r") as intermediate:
        data = pickle.load(intermediate)

    result = save(data)