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

import dask
import json
from dask.multiprocessing import get as dak_get

from dask.diagnostics import ResourceProfiler, Profiler, CacheProfiler, ProgressBar, visualize
from dask import compute
from dask.dot import dot_graph


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

# _ = pipe(
#     'data/*.tif',
#     glob.glob,
#     sorted,
#     map(PIL.Image.open),
#     map(to_array),
#     list,
#     plt_arrays
# )

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

# _ = pipe(
#     'data/*.tif',
#     glob.glob,
#     sorted,
#     map(PIL.Image.open),
#     map(crop_image),
#     pluck('lower'),
#     map(to_array),
#     map(
#         do(
#             plt_array
#         )
#     ),
#     list
# )

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

# print(pipe(
#     'data/*.tif',
#     glob.glob,
#     sorted,
#     map(
#         lambda filename: dict(filename=filename, **extract_metadata(filename))
#     ),
#     list,
#     pandas.DataFrame
# ))

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

# _ = pipe(
#     'data/*.tif',
#     scaled_images,
#     pluck('scaled_image'),
#     map(to_array),
#     list,
#     plt_arrays
# )

## Threshold the images into the ferrite and cementite phase
threshold_image = fcompose(
    PIL.Image.open,
    crop_image,
    get('upper'),
    to_array,
    lambda data: data > skimage.filters.threshold_otsu(data)
)

# _ = pipe('data/*.tif',
#      glob.glob,
#      sorted,
#      map(threshold_image),
#      list,
#      plt_arrays
# )

## Remove white specs
def f_min_size(scale_microns, scale_pixels, island_size=0.2):
    return (island_size * scale_pixels / scale_microns)**2

# _ = pipe('data/*.tif',
#     glob.glob,
#     sorted,
#     map(
#         lambda filename: dict(image=threshold_image(filename),
#                               **extract_metadata(filename))
#     ),
#     mapdict(min_size=lambda d: f_min_size(d['scale_microns'], d['scale_pixels'])),
#     map(
#         lambda d: ~skimage.morphology.remove_small_holes(~d['image'],
#                                                           d['min_size'])
#     ),
#     list,
#     plt_arrays
# )

## Binary closing to reveal the Pearlite Phase
closing = curry(flip(skimage.morphology.closing))
remove_small_holes = curry(skimage.morphology.remove_small_holes)

reveal_pearlite = fcompose(
    closing(skimage.morphology.square(5)),
    remove_small_holes(min_size=1000)
)

# _ = pipe('data/*.tif',
#     glob.glob,
#     sorted,
#     map(
#         lambda filename: dict(image=threshold_image(filename),
#                               **extract_metadata(filename))
#     ),
#     mapdict(min_size=lambda d: f_min_size(d['scale_microns'], d['scale_pixels'])),
#     map(
#         lambda d: ~remove_small_holes(~d['image'], d['min_size'])
#     ),
#     map(reveal_pearlite),
#     list,
#     plt_arrays
# )

## Volume function
frac1 = lambda image: float(image.sum()) / image.size
frac0 = lambda image: 1 - frac1(image)

# print(pipe('data/*.tif',
#     glob.glob,
#     sorted,
#     map(
#         lambda filename: dict(filename=filename,
#                               threshold_image=threshold_image(filename),
#                               **extract_metadata(filename))
#     ),
#     mapdict(
#         min_size=lambda d: f_min_size(d['scale_microns'], d['scale_pixels'])),
#     mapdict(
#         clean_image=lambda d: ~remove_small_holes(~d['threshold_image'], d['min_size'])
#     ),
#     mapdict(
#         pearlite_image=lambda d: reveal_pearlite(d['clean_image'])
#     ),
#     mapdict(
#         pearlite_fraction=lambda data: frac1(data['pearlite_image']),
#         ferrite_fraction=lambda data: frac0(data['clean_image']),
#         cemmentite_fraction=lambda data: frac1(data['clean_image'])
#     ),
#     list,
#     pandas.DataFrame
# )[['filename', 'pearlite_fraction', 'ferrite_fraction', 'cemmentite_fraction']])

def threshold(filename):

    result = dict(filename=filename,
                threshold_image=threshold_image(filename),
                **extract_metadata(filename))
    return result

def min_size(data):
    data['min_size'] = f_min_size(data['scale_microns'], data['scale_pixels'])
    return data

def clean(data):
    data['clean_image'] = ~remove_small_holes(~data['threshold_image'], data['min_size'])
    # print(data['clean_image'])
    return data

def reveal(data):
    data['pearlite_image'] = reveal_pearlite(data['clean_image'])
    # print(data['pearlite_image'])
    return data

def pearlite(data):
    data['pearlite_fraction'] = frac1(data['pearlite_image'])
    return data

def ferrite(data):
    data['ferrite_fraction'] = frac0(data['clean_image'])
    return data

def cemmentite(data):
    data['cemmentite_fraction'] = frac1(data['clean_image'])
    return data

def save(data):
    clean_name = data['filename'].split("/")[-1].split(".")[0]
    file_path = "Data/{0}.json".format(clean_name)
    filtered_data = {}
    filtered_data['filename'] = clean_name
    filtered_data['pearlite_fraction'] = data['pearlite_fraction']
    filtered_data['ferrite_fraction'] = data['ferrite_fraction']
    filtered_data['cemmentite_fraction'] = data['cemmentite_fraction']
    with open(file_path, "w") as save_file:
        save_file.write(json.dumps(filtered_data, sort_keys=True, indent=4, separators=(',', ': ')))

def finalize(saves):
    print("done.")

dsk = {}
files = sorted(glob.glob("data/*.tif"))
final_saves = []
for filename in files:
    print(filename)
    filename_cleaned = filename.split("/")[-1].split(".")[0]
    dsk['threshold-{0}'.format(filename_cleaned)] = (threshold, filename)
    dsk['min_size-{0}'.format(filename_cleaned)] = (min_size, 'threshold-{0}'.format(filename_cleaned))
    dsk['clean-{0}'.format(filename_cleaned)] = (clean, 'min_size-{0}'.format(filename_cleaned))
    dsk['reveal-{0}'.format(filename_cleaned)] = (reveal, 'clean-{0}'.format(filename_cleaned))
    dsk['pearlite-{0}'.format(filename_cleaned)] = (pearlite, 'reveal-{0}'.format(filename_cleaned))
    dsk['ferrite-{0}'.format(filename_cleaned)] = (ferrite, 'pearlite-{0}'.format(filename_cleaned))
    dsk['cemmentite-{0}'.format(filename_cleaned)] = (cemmentite, 'ferrite-{0}'.format(filename_cleaned))
    dsk['save-{0}'.format(filename_cleaned)] = (save, 'cemmentite-{0}'.format(filename_cleaned))
    final_saves.append('save-{0}'.format(filename_cleaned))
dsk['finalize'] = (finalize, final_saves)

dot_graph(dsk)

with ResourceProfiler(0.25) as rprof, Profiler() as prof, CacheProfiler() as cprof, ProgressBar():
    dak_get(dsk, 'finalize')

visualize([prof, rprof, cprof])
