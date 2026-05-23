"""
Jupyter kernel for Mathics3.
"""

import pprint
import re
import subprocess
import sys

from ipykernel.kernelbase import Kernel
from IPython.display import HTML, Javascript, display
from io import StringIO
from mathics import __version__
from mathics.core.load_builtin import import_and_load_builtins
from mathics.session import MathicsSession
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

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
        # Dictionary to store Python variables across %python invocations
        self.python_namespace = {}

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

    def _display_python_input(self, python_code: str) -> None:
        """
        Display the Python input code with syntax highlighting in the input area.
        """
        # Use Pygments to highlight the input code
        formatter = HtmlFormatter(style="default", noclasses=True)
        highlighted = highlight(python_code, PythonLexer(), formatter)

        # Send as display_data to show in the input area
        self.send_response(
            self.iopub_socket,
            "display_data",
            {
                "data": {
                    "text/html": f'<div style="text-align: left; background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 10px;"><strong>Python Input:</strong><div style="margin-top: 5px;">{highlighted}</div></div>',
                    "text/plain": python_code,
                },
                "metadata": {},
            },
        )

    def _format_python_output(self, output_text: str) -> None:
        """
        Format and colorize Python output using Pygments and send to notebook.
        """
        # Use Pygments to highlight the output as Python code
        formatter = HtmlFormatter(style="default", noclasses=True)
        highlighted = highlight(output_text, PythonLexer(), formatter)

        # Send as HTML with syntax highlighting
        self.send_response(
            self.iopub_socket,
            "execute_result",
            {
                "execution_count": self.execution_count,
                "data": {
                    "text/html": f'<div style="text-align: left;">{highlighted}</div>',
                    "text/plain": output_text,
                },
                "metadata": {},
            },
        )

    def _handle_python_magic(self, code: str) -> bool:
        """
        Handle %python magic command. Returns True if handled, False otherwise.
        Supports both single-line expressions and multi-line statements.
        """
        python_match = re.match(r"%python\s+(.*)", code.strip(), re.DOTALL)
        if python_match:
            python_code = python_match.group(1)

            # Display the Python input with syntax highlighting
            self._display_python_input(python_code)

            try:
                # Capture stdout during execution
                old_stdout = sys.stdout
                sys.stdout = StringIO()

                try:
                    # Try to evaluate as an expression first
                    result = eval(
                        python_code,
                        {"__builtins__": __builtins__},
                        self.python_namespace,
                    )
                    output = sys.stdout.getvalue()

                    # If there's captured output, use it; otherwise use the result
                    if output:
                        self.send_response(
                            self.iopub_socket,
                            "stream",
                            {"name": "stdout", "text": output},
                        )
                    elif result is not None:
                        # Use pprint for pretty-printed output
                        formatted_output = pprint.pformat(result)
                        self._format_python_output(formatted_output)
                except SyntaxError:
                    # If eval fails, try exec for multi-line statements
                    output = sys.stdout.getvalue()
                    sys.stdout = StringIO()  # Reset StringIO for exec

                    exec(
                        python_code,
                        {"__builtins__": __builtins__},
                        self.python_namespace,
                    )
                    output += sys.stdout.getvalue()

                    if output:
                        self.send_response(
                            self.iopub_socket,
                            "stream",
                            {"name": "stdout", "text": output},
                        )
                finally:
                    sys.stdout = old_stdout

                return True
            except Exception as e:
                sys.stdout = old_stdout
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
