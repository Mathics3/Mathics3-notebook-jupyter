# Mathics3 Jupyter notebook

This provides a kernel for Mathics3 inside Jupyter.

## Using

After a Mathics3 Jupyter kernel is loaded, you can enter Mathics3 command and you will
get the results evaluated and displayed.

There are two "magic" commands available, `%pip` and `%python`.

### `%pip`

The `%pip` command allows you run Python "pip" commands to see or install what Python packages.


### `%python`

The `%python` command allows you to run Python statements or evaluate python expressions, rather than Mathics3 expressions or statements.

## Building

Install all of the prerequisites:

```console
$ pip install -e .
```

Register the Mathics3 kernel for Jupyter vai via JSON file `mathics3-jupyter/kernel.json`.

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
$ jupyter lab  # or:  make lab
```

## Debugging

Install `jupyter-console` and run `jupyter console` via `make`:

```console
$ make console
jupyter console --kernel=mathics3-jupyter
Jupyter console 6.6.3

Mathics3 10.0.2dev0 Kernel (1.0)- A Mathematica-compatible engine
...
```
