"""
Installs a Mathics3 kernel for use inside Jupyter.
"""

import argparse
import json
import os
import sys
from tempfile import TemporaryDirectory

from jupyter_client.kernelspec import KernelSpecManager


def install_mathics3_kernel(user=True, prefix=None):
    """
    Registers the Mathics3 kernel with Jupyter.
    """
    kernel_json = {
        "argv": [
            sys.executable,
            "-m",
            "mathics3_jupyter_notebook.kernel",  # The module that handles the kernel loop
            "-f",
            "{connection_file}",
        ],
        "display_name": "Mathics3-jupyter",
        "language": "mathematica",
    }

    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Ensure Jupyter can read the directory
        with open(os.path.join(td, "kernel.json"), "w") as f:
            json.dump(kernel_json, f, sort_keys=True, indent=4)

        print("Installing Jupyter kernel spec for Mathics3...")
        try:
            KernelSpecManager().install_kernel_spec(
                td, "mathics3-jupyter", user=user, prefix=prefix
            )
            print(
                "Successfully installed Mathics3 kernel in mathics3-jupyter/kernel.json"
            )
        except Exception as e:
            print(f"Failed to install kernel: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install Mathics3 Kernel")
    parser.add_argument("--user", action="store_true", help="Install to user directory")
    parser.add_argument("--prefix", help="Install to a specific prefix")

    args = parser.parse_args()

    # Default to user install if not specified
    install_mathics3_kernel(user=args.user or True, prefix=args.prefix)
