#!/bin/env python3
"""
A Command-line program to install the Mathics3 Jupyter Kernel
and example Mathics3 Jupyter Notebook files.

"""
import argparse
import json
import os
import os.path as osp
import shutil
import sys
from tempfile import TemporaryDirectory
from typing import Any, Dict, Final, Optional

from jupyter_client.kernelspec import KernelSpecManager

# Location of Notebook files
DEFAULT_NOTEBOOK_HOME: Final[str] = os.path.join(
    os.environ.get("HOME", os.path.expanduser("~")), "Jupyter-notebooks"
)

# Name that appears inside Jupyter showing what kernel is running
DISPLAY_NAME: Final[str] = "Mathics3 Kernel (Wolfram Language)"

# The source directory for icons relative to the project root
ICON_SOURCE_DIR: Final[str] = osp.normpath(
    osp.join(osp.dirname(__file__), "..", "static")
)

# The contents of our kernel.json file
KERNEL_JSON: Final[Dict[str, Any]] = {
    "argv": [
        sys.executable,
        "-m",
        "mathics3_jupyter_kernel.kernel",  # The module that handles the kernel loop
        "-f",
        "{connection_file}",
    ],
    "display_name": DISPLAY_NAME,
    "language": "wolfram",
    "metadata": {
        "language_info": {
            "name": "wolfram",
            "codemirror_mode": "gfm",
            "file_extension": ".wl",
            "mimetype": "text/x-wolfram",
        },
    },
}

KERNEL_NAME: Final[str] = "Mathics3-Kernel"

# The source directory for icons relative to the project root
NOTEBOOK_SOURCE_DIR: Final[str] = osp.normpath(
    osp.join(osp.dirname(__file__), "..", "examples")
)


def install_my_kernel_spec(user=True, prefix=None, notebook_home: Optional[str] = None):
    """
    Creates a JSON 'kernel.json' file custom for the Mathics3 Jupyter kernel of
    this project.
    """
    with TemporaryDirectory(prefix="kernel-", suffix=".json") as target_dir:
        # Create the kernel directory inside a temp folder, and
        # ensure Jupyter can read the directory.
        os.chmod(target_dir, 0o755)

        # Write the file "kernel.json".
        with open(os.path.join(target_dir, "kernel.json"), "w") as f:
            json.dump(KERNEL_JSON, f, sort_keys=True, indent=4)

        # Jupyter specifically looks for logo-32x32.png and logo-64x64.png
        icon_found = False
        if osp.isdir(ICON_SOURCE_DIR):
            for icon_name in ["logo-32x32.png", "logo-64x64.png"]:
                src_path = osp.normpath(osp.join(ICON_SOURCE_DIR, icon_name))
                if osp.exists(src_path):
                    print(f"Found icon: {icon_name}, adding to kernelspec...")
                    shutil.copy(src_path, target_dir)
                    icon_found = True

        if not icon_found:
            print(
                f"Warning: No icons found in {ICON_SOURCE_DIR}/. Kernel will install without a logo."
            )

        print(f"Installing Jupyter kernel spec for {DISPLAY_NAME}...")
        try:
            destination_path = KernelSpecManager().install_kernel_spec(
                target_dir, KERNEL_NAME, user=user, prefix=prefix
            )
        except Exception as e:
            print(f"Failed to install kernel: {e}")
        else:
            print(f"Successfully installed Mathics3 kernel in {destination_path}")
            if notebook_home is not None:
                # Create target directory if it doesn't exist
                os.makedirs(notebook_home, exist_ok=True)

                if osp.isdir(notebook_home):
                    print("Copying sample notebooks...")

                    for notebook_file in os.listdir(NOTEBOOK_SOURCE_DIR):
                        if notebook_file.endswith(".ipynb"):
                            source_path = os.path.join(
                                NOTEBOOK_SOURCE_DIR, notebook_file
                            )
                            target_path = os.path.join(
                                DEFAULT_NOTEBOOK_HOME, notebook_file
                            )
                            print(
                                f"Copying notebook: {target_path}, adding to {DEFAULT_NOTEBOOK_HOME}..."
                            )
                            shutil.copy2(source_path, target_path)


def _is_root():
    try:
        return os.getuid() == 0
    except AttributeError:
        return False  # Windows


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=f"Install the {DISPLAY_NAME} kernel spec for Jupyter."
    )
    parser.add_argument(
        "--user",
        action="store_true",
        help="Install to the per-user kernelspec directory",
    )
    parser.add_argument(
        "--sys-prefix",
        action="store_true",
        help="Install to Python's sys.prefix (e.g. venv)",
    )
    parser.add_argument("--prefix", help="Install to the given prefix")

    parser.add_argument(
        "--no-examples",
        action="store_true",
        help="Do not install example notebooks",
    )
    parser.add_argument(
        "--notebook-home",
        type=str,
        default=DEFAULT_NOTEBOOK_HOME,
        help=f"Path string to copy example Jupyter notebook files (default: {DEFAULT_NOTEBOOK_HOME})",
    )

    args = parser.parse_args(argv)

    if args.sys_prefix:
        args.prefix = sys.prefix
    if not args.prefix and not args.user and _is_root():
        args.user = False

    notebook_home = None if args.no_examples else args.notebook_home
    install_my_kernel_spec(
        user=args.user or True, prefix=args.prefix, notebook_home=notebook_home
    )
    print("Installation complete.")


if __name__ == "__main__":
    main()
