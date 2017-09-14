<h1> <p align="center"><sup><strong>
Analysis of SEM Images of Steel
</strong></sup></p>
</h1>

<p align="center">
<a href="https://travis-ci.org/wd15/sem-image-stats" target="_blank">
<img src="https://api.travis-ci.org/wd15/sem-image-stats.svg" alt="Travis CI">
</a>
<a href="https://github.com/wd15/sem-images-stats/blob/master/LICENSE.md" target="_blank">
<img src="https://img.shields.io/badge/license-mit-blue.svg" alt="License">
</a>
</p>

### Overview

The goal of this work is to analyze images of steel from SEM. The initial data set consists of 9 images. The first step in the work (comprising this notebook) is to categorize the microstructure in each image. A number of analysis steps are required including

 - cropping the images,
 - extracting meta-data embedded in the images,
 - thresholding the images to increase contrast,
 - classifying the pixels in the image as a given phase,
 - classifying the inter lammelar spacing in one of the phases,
 - obtaining statistics about the microstructure such as the volume fraction, spacing and shape.

### Toolz

This analysis uses [Toolz](http://toolz.readthedocs.io/en/latest/) to explore the use of functional programming for data pipelines in Python. It seems to make the code a lot cleaner with less intermediate variables, which seems to be an advantage especially when evaluating cells in the notebook. Overall, it is currently unclear how much of benefit this approach provides. It does seem to obfuscate some of the code for non-functional programmers. Hopefully, it will help with parallel processing of the data pipelines using Dask in the future.

### Execution with Dask

We provide a notebook [index.ipynb](./index.ipynb) that runs the study with dask. The execution graph can be find in this repository [Graph](./mydask.png).

### Execution with Maestrowf

Before executing we recommend installing the required libraries by doing:
    
    $ pip install -r requirements.txt

To run the study with Maestrowf we have written the Dask workflow into a Maestrowf [Spec](./sem-study.yaml).
The execution steps is described in [maestrowf.ipynb](./maestrowf.ipynb).

### Archiving with Maestrowf

To push the record into CoRR run:

	$ archive -f corr_config_file_path/config.json maestrowf_record_spec_path/spec.yaml -d 1

This should produce a CoRR record/project+record in the user dashboard.

### Notebook

The main notebook is [index.ipynb](./index.ipynb).