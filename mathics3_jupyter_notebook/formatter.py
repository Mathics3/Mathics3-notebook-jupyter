"""
Jupyter Mathics3 Formatter module
"""

from typing import Dict, Final

from mathics.core.atoms import String
from mathics.core.systemsymbols import (
    SymbolAborted,
    SymbolFailed,
    SymbolInterpretationBox,
    SymbolOutputForm,
    SymbolStandardForm,
    SymbolTeXForm,
)
from mathics.format.box import format_element

# import base64
# from mathics.formatters import MathicsLaTeXFormatter


# Maps a Form to a kind of html format.
# text is the usual text-kind of output.
# LaTeX is handled by MathJaX display mode $$ $$
# MathML could be tagged differently too.
FORM_TO_HTML_TAG_FORMAT: Final[Dict[str, str]] = {
    "System`FullForm": "text",
    "System`InputForm": "text",
    "System`MathMLForm": "MathML",
    "System`OutputForm": "text",
    "System`TeXForm": "LaTeX",
    "System`String": "text",
}


def format_output(evaluation, expr, execution_count: int) -> dict:
    """
    Handle unformatted output using the *specific* capabilities \
    of mathics-django.

    evaluation.py format_output() from which this was derived is \
    similar but it can't make use of a front-ends \
    specific capabilities.

    :param evaluation: The Mathics3 evaluation context
    :param expr: The expression result to format
    """

    def build_content(content: dict, mime_type, value) -> dict:
        data = {
            mime_type: value,
        }
        content["data"] = data
        return content

    # Start with the standard plain text representation
    content = {"execution_count": execution_count, "metadata": {}}

    if expr is SymbolAborted:
        return build_content(content, "text/plain", "$Aborted")
    elif expr is SymbolFailed:
        return build_content(content, "text/plain", "$Failed")

    # For some expressions, we want formatting to be different.
    # In particular for FullForm and InputForm output, we don't want
    # MathML, we want
    # plain-ol' text so we can cut and paste that.
    expr_type = expr.get_head_name()
    # For these forms, we strip off the outer "Form" part
    html_tag_format = FORM_TO_HTML_TAG_FORMAT.get(expr_type, "xml")

    # This part is similar to mathics.core.evaluation.format_output().
    if html_tag_format == "text":
        boxed = format_element(expr, evaluation, SymbolOutputForm)
        if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
            return build_content(content, "text/plain", boxed.elements[0].value)

        result = boxed.boxes_to_text()
        return build_content(content, "text/plain", result)

    if html_tag_format == "xml":
        boxed = format_element(expr, evaluation, SymbolStandardForm)
        if (
            hasattr(boxed, "head")
            and boxed.head is SymbolInterpretationBox
            and (box_value := boxed.elements[0].value).startswith('"<math ')
        ):
            # FIXME: [1:-1] is to strip quotes.
            # We should probably address a long-standing mistake where strings
            # have quotes in them.
            return build_content(content, "text/html", box_value)

        # This can happen.
        mathml = boxed.to_mathml(evaluation=evaluation)
        return build_content(content, "text/html", f"<math>{mathml}</math>")

    if html_tag_format == "LaTeX":
        boxed = format_element(expr, evaluation, SymbolTeXForm)
        render_TeXForm_expr = evaluation.parse("Settings`$RenderTeXForm")
        if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
            # FIXME: [1:-1] is to strip quotes.
            # We should probably address a long-standing mistake where strings
            # have quotes in them.
            box_str_sans_quotes = boxed.elements[0].value[1:-1]
            render_TeXForm = render_TeXForm_expr.evaluate(evaluation).to_python()
            if render_TeXForm:
                box_str_sans_quotes = f"$${box_str_sans_quotes}$$"
            return build_content(content, "text/latex", box_str_sans_quotes)

        # THINK ABOUT: This probably no longer happens
        if isinstance(boxed, String):
            return build_content(content, "text/plain", boxed.to_text())
        else:
            render_TeXForm = render_TeXForm_expr.evaluate(evaluation).to_python()
            result = boxed.to_tex(evaluation=evaluation)
            if render_TeXForm:
                result = f"$${result}$$"
                mime_type = "text/latex"
            else:
                mime_type = "text/plain"
            return build_content(content, mime_type, result)

    return build_content(content, "text/plain", str(expr))
