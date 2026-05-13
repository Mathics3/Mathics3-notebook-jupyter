"""
Jupyter Mathics3 Formatter module
"""

# import base64
# from mathics.formatters import MathicsLaTeXFormatter
from IPython.display import HTML, Code, Javascript, Math
from mathics3_kernel.frontend.format import Formatter


class Mathics3JupyterFormatter(Formatter):
    """
    Handles the conversion of Mathics3 expressions into Jupyter-compatible
    MIME types (text/plain, text/latex, image/svg+xml, etc.)
    """

    def __init__(self):
        # We reuse the LaTeX formatter instance for efficiency
        # self.latex_formatter = MathicsLaTeXFormatter()
        pass

    def text(self, result):
        return Code(result, language="mathematica")

    def math(self, result):
        return Math(result)

    def graphics3d(self, result):
        # return JSON(json.loads(result))
        return Javascript(f"drawGraphics3d(element, {result})")

    def svg(self, result):
        return self.html(result)

    def html(self, result):
        result = result.replace("<math", "<div")
        result = result.replace("<mglyph", '<img style="display: inline-block" ')
        result = result.replace("<mrow>", "")
        result = result.replace("<mo>", "")
        return HTML(result)

    def format_output(self, evaluation, expr):
        """
        Processes a Mathics3 expression and returns a dictionary mapping
        MIME types to their formatted string/byte data.

        :param evaluation: The Mathics3 evaluation context
        :param expr: The expression result to format
        """
        # Start with the standard plain text representation
        data = {"text/plain": str(expr)}

        # try:
        #     # We attempt to format the expression as LaTeX for MathJax rendering
        #     latex_code = self.latex_formatter.format(expr)
        #     if latex_code:
        #         data['text/latex'] = f"${latex_code}$"
        # except Exception:
        #     # If LaTeX formatting fails, we fallback gracefully
        #     pass

        # try:
        #     # Check for SVG support (vector graphics)
        #     if hasattr(expr, 'get_as_svg'):
        #         svg_data = expr.get_as_svg()
        #         if svg_data:
        #             data['image/svg+xml'] = svg_data

        #     # Check for PNG support (raster graphics)
        #     elif hasattr(expr, 'get_as_png'):
        #         png_bytes = expr.get_as_png()
        #         if png_bytes:
        #             data['image/png'] = base64.b64encode(png_bytes).decode('ascii')
        # except Exception:
        #     # Graphics errors should not crash the kernel execution
        #     pass

        return data
