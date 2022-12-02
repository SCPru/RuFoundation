import re
import urllib.parse

from django.db.models import Count, Q

from renderer.utils import render_template_from_string
from . import ModuleError
from web.models.articles import Tag, TagsCategory


def parse_font_size(size):
    match = re.fullmatch(r'(\d+)(.*)', size)
    if not match:
        raise ModuleError('Некорректный размер: %s' % size)
    try:
        number = float(match[1])
        unit = match[2].strip().lower()
        return number, unit
    except:
        raise ModuleError('Некорректный размер: %s' % size)


def interpolate_font_size(min_size, max_size, value):
    min_sz, min_unit = parse_font_size(min_size)
    max_sz, max_unit = parse_font_size(max_size)
    if min_unit != max_unit:
        raise ModuleError('Разные единицы измерения максимального и минимального размера: %s и %s' % (min_size, max_size))
    sz = min_sz + (max_sz - min_sz) * value
    return '%.4f%s' % (sz, min_unit)


def parse_color(color):
    if color[0] == '#':
        if len(color) == 4 or len(color) == 7:
            try:
                if len(color) == 4:
                    r = int(color[1]+color[1], 16)
                    g = int(color[2]+color[2], 16)
                    b = int(color[3]+color[3], 16)
                else:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                return r, g, b
            except:
                pass
    elif color.lstrip().startswith('rgb'):
        match = re.fullmatch(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color.strip())
        if match:
            try:
                r = int(match[1])
                g = int(match[2])
                b = int(match[3])
                return r, g, b
            except:
                pass
    else:
        match = re.fullmatch(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color.strip())
        if match:
            try:
                r = int(match[1])
                g = int(match[2])
                b = int(match[3])
                return r, g, b
            except:
                pass
    raise ModuleError('Некорректный цвет: %s' % color)


def interpolate_color(min_color, max_color, value):
    min_r, min_g, min_b = parse_color(min_color)
    max_r, max_g, max_b = parse_color(max_color)
    r = int(min_r + (max_r - min_r) * value)
    g = int(min_g + (max_g - min_g) * value)
    b = int(min_b + (max_b - min_b) * value)
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))
    return '#%02x%02x%02x' % (r, g, b)


def render(context, params):
    if 'minfontsize' in params and 'maxfontsize' in params:
        min_size = params['minfontsize']
        max_size = params['maxfontsize']
    else:
        min_size = '100%'
        max_size = '300%'

    if 'mincolor' in params and 'maxcolor' in params:
        min_color = params['mincolor']
        max_color = params['maxcolor']
    else:
        min_color = '128,128,192'
        max_color = '64,64,128'

    limit = None
    if 'limit' in params:
        limit = int(params['limit'])

    target = params.get('target', 'system:page-tags')

    tags = Tag.objects.prefetch_related("category").filter(~Q(name__startswith='_')).annotate(num_articles=Count('articles')).order_by('-num_articles')
    if limit is not None:
        tags = tags[:limit]

    values = tags.values_list('num_articles', flat=True)
    if values:
        min_num = min(values)
        max_num = max(values)
    else:
        min_num = max_num = 0

    tags = sorted(tags, key=lambda x: x.name)

    if params.get("categories", "no") == "yes":
        render_tags = {}

        for category in TagsCategory.objects.filter(id__in=map(lambda x: x.category.id, tags)).order_by("priority"):
            render_tags[category] = []

        for tag in tags:
            value = float(tag.num_articles - min_num) / (max_num - min_num) if max_num - min_num else 0
            render_tags[tag.category].append({
                'name': tag.name,
                'color': interpolate_color(min_color, max_color, value),
                'size': interpolate_font_size(min_size, max_size, value),
                'link': '/%s/tag/%s' % (target, urllib.parse.quote(tag.full_name, safe=''))
            })

        return render_template_from_string(
            """
            <div class="pages-tag-cloud-box">
                {% for category, tags in categories.items %}
                    <div class="w-collapsible collapsible-block">
                        <div class="collapsible-block-folded" style="display: none;">
                            <h2 class="collapsible-block-link"><a href="javascript:;">+ {{ category.name }}{% if not category.is_default %} ({{ category.slug }}){% endif %}</a></h2>
                        </div>
                        <div class="collapsible-block-unfolded" style="display: block;">
                            <div class="collapsible-block-unfolded-link">
                                <h2 class="collapsible-block-link"><a href="javascript:;">- {{ category.name }}{% if not category.is_default %} ({{ category.slug }}){% endif %}</a></h2>
                            </div>
                            <div class="collapsible-block-content">
                                {% if category.description %}<h4>{{ category.description }}</h4>{% endif %}
                                <hr style="margin: auto">
                                {% for tag in tags %}
                                    <a class="tag" href="{{ tag.link }}" style="font-size: {{ tag.size }}; color: {{ tag.color }}">{{ tag.name }}</a>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    <br>
                {% endfor %}
            </div>
            """,
            categories=render_tags
        )

    render_tags = []

    for tag in tags:
        value = float(tag.num_articles - min_num) / (max_num - min_num) if max_num - min_num else 0
        render_tags.append({
            'name': tag.full_name,
            'color': interpolate_color(min_color, max_color, value),
            'size': interpolate_font_size(min_size, max_size, value),
            'link': '/%s/tag/%s' % (target, urllib.parse.quote(tag.full_name, safe=''))
        })

    return render_template_from_string(
            """
            <div class="pages-tag-cloud-box">
                {% for tag in tags %}
                    <a class="tag" href="{{ tag.link }}" style="font-size: {{ tag.size }}; color: {{ tag.color }}">{{ tag.name }}</a>
                {% endfor %}
            </div>
            """,
            tags=render_tags
        )
