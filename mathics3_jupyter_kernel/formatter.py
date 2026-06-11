"""
Jupyter Mathics3 Formatter module
"""

import base64
import io
import logging
from typing import Dict, Final

from mathics.core.atoms import String
from mathics.core.expression import Expression
from mathics.core.symbols import Symbol
from mathics.core.systemsymbols import (
    SymbolAborted,
    SymbolExportString,
    SymbolFailed,
    SymbolInterpretationBox,
    SymbolMathMLForm,
    SymbolOutputForm,
    SymbolPaneBox,
    SymbolStandardForm,
    SymbolTeXForm,
)

# from mathics.eval.image import eval_ImageExport
from mathics.format.box import format_element

# Maps a Form to a kind of html format.
# text is the usual text-kind of output.
# LaTeX is handled by MathJaX display mode $$ $$
# MathML could be tagged differently too.
FORM_TO_HTML_TAG_FORMAT: Final[Dict[str, str]] = {
    "System`FullForm": "text",
    "System`InputForm": "text",
    "System`MathMLForm": "mathml",
    "System`MatrixForm": "mathml",
    "System`OutputForm": "text",
    "System`TeXForm": "latex",
    "System`String": "text",
}


# Set up logging to file
logger = logging.getLogger(__name__)
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

    # def eval_boxed(result, fn: Callable, obj, **options):
    #     try:
    #         boxed = fn(evaluation=obj, **options)
    #     except BoxError:
    #         boxed = None
    #         if not hasattr(obj, "seen_box_error"):
    #             obj.seen_box_error = True
    #             obj.message(
    #                 "General",
    #                 "notboxes",
    #                 Expression(SymbolFullForm, result).evaluate(obj),
    #             )

    #     return boxed

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
            html_str = _wrap_mathml_for_display(box_str)
            return build_mime_content(mime_content, "text/html", html_str)

        boxed = format_element(expr, evaluation, SymbolStandardForm)
        return build_mime_content(mime_content, "text/plain", str(boxed))

    # def format_latex(expr, evaluation, mime_content: dict) -> dict:
    #     boxed = format_element(expr, evaluation, SymbolMathMLForm)
    #     if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
    #         box_str = boxed.elements[0].value[1:-1]
    #         # Wrap MathML for display math with left alignment
    #         html_str = _wrap_tex_for_display(box_str)
    #         return build_mime_content(mime_content, "text/latex", html_str)

    #     if isinstance(boxed, String):
    #         box_str = boxed.value[1:-1]
    #         html_str = _wrap_tex_for_display(box_str)
    #         return build_mime_content(mime_content, "text/latex", html_str)

    #     boxed = format_element(expr, evaluation, SymbolStandardForm)
    #     return build_mime_content(mime_content, "text/plain", str(boxed))

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

    # def _wrap_tex_for_display(tex_html: str) -> str:
    #     """
    #     Wrap MathML in a container for display math (left-aligned, block-level).

    #     Modifies the <math> element to use and wraps it
    #     in a div with left alignment.
    #     """
    #     # Wrap in a div for left alignment
    #     return f'<div style="text-align: left; overflow-x: auto;">{tex_html}</div>'

    #     def build_mime_content(
    #         mime_content: dict, mime_type, value, align=None
    #     ) -> dict:
    #         """Build MIME content with optional alignment styling."""
    #         # If HTML and alignment specified, wrap in a div with alignment
    #         if mime_type == "text/html" and align:
    #             value = f'<div style="text-align: {align};">{value}</div>'

    #         data = {
    #             mime_type: value,
    #         }
    #         mime_content["data"] = data
    #         return mime_content

    # def format_text(expr, evaluation, mime_content: dict) -> dict:
    #     boxed = format_element(expr, evaluation, SymbolStandardForm)
    #     return build_mime_content(mime_content, "text/plain", str(boxed))

    # Start with the standard plain text representation
    mime_content = {"execution_count": execution_count, "metadata": {}}

    if expr is SymbolAborted:
        return build_mime_content(mime_content, "text/html", "<i>$Aborted</i>")
    elif expr is SymbolFailed:
        return build_mime_content(mime_content, "text/html", "<i>$Failed</i>")

    # logger.warning(f"expr: {expr}")

    # For some expressions, we want formatting to be different.
    # In particular for FullForm and InputForm output, we don't want
    # MathML, we want plain-ol' text so we can cut and paste that.

    expr_head = expr.get_head_name()
    if expr_head in FORM_TO_HTML_TAG_FORMAT:
        # For these forms, we strip off the outer "Form" part
        html_tag_format = FORM_TO_HTML_TAG_FORMAT[expr_head]
    else:
        html_tag_format = "mathml"

    # logger.warning(f"expr: {expr}")
    # print(f"XXX expr: {expr} expr_head: {expr_head}")

    # Note: We order tests more general tests at the end.
    # Note: I (rocky) haven't been able to get this to work using Symbols, e.g.
    # SymbolString, SymbolGraphics, etc. I don't know why. One handicap is
    # that not expr.head is not always guarenteed to work. Although, that is
    # worked around using hasattr(expr, "head"), something more needs to be done.
    if expr_head in ("System`String",):
        return build_mime_content(mime_content, "text/plain", f'"{expr.value}"')

    if expr_head in ("System`Graphics", "System`Plot"):
        svg_expr = Expression(SymbolExportString, expr, StringSVG)
        svg_str = svg_expr.evaluate(evaluation).to_python(string_quotes=False)
        return build_mime_content(mime_content, "image/svg+xml", svg_str)

    if expr_head in ("System`Graphics3D"):
        # FIXME:
        boxed = format_element(expr, evaluation, SymbolMathMLForm)
        if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
            box_str = boxed.elements[0].value[1:-1]
            # print(f"XXX0 {box_str}")
            return build_mime_content(mime_content, "text/plain", box_str)
        # print(f"XXX1: {boxed}")
        return build_mime_content(mime_content, "text/html", boxed)

    if expr_head in ("System`Image",):
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

    if expr_head == "Pymathics`Graph" and hasattr(expr, "G"):
        from pymathics.graph.format import format_graph, get_svg_graph

        format_graph(expr.G)
        svg_str = get_svg_graph()
        return build_mime_content(mime_content, "image/svg+xml", svg_str)

    # This part is similar to mathics.core.evaluation.format_output().
    if html_tag_format == "text":
        boxed = format_element(expr, evaluation, SymbolOutputForm)
        boxed_head = boxed.head
        if boxed_head is SymbolInterpretationBox:
            box_str = str(boxed)
            first_element = boxed.elements[0]
            first_head = first_element.head
            if first_head is SymbolPaneBox:
                box_str = first_element.elements[0].value[1:-1]
            return build_mime_content(mime_content, "text/plain", box_str)
        return build_mime_content(mime_content, "text/plain", boxed.to_text())

    if expr_head is SymbolMathMLForm or html_tag_format == "mathml":
        return format_mathml(expr, evaluation, mime_content)

    if isinstance(expr, Symbol) and str(expr).startswith("Global`"):
        return build_mime_content(
            mime_content, "text/html", f"<i>{expr.short_name}</i>"
        )

    if expr_head is SymbolTeXForm or html_tag_format == "latex":
        boxed = format_element(expr, evaluation, SymbolTeXForm)
        if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
            box_str = f"$${boxed.elements[0].value[1:-1]}$$"
        else:
            box_str = f"$${boxed._value[1:-1]}$$"

        return build_mime_content(mime_content, "text/latex", box_str)

    elif expr_head in (
        "System,`FullForm",
        "System`InputForm",
        "System`OutputForm",
        "System`StandardForm",
    ):
        form = Symbol(expr_head)
        boxed = format_element(expr, evaluation, form)
        return build_mime_content(mime_content, "text/plain", str(boxed))

    return format_mathml(expr, evaluation, mime_content)
    # return format_text(expr, evaluation, mime_content)
