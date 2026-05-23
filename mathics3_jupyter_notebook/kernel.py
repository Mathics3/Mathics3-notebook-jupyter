"""
Jupyter kernel for Mathics3.
"""

import re
import subprocess
import sys

from ipykernel.kernelbase import Kernel
from IPython.display import HTML, Javascript, display
from mathics import __version__
from mathics.core.load_builtin import import_and_load_builtins
from mathics.session import MathicsSession

from mathics3_jupyter_notebook.formatter import format_output

import_and_load_builtins()


class Mathics3Kernel(Kernel):
    implementation = "Mathics3"
    implementation_version = "1.0"
    language = "mathematica3"
    language_version = "1.0"
    banner = f"Mathics3 {__version__} Kernel ({implementation_version})- A Mathematica-compatible engine"
    help_links = [
        {"text": "Mathics3", "url": "https://mathics.org/"},
        {
            "text": "Mathics3-notebook-jupyter GitHub",
            "url": "https://github.com/Mathics3/Mathics3-notebook-jupyter",
        },
    ]
    language_info = {
        "name": "mathematica",
        "mimetype": "text/x-mathematica",
        "file_extension": ".wl",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Do not store this 'self.session'.
        # ipykernel uses 'self.session' for its own messaging system.
        self.mathics_engine = MathicsSession()

        # Inject custom CSS for left-aligned math output
        display(
            HTML(
                """
                /* related resource: base.css */
                <style>
                /* Left-align MathML output */
                .output_area .output_result {
                    text-align: left !important;
                }

                .output_area .output_result math {
                    display: block !important;
                    margin-left: 0 !important;
                    margin-right: auto !important;
                }
                </style>
                """
            )
        )

        display(
            Javascript(
                """
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = 'https://cdn.jsdelivr.net/npm/@mathicsorg/mathics-threejs-backend';
            document.head.appendChild(script);
            console.log('Loading mathics-threejs-backend');
    """
            )
        )

    def _handle_pip_magic(self, line: str) -> bool:
        """Handle %pip magic command. Returns True if handled, False otherwise."""
        pip_match = re.match(r"%pip\s+(.*)", line.strip())
        if pip_match:
            args = pip_match.group(1)
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip"] + args.split(),
                    capture_output=True,
                    text=True,
                )
                # Send output back to notebook
                if result.stdout:
                    self.send_response(
                        self.iopub_socket,
                        "stream",
                        {"name": "stdout", "text": result.stdout},
                    )
                if result.stderr:
                    self.send_response(
                        self.iopub_socket,
                        "stream",
                        {"name": "stderr", "text": result.stderr},
                    )
                return True
            except Exception as e:
                self.send_response(
                    self.iopub_socket,
                    "stream",
                    {"name": "stderr", "text": f"Error running pip: {str(e)}\n"},
                )
                return True
        return False

    def _handle_python_magic(self, line: str) -> bool:
        """Handle %python magic command. Returns True if handled, False otherwise."""
        python_match = re.match(r"%python\s+(.*)", line.strip())
        if python_match:
            code = python_match.group(1)
            try:
                # Execute the Python code
                result = eval(code)
                # Send output back to notebook
                output_text = str(result)
                self.send_response(
                    self.iopub_socket,
                    "stream",
                    {"name": "stdout", "text": output_text + "\n"},
                )
                return True
            except Exception as e:
                self.send_response(
                    self.iopub_socket,
                    "stream",
                    {
                        "name": "stderr",
                        "text": f"Error running Python: {type(e).__name__}: {str(e)}\n",
                    },
                )
                return True
        return False

    def do_execute(
        self,
        code: str,
        silent,
        store_history=True,
        user_expressions=None,
        allow_stdin=True,
    ):
        """
        This method is hooked in by the IPKernelApp.launch_instance(kernel_class=Mathics3Kernel) call from __main__.py.

        It evaluates `code` as a Mathics3 expression and sends the output back to Jupyter
        """
        if not store_history:
            # Something somewhere else is incrementing execution count.
            # So we subtract 1, here if we don't want the cell number
            # to increment.
            self.execution_count -= 1

        if not code.strip():
            return {
                "status": "ok",
                "execution_count": self.execution_count,
                "payload": [],
                "user_expressions": {},
            }

        # Handle magic commands
        if self._handle_pip_magic(code):
            return {
                "status": "ok",
                "execution_count": self.execution_count,
                "payload": [],
                "user_expressions": {},
            }

        if self._handle_python_magic(code):
            return {
                "status": "ok",
                "execution_count": self.execution_count,
                "payload": [],
                "user_expressions": {},
            }

        if not silent:
            try:
                # Evaluate the input code using the Mathics3 engine
                # Mathics3 returns an object that we can convert to a string

                expr = self.mathics_engine.evaluate(code)
                evaluation = self.mathics_engine.evaluation
                content = format_output(evaluation, expr, self.execution_count)
                # Send the result back to the Jupyter frontend
                self.send_response(self.iopub_socket, "execute_result", content)

            except Exception as e:
                return {
                    "status": "error",
                    "ename": type(e).__name__,
                    "evalue": str(e),
                    "traceback": [],
                }

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=Mathics3Kernel)
