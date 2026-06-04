"""
Jupyter kernel for Mathics3.
"""

import ast
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

from mathics3_jupyter_kernel.formatter import format_output

import_and_load_builtins()


class Mathics3Kernel(Kernel):
    implementation = "Mathics3"
    implementation_version = "1.0"
    language = "mathematica"
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
        self.mathics3_engine = MathicsSession()

        # Dictionary to store Python variables across %python invocations
        self.python_namespace = {}
        self.html_formatter = HtmlFormatter(style="default", noclasses=True)

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
            console.log('Loading mathics-threejs-backend');
            script.type = 'text/javascript';
            script.src = 'https://cdn.jsdelivr.net/npm/@mathicsorg/mathics-threejs-backend';
            document.head.appendChild(script);
            console.log("Initializing Mathics3 Python Dropdown Extension...");

            function setupPythonDropdown() {
                // Target the classic Jupyter Notebook cell-type dropdown
                var cell_type_select = document.querySelector("#cell_type") || document.querySelector(".cell-type-select select");
                if (!cell_type_select) {
                    // If UI hasn't fully rendered yet, retry shortly
                    setTimeout(setupPythonDropdown, 1000);
                    return;
                }

                // Check if "Python" option already exists to prevent duplicate insertion
                var exists = Array.from(cell_type_select.options).some(opt => opt.value === 'python');
                if (!exists) {
                    var pythonOption = document.createElement("option");
                    pythonOption.value = "python";
                    pythonOption.text = "Python";
                    cell_type_select.add(pythonOption);
                }

                // Intercept dropdown selection changes
                cell_type_select.addEventListener("change", function(e) {
                    if (this.value === "python") {
                        var cell = Jupyter.notebook.get_selected_cell();

                        # Convert to standard code cell under the hood so Jupyter doesn't crash
                        cell.change_to_code();

                        # Set a custom metadata flag so the UI remembers this is a Python cell
                        cell.metadata.custom_lang = "python";

                        # Change visual styling or add a watermark placeholder if desired
                        if (!cell.get_text().startsWith("%python")) {
                            cell.set_text("%python\\n" + cell.get_text());
                        }
                    }
                });

                // Listen for cell execution events to clean up or auto-inject %python ahead of transmission
                if (window.Jupyter && Jupyter.notebook) {
                    Jupyter.notebook.events.on('execute.Cell', function(evt, data) {
                        var cell = data.cell;
                        if (cell.metadata.custom_lang === "python") {
                            var text = cell.get_text();
                            if (!text.startsWith("%python")) {
                                cell.set_text("%python\\n" + text);
                            }
                        }
                    });
                }
            }

            // Run setup once DOM and Jupyter objects are fully active
            if (document.readyState === "complete") {
                setupPythonDropdown();
            } else {
                window.addEventListener("load", setupPythonDropdown);
            }
            """
            )
        )

    def _display_python_input(self, python_code: str) -> None:
        """
        Display the Python input code with syntax highlighting in the input area.
        """
        # Use Pygments to highlight the input code
        highlighted = highlight(python_code, PythonLexer(), self.html_formatter)

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
        highlighted = highlight(output_text, PythonLexer(), self.html_formatter)

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

    def _handle_html_cell_magic(self, code: str) -> bool:
        """Handle %html magic command. Returns True if handled, False otherwise."""
        html_match = re.match(r"%html\s+(.*)", code.strip(), re.DOTALL)
        if html_match:
            html_content = html_match.group(1)
            try:
                # Send Markdown content as display_data
                self.send_response(
                    self.iopub_socket,
                    "display_data",
                    {
                        "data": {
                            "text/html": html_content,
                            "text/plain": code,
                        },
                        "metadata": {},
                    },
                )
                return True
            except Exception as e:
                self.send_response(
                    self.iopub_socket,
                    "stream",
                    {
                        "name": "stderr",
                        "text": f"Error rendering HTML: {type(e).__name__}: {str(e)}\n",
                    },
                )
                return True
        return False

    def _handle_pip_cell_magic(self, line: str) -> bool:
        """Handle %pip magic command. Returns True if handled, False otherwise.

        Usage:
            %pip install package_name
            %pip list
            %pip show package_name
        """
        success = False
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
                success = True
            except Exception as e:
                self.send_response(
                    self.iopub_socket,
                    "stream",
                    {"name": "stderr", "text": f"Error running pip: {str(e)}\n"},
                )
                success = True
        return success

    def _handle_python_magic(self, code: str) -> bool:
        """
        Handle %python or %py magic command. Returns True if handled, False otherwise.
        Supports both single-line expressions and multi-line statements.
        """
        python_match = re.match(r"%py(?:thon)?\s+(.*)", code.strip(), re.DOTALL)
        success = False

        if python_match:
            python_code = python_match.group(1)

            # Display the Python input with syntax highlighting
            self._display_python_input(python_code)

            old_stdout = sys.stdout
            result = None
            try:
                # Capture stdout during execution
                sys.stdout = StringIO()

                # Parse the python_code into an Abstract Syntax Tree (AST)
                parsed_ast = ast.parse(python_code)
                globals_dict = {
                    "__builtins__": __builtins__,
                    "session": self.mathics3_engine,
                }

                if not parsed_ast.body:
                    # Compiling and evaluating will probably fail,
                    # but we'll try it anyway.
                    eval_mode = "exec"
                    pseudo_filename = "<mathics-python-exec>"
                    eval_ast = parsed_ast

                else:

                    # Check if the last statement in the block is an expression.
                    last_node = parsed_ast.body[-1]

                    if isinstance(last_node, ast.Expr):
                        # Separate the previous statements from the final expression.
                        statements = parsed_ast.body[:-1]
                        expression = last_node.value

                        # Execute all statements preceding the final expression.
                        if statements:
                            exec_ast = ast.Module(body=statements, type_ignores=[])
                            exec(
                                compile(
                                    exec_ast,
                                    filename="<magic-python-exec>",
                                    mode="exec",
                                ),
                                globals_dict,
                                self.python_namespace,
                            )

                        # Evaluate the final expression and return its value.
                        eval_ast = ast.Expression(body=expression)
                        eval_mode = "eval"
                        pseudo_filename = "<magics-python-eval-last>"
                    else:
                        # If the last statement isn't an expression,
                        # execute everything as statements.
                        eval_ast = parsed_ast
                        eval_mode = "exec"
                        pseudo_filename = "<mathics-python-exec>"

                result = eval(
                    compile(eval_ast, filename=pseudo_filename, mode=eval_mode),
                    globals_dict,
                    self.python_namespace,
                )

                output = sys.stdout.getvalue()
                if output:
                    self.send_response(
                        self.iopub_socket,
                        "stream",
                        {"name": "stdout", "text": output},
                    )
                success = True

            except Exception as e:
                sys.stdout = old_stdout
                self.send_response(
                    self.iopub_socket,
                    "stream",
                    {
                        "name": "stderr",
                        "text": f"Error execution Python magic: {type(e).__name__}: {str(e)}\n",
                    },
                )
                return True

            finally:
                sys.stdout = old_stdout

                if result is not None:
                    # Use pprint for pretty-printed output
                    formatted_output = pprint.pformat(result)
                    self._format_python_output(formatted_output)
                success = True

        return success

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

        # Handle cell magic commands
        if self._handle_pip_cell_magic(code):
            return {
                "status": "ok",
                "execution_count": self.execution_count,
                "payload": [],
                "user_expressions": {},
            }

        if self._handle_html_cell_magic(code):
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

                expr = self.mathics3_engine.evaluate(code)
                print(f"XXX mathics3_engine.evaluate({code}) = {expr})")
                evaluation = self.mathics3_engine.evaluation
                evaluation.definitions.set_line_no(self.execution_count + 1)
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

    def evaluate_expression(self, expr_str: str):
        expr = self.mathics3_engine.evaluate(expr_str)
        evaluation = self.mathics3_engine.evaluation
        return format_output(evaluation, expr, self.execution_count)


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=Mathics3Kernel)
