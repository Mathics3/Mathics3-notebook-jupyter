.PHONY: all notebook lab

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
	jupyter notebook

#: Register a mathics3 Jupyter kernel
register-kernel:
	$(PYTHON3) -m mathics3_jupyter_notebook.install
