from ipykernel.kernelbase import Kernel
from IPython.display import Javascript, display
from mathics.core.load_builtin import import_and_load_builtins
from mathics.session import MathicsSession

from mathics3_jupyter_notebook.formatter import JupyterFormatter

import_and_load_builtins()


class Mathics3Kernel(Kernel):
    implementation = "Mathics3"
    implementation_version = "1.0"
    language = "mathematica"
    language_version = "1.0"
    language_info = {
        "name": "mathematica",
        "mimetype": "text/x-mathematica",
        "file_extension": ".m",
    }
    banner = "Mathics3 Kernel - A Wolfram Language compatible engine"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Do NOT name this 'self.session'.
        # ipykernel uses 'self.session' for its own messaging system.
        self.mathics_engine = MathicsSession()
        self.formatter = JupyterFormatter()
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
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=True
    ):
        if not self.session:
            return {
                "status": "error",
                "ename": "ImportError",
                "evalue": "Mathics core not loaded",
                "traceback": [],
            }

        if not silent and self.mathics_engine:
            try:
                # Evaluate the input code using the Mathics3 engine
                # Mathics3 returns an object that we can convert to a string
                result = self.mathics_engine.evaluate(code)
                output = str(result)

                # Send the result back to the Jupyter frontend
                stream_content = {"name": "stdout", "text": output}
                self.send_response(self.iopub_socket, "stream", stream_content)

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


if __name__ == "__main__":
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=Mathics3Kernel)
