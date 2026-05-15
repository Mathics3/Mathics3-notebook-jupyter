"""
Jupyter Mathics3 Formatter module
"""

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

# from mathics.eval.image import eval_ImageExport
from mathics.format.box import format_element

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
            return build_mime_content(mime_content, "text/html", box_str)

        if isinstance(boxed, String) and boxed.value.startswith('"<math'):
            return build_mime_content(mime_content, "text/html", boxed.value[1:-1])

        boxed = format_element(expr, evaluation, SymbolStandardForm)
        return build_mime_content(mime_content, "text/plain", str(boxed))

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

    elif expr_head in (SymbolGraphics, SymbolImage, SymbolPlot):
        svg_expr = Expression(SymbolExportString, expr, StringSVG)
        svg_str = svg_expr.evaluate(evaluation).to_python(string_quotes=False)
        return build_mime_content(mime_content, "image/svg+xml", svg_str)
    # elif expr_head in (SymbolImage):
    #     png_data = expr.pil().to_bytes()
    #     return build_mime_content(mime_content, "image/svg+xml", png_data)

    return format_mathml(expr, evaluation, mime_content)
    # return format_text(expr, evaluation, mime_content)
