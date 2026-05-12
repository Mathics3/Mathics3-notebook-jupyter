import sys
from ipykernel.kernelbase import Kernel

# Try to import the Mathics3 core engine
try:
    from mathics.session import MathicsSession
except ImportError as e:
    # This is a common failure point if mathics-core is not installed
    # in the same environment as the kernel
    print(f"Error: mathics not found: {e}\n. Please install it with 'pip install Mathics3'", file=sys.stderr)
    MathicsSession = None

class Mathics3Kernel(Kernel):
    implementation = 'Mathics3'
    implementation_version = '1.0'
    language = 'mathematica'
    language_version = '1.0'
    language_info = {
        'name': 'mathematica',
        'mimetype': 'text/x-mathematica',
        'file_extension': '.m',
    }
    banner = "Mathics3 Kernel - A Wolfram Language compatible engine"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # CRITICAL: Do NOT name this 'self.session'.
        # ipykernel uses 'self.session' for its own messaging system.
        if MathicsSession:
            self.mathics_engine = MathicsSession()
        else:
            self.mathics_engine = None

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        if not self.session:
            return {
                'status': 'error',
                'ename': 'ImportError',
                'evalue': 'Mathics core not loaded',
                'traceback': []
            }

        if not silent and self.mathics_engine:
            try:
                # Evaluate the input code using the Mathics3 engine
                # Mathics3 returns an object that we can convert to a string
                result = self.mathics_engine.evaluate(code)
                output = str(result)

                # Send the result back to the Jupyter frontend
                stream_content = {'name': 'stdout', 'text': output}
                self.send_response(self.iopub_socket, 'stream', stream_content)

            except Exception as e:
                # Handle errors during evaluation
                return {
                    'status': 'error',
                    'ename': type(e).__name__,
                    'evalue': str(e),
                    'traceback': []
                }

        return {
            'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=Mathics3Kernel)
