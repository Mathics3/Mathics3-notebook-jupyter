.PHONY: all generate-config notebook lab register-kernel

PYTHON3 ?= python3

all: notebook

#: Run Jupyter console for debugging problems
console:
	jupyter console --kernel=mathics3-jupyter

#: Run Jupyter lab with this Jupyter kernel
lab:
	jupyter lab


#: Run Jupyter notebook with this Jupyter kernel
notebook:
	jupyter notebook --notebook-dir=$(HOME)/Jupyter-notebooks

#: Register a mathics3 Jupyter kernel
register-kernel:
	$(PYTHON3) -m mathics3_jupyter_notebook.install

#: Gerate a Jupyter config to note where Jupyter notebooks should be saved
generate-config:
	jupyter server --generate-config
