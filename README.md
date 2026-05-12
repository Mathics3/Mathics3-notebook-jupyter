# Mathics3 Jupyter notebook

This library provides helper functions for integrating Mathics3 into notebook environments.
Currently, it supports Jupyter(Lite), marimo, and Observable.

## Building

Install all of the prerequisites:

```console
$ pip install -e .
```

Register the Mathics3 kernel into Jupyter.

```console
$ python3 -m mathics3_jupyter_notebook.install
```

This needs to be done only once.

To see that this has been installed run:

```console
$ jupyter kernelspec list
```


```
%load_ext mathics3_kernel.frontend.jupyter
```

Usage is as simple as executing the above code in a notebook cell,
and then Mathics3 code can be directly run in all subsequent cells.
Here is a [sample notebook](examples/jupyter-notebook.ipynb)
that can be used with a local Jupyter installation.

## Running

```console
$ jupyter lab
```
