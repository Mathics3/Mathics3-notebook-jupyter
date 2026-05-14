.PHONY: all generate-config notebook lab register-kernel

PYTHON3 ?= python3
GIT2CL ?= admin-tools/git2cl


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

#: Make distirbution: wheels and tarball
dist:
	./admin-tools/make-dist.sh

#: Remove ChangeLog
rmChangeLog:
	$(RM) ChangeLog || true

#: Create ChangeLog from version control without corrections
ChangeLog-without-corrections:
	git log --pretty --numstat --summary | $(GIT2CL) >ChangeLog

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog ChangeLog-without-corrections
	patch ChangeLog < ChangeLog-spell-corrected.diff
