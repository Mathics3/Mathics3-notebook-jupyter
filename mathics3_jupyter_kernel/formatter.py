"""
Jupyter Mathics3 Formatter module
"""

import base64
import io
import logging
from typing import Callable

from mathics.core.atoms import String
from mathics.core.expression import BoxError, Expression
from mathics.core.symbols import Symbol
from mathics.core.systemsymbols import (
    SymbolAborted,
    SymbolExportString,
    SymbolFailed,
    SymbolFullForm,
    SymbolGraphics,
    SymbolGraphics3D,
    SymbolImage,
    SymbolInputForm,
    SymbolInterpretationBox,
    SymbolMathMLForm,
    SymbolOutputForm,
    SymbolPlot,
    SymbolStandardForm,
    SymbolString,
    SymbolTeXForm,
)

import matplotlib.pyplot as plt

# from mathics.eval.image import eval_ImageExport
from mathics.format.box import format_element

# Set up logging to file
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("/tmp/jupyter-formatter.log")
file_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(file_handler)

StringSVG = String("SVG")


def format_output(evaluation, expr, execution_count: int) -> dict:
    """
    Handle unformatted output using the *specific* capabilities
    of Mathics3 Jupyter

    evaluation.py format_output() from which this was derived is \
    similar but it can't make use of a front-ends \
    specific capabilities.

    :param evaluation: The Mathics3 evaluation context
    :param expr: The expression result to format
    """

    def eval_boxed(result, fn: Callable, obj, **options):
        try:
            boxed = fn(evaluation=obj, **options)
        except BoxError:
            boxed = None
            if not hasattr(obj, "seen_box_error"):
                obj.seen_box_error = True
                obj.message(
                    "General",
                    "notboxes",
                    Expression(SymbolFullForm, result).evaluate(obj),
                )

        return boxed

    def build_mime_content(mime_content: dict, mime_type, value) -> dict:
        data = {
            mime_type: value,
        }
        mime_content["data"] = data
        return mime_content

    def format_mathml(expr, evaluation, mime_content: dict) -> dict:
        boxed = format_element(expr, evaluation, SymbolMathMLForm)
        if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
            box_str = boxed.elements[0].value[1:-1]
            # Wrap MathML for display math with left alignment
            html_str = _wrap_mathml_for_display(box_str)
            return build_mime_content(mime_content, "text/html", html_str)

        if isinstance(boxed, String) and boxed.value.startswith('"<math'):
            box_str = boxed.value[1:-1]
            # logger.warning(f"MathML format_mathml 1: {box_str}")
            html_str = _wrap_mathml_for_display(box_str)
            return build_mime_content(mime_content, "text/html", html_str)

        boxed = format_element(expr, evaluation, SymbolStandardForm)
        return build_mime_content(mime_content, "text/plain", str(boxed))

    def _wrap_mathml_for_display(math_html: str) -> str:
        """
        Wrap MathML in a container for display math (left-aligned, block-level).

        Modifies the <math> element to use and wraps it
        in a div with left alignment.
        """
        math_html = math_html.replace("<math", "<math", 1)
        math_html = math_html.replace('display="block"', "")
        # logger.warning(f"MathML format_math: {math_html}")

        # Wrap in a div for left alignment
        return f'<div style="text-align: left; overflow-x: auto;">{math_html}</div>'

        def build_mime_content(
            mime_content: dict, mime_type, value, align=None
        ) -> dict:
            """Build MIME content with optional alignment styling."""
            # If HTML and alignment specified, wrap in a div with alignment
            if mime_type == "text/html" and align:
                value = f'<div style="text-align: {align};">{value}</div>'

            data = {
                mime_type: value,
            }
            mime_content["data"] = data
            return mime_content

    def format_text(expr, evaluation, mime_content: dict) -> dict:
        boxed = format_element(expr, evaluation, SymbolStandardForm)
        return build_mime_content(mime_content, "text/plain", str(boxed))

    # Start with the standard plain text representation
    mime_content = {"execution_count": execution_count, "metadata": {}}

    if expr is SymbolAborted:
        return build_mime_content(mime_content, "text/html", "<i>$Aborted</i>")
    elif expr is SymbolFailed:
        return build_mime_content(mime_content, "text/html", "<i>$Failed</i>")

    expr_head = expr.get_head()
    # logger.warning(f"expr: {expr}")

    if expr_head is SymbolMathMLForm:
        return format_mathml(expr, evaluation, mime_content)

    if expr_head is SymbolString:
        return build_mime_content(mime_content, "text/plain", f'"{expr.value}"')

    if isinstance(expr, Symbol) and str(expr).startswith("Global`"):
        return build_mime_content(
            mime_content, "text/html", f"<i>{expr.short_name}</i>"
        )

    if expr_head is SymbolTeXForm:
        boxed = format_element(expr, evaluation, SymbolTeXForm)
        if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
            box_str = boxed.elements[0].value[1:-1]
            return build_mime_content(mime_content, "text/latex", f"$${box_str}$$")

        box_str = f"$${boxed._value[1:-1]}$$"
        return build_mime_content(mime_content, "text/latex", box_str)

    elif (form := expr_head) in (
        SymbolFullForm,
        SymbolInputForm,
        SymbolOutputForm,
        SymbolStandardForm,
    ):
        boxed = format_element(expr, evaluation, form)
        return build_mime_content(mime_content, "text/plain", str(boxed))

    elif expr_head in (SymbolGraphics, SymbolPlot):
        svg_expr = Expression(SymbolExportString, expr, StringSVG)
        svg_str = svg_expr.evaluate(evaluation).to_python(string_quotes=False)
        return build_mime_content(mime_content, "image/svg+xml", svg_str)

    elif expr_head in (SymbolImage,):
        # Create an in-memory bytes buffer.
        # Save the PIL image into the buffer, forcing the PNG format.
        # Retrieve the raw bytes from the buffer.
        # Encode the raw bytes into a Base64 string and decode to a UTF-8 string.
        if hasattr(expr, "pil") and not hasattr(expr, "pillow"):
            expr.pillow = expr.pil()
        if hasattr(expr, "pillow"):
            buffer = io.BytesIO()
            expr.pillow.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()
            base64_encoded = base64.b64encode(png_bytes).decode("utf-8")
            # logger.warning(f"SymbolImage: {base64_encoded}")

            return build_mime_content(mime_content, "image/png", base64_encoded)
        format_text(expr, evaluation, mime_content)

    return format_mathml(expr, evaluation, mime_content)
    # return format_text(expr, evaluation, mime_content)
