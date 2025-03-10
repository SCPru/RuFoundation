from renderer.utils import render_template_from_string

def render(context, params):
    rat = 'vertical-rat.gif' if params.get('direction') == 'vertical' else 'horizontal-rat.gif'
    return render_template_from_string(
        """<img src="/-/static/rat/{{ rat }}" alt="this slowpoke moves"  width="250" />""",
        rat=rat
    )