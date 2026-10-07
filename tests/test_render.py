import pytest

from ff_briefing.render.converter import RenderError, render_html

TITLE = "Fantasy briefing for 2026-10-07"


def test_headings_lists_and_links_render_as_html_elements() -> None:
    out = render_html("# Title\n\n- a\n- b\n\n[src](https://example.com/x)", TITLE)

    assert "<h1>Title</h1>" in out
    assert "<ul>" in out and out.count("<li>") == 2
    assert '<a href="https://example.com/x">src</a>' in out


def test_markdown_table_renders_header_and_data_cells() -> None:
    out = render_html("| A | B |\n|---|---|\n| 1 | 2 |\n", TITLE)

    assert "<table>" in out
    assert "<th>A</th>" in out
    assert "<td>1</td>" in out


def test_league_headings_render_as_ordered_h2_sections() -> None:
    out = render_html("## Sunday Funday\n\ntext\n\n## Office League\n\ntext", TITLE)

    assert out.count("<h2>") == 2
    assert out.index("Sunday Funday") < out.index("Office League")


def test_output_declares_dark_scheme_and_has_no_external_references() -> None:
    out = render_html("# Hello\n\nno links here", TITLE)

    assert "prefers-color-scheme: dark" in out
    assert "<link" not in out
    assert "<script" not in out
    assert "http" not in out


def test_raw_html_in_markdown_is_escaped() -> None:
    out = render_html("<script>alert(1)</script>\n\ntext", TITLE)

    assert "&lt;script&gt;" in out
    assert "<script>" not in out


def test_title_appears_in_title_tag_and_is_escaped() -> None:
    out = render_html("# Hi", "A <b> & 2026-10-07")

    assert "<title>A &lt;b&gt; &amp; 2026-10-07</title>" in out


def test_title_is_shown_as_page_heading() -> None:
    out = render_html("body text", TITLE)

    assert f'<h1 class="page-title">{TITLE}</h1>' in out


@pytest.mark.parametrize("text", ["", "  \n\n", "\t\n"])
def test_blank_markdown_raises_render_error(text: str) -> None:
    with pytest.raises(RenderError):
        render_html(text, TITLE)


def test_markdown_with_no_block_content_raises_render_error() -> None:
    with pytest.raises(RenderError):
        render_html("[ref]: https://example.com/x", TITLE)
