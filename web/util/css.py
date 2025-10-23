import re

def simple_minify_css(css: str) -> str:
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\s*([:;{}>,])\s*', r'\1', css)
    css = re.sub(r'\s+', ' ', css)
    css = css.strip()

    return css