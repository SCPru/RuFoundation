from renderer.utils import render_template_from_string

def render(context, params):
    rat = 'vertical-rat.gif' if params.get('direction') == 'vertical' else 'horizontal-rat.gif'
    return render_template_from_string(
        """
        <img src="/-/static/rat/{{ rat }}" alt="this slowpoke moves"  width="250" />
        <audio autoplay loop>
            <source src="/-/static/rat/rat.mp3" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        """,
        rat=rat
    )