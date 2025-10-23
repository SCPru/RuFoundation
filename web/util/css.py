import re

def simple_minify_css(css: str) -> str:
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\s*([:;{}>,])\s*', r'\1', css)
    css = re.sub(r'\s+', ' ', css)
    css = css.strip()

    return css

def normalize_computed_style(css: str) -> str:
    import_pattern = r'(@import\s*(?:(?:url\s*\(\s*)?(["\']?)([^"\'\)]*?)\2\s*\)?\s*)(?:[^;]*);?)'
    imports = re.findall(import_pattern, css, re.IGNORECASE | re.DOTALL)
    
    if not imports:
        return css

    for import_rule in imports:
        css = css.replace(import_rule[0], '', 1)
    
    result = '\n'.join([imp[0] for imp in imports]) + '\n' + css.strip()
    
    return result