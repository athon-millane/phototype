#!/bin/bash

source deactivate
conda env remove -n engg3800g04
conda env create -f env.yml
source activate engg3800g04
jupyter labextension install jupyterlab-jupytext
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter lab
