import html
import re
from importlib import resources

from markdown_it import MarkdownIt

from ff_briefing.errors import BriefingError


class RenderError(BriefingError):
    pass


def _template() -> str:
    return resources.files("ff_briefing.render").joinpath("template.html").read_text("utf-8")


def render_html(markdown_text: str, title: str) -> str:
    if not markdown_text.strip():
        raise RenderError("briefing markdown is empty; nothing to render")
    # html=False escapes raw HTML: the briefing is LLM output built from web-sourced text.
    body = MarkdownIt("commonmark", {"html": False}).enable("table").render(markdown_text)
    if not body.strip():
        raise RenderError("briefing markdown has no renderable content")
    # Single pass so placeholder-like text inside the title or body is never re-expanded.
    values = {"title": html.escape(title), "body": body}
    return re.sub(r"\{\{(title|body)\}\}", lambda m: values[m.group(1)], _template())
