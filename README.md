# GGG Python Measurement Code

Experimental measurement code written for use in the Quantum Dots project in the Goldhaber-Gordon lab at Stanford, 
but general enough for anyone to use. 
Some of the features are dynamic updating of plots and an automatic saving of data with full information about the state of all instruments. 
The most unique feature compared to other Python code is background measurement/plotting. 
The plotting backend used is Holoviews. For instrument drivers, the easiest way is to take advantage of QCoDeS drivers, 
but it is not too difficult to write one.

## Installing
Open conda terminal.

Using the environment file provided (.yml) run 
```
conda env create -f gggmeas.yml
```

Change to this environment using 
```
conda activate gggmeas
```
(Can also change the name by opening gggmeas.yml in a text editor and editing the first name line)

Jupyter notebook should be a little easier regarding extensions, but have only tested jupyter lab. 

Then use either `jupyter notebook` or `jupyter lab` to start.

### Jupyter Lab Specific Extensions

May have to install nb_conda_kernels via
```
conda install nb_conda_kernels
```
if jupyter lab only sees base environment 
(one indication is that it can’t find modules that are only installed in this environment but not the base one)

Install extension allowing for javascript output used by Holoviews
```
jupyter labextension install @pyviz/jupyterlab_pyviz
```
If you get a nodejs or npm error, try `conda install -c conda-forge nodejs`
		
For linecuts run 
```
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

## Examples
See [Demo.ipynb](https://github.com/dgglab/QDotsPythonCode/blob/master/Demo.ipynb) for a demo of examples.

Note that the actual plots themselves and thumbnails that are saved will probably not display properly.
