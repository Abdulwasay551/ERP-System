from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile

def render_pdf(template_src, context_dict, output_path=None):
    html_string = render_to_string(template_src, context_dict)
    html = HTML(string=html_string)
    if output_path:
        html.write_pdf(target=output_path)
        return output_path
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as output:
            html.write_pdf(target=output.name)
            return output.name 