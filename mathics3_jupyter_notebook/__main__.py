import sys
from ipykernel.kernelapp import IPKernelApp

# Ensure the package is available on the path
# This allows us to import the kernel class from the current package
try:
    from mathics3_jupyter_notebook.kernel import Mathics3Kernel
except ImportError:
    # Fallback in case the internal structure differs or names are slightly off
    # You may need to adjust this import to match your specific filename (e.g., .kernel_class)
    print("Error: Could not find Mathics3Kernel in mathics3_jupyter_notebook.kernel", file=sys.stderr)
    sys.exit(1)

def main():
    """
    Standard entry point for the Jupyter kernel.
    This initializes the ZeroMQ sockets and starts the event loop.
    """
    # IPKernelApp is the standard launcher provided by ipykernel
    # We pass our custom class so it knows how to handle Mathics3 expressions
    IPKernelApp.launch_instance(kernel_class=Mathics3Kernel)

if __name__ == '__main__':
    main()
