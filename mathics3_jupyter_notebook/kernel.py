from ipykernel.kernelbase import Kernel
from IPython.display import Javascript, display
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
        if not silent:
            try:
                # Evaluate the input code using the Mathics3 engine
                # Mathics3 returns an object that we can convert to a string

                expr = self.mathics_engine.evaluate(code)
                # # Send the result back to the Jupyter frontend
                # output = str(expr)
                # stream_content = {"name": "stdout", "text": output}
                # self.send_response(self.iopub_socket, "stream", stream_content)

                evaluation = self.mathics_engine.evaluation
                content = format_output(evaluation, expr, self.execution_count)
                # Send the result back to the Jupyter frontend
                self.send_response(self.iopub_socket, "execute_result", content)

            except Exception as e:
                # Handle errors during evaluation
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

    # This doesn't work...
    # Nor does renaming "async def kernel_... to "def do_kernel_..."
    # async def kernel_info_request(self, stream, ident, parent):
    #     """Override the base handler to inject HTML metadata."""

    #     # Build the standard content
    #     content = {
    #         'protocol_version': '5.3', # from ipykernel._version import kernel_protocol_version
    #         'implementation': self.implementation,
    #         'implementation_version': self.implementation_version,
    #         'language_info': self.language_info,
    #         'banner': self.banner, # Plain text fallback
    #         'help_links': self.help_links,
    #     }

    #     # Add the Metadata block for HTML support
    #     # Note: Different frontends look for different metadata keys.
    #     content['metadata'] = {
    #         'jupyter': {
    #             'about': {
    #                 'body': "<h1>Mathics3</h1><p>A <i>Wolfram Language</i> engine with <b>SymPy</b> integration.</p>",
    #                 'logo': "static/logo-64x64.png"
    #             }
    #         }
    #     }

    #     # Send the response manually using the internal utility
    #     self.send_response(stream, 'kernel_info_reply', content, ident)


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=Mathics3Kernel)
