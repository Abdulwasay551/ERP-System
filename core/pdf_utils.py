from django.template.loader import render_to_string
import tempfile

def render_pdf(template_src, context_dict, output_path=None):
    # Imported lazily, not at module load time: WeasyPrint needs native Pango/Cairo
    # system libraries that aren't present on Vercel's Python serverless runtime. A
    # top-level import here would crash on import for every single request (urls.py ->
    # sales.api_urls -> sales.api_views -> this module), not just PDF generation -
    # deferring it means only an actual render_pdf() call fails, and callers already
    # catch that and degrade gracefully instead of taking down the whole site.
    from weasyprint import HTML
    html_string = render_to_string(template_src, context_dict)
    html = HTML(string=html_string)
    if output_path:
        html.write_pdf(target=output_path)
        return output_path
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as output:
            html.write_pdf(target=output.name)
            return output.name 