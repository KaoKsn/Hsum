"""
This file has API endpoints that handle working with an LLM (external or internal)

It has routes for report generation.

Currently reports can be requested in the following format:
    pdf (Portable Document Format), HTML (Hyper Text MarkUp Language)

Author: KaoKsn
"""

from markdown_it import MarkdownIt
import nh3
from weasyprint import HTML
import sys


def generateReport(format: str, content: str):
    """Generate a report in the requested format

    Raise ValueError if an unsupported format is requested

    It can raise Exceptions so the caller must handle it.
    """

    supported_formats = ["pdf", "html"]

    format = format.lower().strip()
    if format not in supported_formats:
        raise ValueError(
            f"Format: {format} isn't supported.",
            f"Please one of these: {supported_formats}",
        )
    if format == "pdf":
        return pdfGenerator(content)
    elif format == "html":
        return htmlGenerator(content)
    else:
        raise ValueError("unsupported format. Choose either `pdf` or `html`")


def pdfGenerator(content: str) -> bytes | None:
    try:
        safe_html = htmlGenerator(content)
        return safe_html.write_pdf()
    except Exception as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        raise


def htmlGenerator(markdown_text: str) -> HTML:
    md = MarkdownIt("js-default")
    rendered_html = md.render(markdown_text)

    safe_html = nh3.clean(
        rendered_html,
        tags={
            "p",
            "br",
            "hr",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "strong",
            "em",
            "del",
            "blockquote",
            "ul",
            "ol",
            "li",
            "pre",
            "code",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "a",
        },
        attributes={"a": {"href", "title"}},
        url_schemes={"http", "https", "mailto"},
    )

    document = f"""<!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: sans-serif; line-height: 1.5; }}
          pre {{ white-space: pre-wrap; }}
          table {{ border-collapse: collapse; }}
          th, td {{ border: 1px solid #aaa; padding: 0.4em; }}
        </style>
      </head>
      <body>{safe_html}</body>
    </html>"""

    return HTML(string=document)
