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

fcompose = lambda *args: compose(*args[::-1])

mapdict = lambda **kwargs: map(lambda data: dict(dict((k, f(data)) for k, f in kwargs.items()), **data))

## Helper functions
@curry
def dfassign(df, **kwargs):
    return df.assign(**dict(((k, f(df)) for k, f in kwargs.items())))

## View the images
reshape = lambda arr: arr if len(arr.shape) == 2 else arr[...,0]
to_array = lambda image: reshape(numpy.asarray(image.convert("L")))

def plt_arrays(arrs):
    """Plot a set of (n, n) arrays as row column sub plots.
    """
    fig = matplotlib.pyplot.figure(figsize=(7, 7))
    N = int(numpy.ceil(numpy.sqrt(len(arrs))))
    for i, arr in enumerate(arrs):
        ax = fig.add_subplot(N, N, i + 1)
        out = ax.imshow(arr, cmap='Greys_r', interpolation='none')
        out.axes.get_xaxis().set_visible(False)
        out.axes.get_yaxis().set_visible(False)
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.show()

## Extract the metadata
@curry
def crop_image(image, cutoff=960):
    """Crop the images into the "upper" and "lower" portions.

    Splits the image into the actual image of the microstructure and the embedded metadata.

    Args:
      image: a PIL image
      cutoff: the cutoff height for the upper image

    Returns:
      {'upper' : upper_image, 'lower': lower_image}
    """
    return dict(
               upper=image.crop(box=(0, 0, image.size[0], cutoff)),
               lower=image.crop(box=(0, cutoff, image.size[0], image.size[1]))
           )

def plt_array(arr):
    """Plot a single 2D array
    """
    ax = matplotlib.pyplot.imshow(arr, cmap='Greys_r', interpolation='none')
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.show()

# NBVAL_IGNORE_OUTPUT
repair_string = lambda string: float('10' if string == 'mum' else string.replace('pm', ''))

scale_pixels = fcompose(
    to_array,
    lambda data: skimage.measure.label(data, background=0),
    skimage.measure.regionprops,
    get(1),
    lambda data: data.bbox[3] - data.bbox[1],
)

extract_strings = fcompose(
    lambda image: pytesseract.image_to_string(image),
    lambda string: string.split(),
    get([1, 3, -1]),
    lambda data: dict(scale_microns=repair_string(data[0]),
                      date=data[1].replace('-', ''),
                      time=data[2])
)

extract_metadata = fcompose(
    PIL.Image.open,
    crop_image,
    get('lower'),
    lambda image: dict(scale_pixels=scale_pixels(image), **extract_strings(image))
)

## Rescale the images
extract_image = fcompose(
    PIL.Image.open,
    crop_image,
    get('upper')
)

def scale_image(image, rescale_factor):
    """Scale the image using PIL's thumbnail

    thumbnail is an inplace operation so copies are required.

    Args:
      image: a PIL image
      rescale_factor: how much to rescale the image by

    Returns:
      a new image
    """
    copy_image = image.copy()
    copy_image.thumbnail(numpy.array(copy_image.size) * rescale_factor, PIL.Image.ANTIALIAS)
    return copy_image

get_df = fcompose(
    glob.glob,
    sorted,
    map(
        lambda filename: dict(filename=filename,
                              **extract_metadata(filename))
    ),
    list,
    pandas.DataFrame,
    dfassign(pixel_size=lambda df: df['scale_microns'] / df['scale_pixels']),
    dfassign(rescale_factor=lambda df: df['pixel_size'] / max(df['pixel_size'])),
)

scaled_images = fcompose(
    get_df,
    lambda df: df.T.to_dict().values(),
    mapdict(image=lambda data: extract_image(data['filename'])),
    mapdict(scaled_image=lambda data: scale_image(data['image'], data['rescale_factor'])),
    list
)

## Threshold the images into the ferrite and cementite phase
threshold_image = fcompose(
    PIL.Image.open,
    crop_image,
    get('upper'),
    to_array,
    lambda data: data > skimage.filters.threshold_otsu(data)
)

def threshold(filename):

    result = dict(filename=filename,
                threshold_image=threshold_image(filename),
                **extract_metadata(filename))
    return result

if __name__ == '__main__':
    filename = sys.argv[1]
    filename_cleaned = filename.split("/")[-1].split(".")[0]
    result = threshold(filename)

    pickle.dump(result, open("{0}-threshold.data".format(filename_cleaned), 'wb'))
    
    print "{0}-threshold.data".format(filename_cleaned)