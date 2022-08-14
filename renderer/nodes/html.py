from django.utils.safestring import SafeString
import re

from renderer import nodes
from . import Node
from ..tokenizer import TokenType
from django.utils import html
from .link import LinkNode

# this module also handles HTML-like nodes, such as include, module...


class HTMLNode(Node):
    starting_token_type = TokenType.OpenDoubleBracket

    @classmethod
    def extract_name_from_attributes(cls, attributes):
        if attributes and attributes[0]:
            return attributes[0][0], attributes[1:]
        return '', attributes

    @classmethod
    def parse(cls, p):
        from .html_base import HTMLBaseNode

        # [[ has already been parsed
        sub_html_nodes = [x for x in nodes.NODE_CLASSES if issubclass(x, HTMLBaseNode) and x != HTMLBaseNode]

        p.tokenizer.skip_whitespace()
        name = p.read_as_value_until([TokenType.Whitespace, TokenType.CloseDoubleBracket])
        if name is None:
            return None
        name = name.lower()
        if name and name[0] == '/':
            return None
        trim_paragraphs = False
        if name.endswith('_'):
            trim_paragraphs = True
            name = name[:-1]

        # find which subclass to use. check if current configuration is allowed
        f_cls = None
        for node_cls in sub_html_nodes:
            if not node_cls.is_allowed(name, p):
                continue
            f_cls = node_cls

        if not f_cls:
            return None

        in_tabview = (name == 'tabview')
        attributes = []
        children = []
        module_content = ''
        while True:
            p.tokenizer.skip_whitespace()
            if f_cls.is_single_argument:
                tab_name = p.read_as_value_until([TokenType.CloseDoubleBracket])
                if tab_name is None:
                    return None
                attributes.append((tab_name.strip(), tab_name.strip()))
                tk = p.tokenizer.read_token()
                if tk.type != TokenType.CloseDoubleBracket:
                    return None
                break
            elif f_cls.is_first_single_argument and not attributes:
                arg = p.read_as_value_until([TokenType.Whitespace, TokenType.CloseDoubleBracket])
                if arg is None:
                    return None
                attributes.append((arg.strip(), arg.strip()))
                tk = p.tokenizer.read_token()
                if tk.type == TokenType.CloseDoubleBracket:
                    break
                continue
            maybe_pipe = [TokenType.Pipe] if f_cls.pipe_separated_attributes else []
            attr_name = p.read_as_value_until(
                [TokenType.CloseDoubleBracket, TokenType.Whitespace, TokenType.Newline, TokenType.Equals] + maybe_pipe)
            if attr_name is None:
                return None
            attr_name = attr_name.strip()
            p.tokenizer.skip_whitespace()
            pos = p.tokenizer.position
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.CloseDoubleBracket:
                if attr_name:
                    attributes.append((attr_name, attr_name))
                break
            elif tk.type == TokenType.Pipe:
                # there can be random pipes
                if attr_name:
                    attributes.append((attr_name, attr_name))
                continue
            else:
                # read attribute
                if tk.type != TokenType.Equals:
                    p.tokenizer.position = pos
                    if attr_name:
                        attributes.append((attr_name, attr_name))
                    continue
                # from here, different handling for include. this is a hack in original Wikidot syntax
                if f_cls.pipe_separated_attributes:
                    value = p.read_as_value_until([TokenType.Pipe, TokenType.CloseDoubleBracket])
                    if value is None:
                        return None
                    attributes.append((attr_name, value.strip()))
                    pos = p.tokenizer.position
                    tk = p.tokenizer.read_token()
                    if tk.type != TokenType.Pipe:
                        p.tokenizer.position = pos
                else:
                    p.tokenizer.skip_whitespace()
                    tk = p.read_quoted_arg()
                    if tk.type != TokenType.String and tk.type != TokenType.QuotedString:
                        p.tokenizer.position = pos
                        continue
                    attributes.append((attr_name, tk.value))
        if f_cls.is_single_tag(name, attributes):
            default_content = '' if f_cls.is_raw_text else []
            c = f_cls(name, attributes, default_content)
            c.trim_paragraphs = trim_paragraphs
            return c
        # tag beginning found. now iterate and check for tag ending
        while True:
            pos = p.tokenizer.position
            tk = p.tokenizer.read_token()
            first_tk = tk
            if first_tk.type == TokenType.Null:
                return None
            first_pos = p.tokenizer.position
            # [[ / <attr_name> ]]
            if tk.type == TokenType.OpenDoubleBracket:
                p.tokenizer.skip_whitespace()
                tk = p.tokenizer.read_token()
                if tk.type == TokenType.Slash:
                    p.tokenizer.skip_whitespace()
                    close_name = p.read_as_value_until([TokenType.CloseDoubleBracket, TokenType.Whitespace])
                    if close_name is None:
                        return None
                    close_name = close_name.lower()
                    if close_name.endswith('_'):
                        close_name = close_name[:-1]
                    if close_name == name:
                        p.tokenizer.skip_whitespace()
                        tk = p.tokenizer.read_token()
                        if tk.type == TokenType.CloseDoubleBracket:
                            # all done!
                            if trim_paragraphs:
                                # special handling, we just eat any whitespace or newlines.
                                # this reproduces what wikidot does with [[span_]]
                                while True:
                                    pos = p.tokenizer.position
                                    tk = p.tokenizer.read_token()
                                    if tk.type == TokenType.Whitespace or tk.type == TokenType.Newline:
                                        continue
                                    p.tokenizer.position = pos
                                    break
                            if f_cls.is_raw_text:
                                c = f_cls(name, attributes, module_content)
                                c.trim_paragraphs = trim_paragraphs
                                return c
                            else:
                                c = f_cls(name, attributes, children)
                                c.trim_paragraphs = trim_paragraphs
                                return c

            if not f_cls.is_raw_text:
                p.tokenizer.position = pos
                was_in_tabview = p._context._in_tabview
                p._context._in_tabview = in_tabview
                new_children = p.parse_nodes()
                p._context._in_tabview = was_in_tabview
                if not new_children:  # this means we reached EOF before locating end tag
                    return None
                children += new_children
            else:
                p.tokenizer.position = first_pos
                module_content += first_tk.raw

    allowed_tags = ['a', 'span', 'div', 'div_', 'table', 'row', 'hcell', 'cell', 'li', 'ul', 'ol']

    @staticmethod
    def node_allowed(name):
        name = name.lower()
        return name in HTMLNode.allowed_tags

    @staticmethod
    def get_attribute(attributes, name, default=None):
        name = name.lower()
        attr = [x for x in attributes if x[0].lower() == name]
        if attr:
            return attr[0][1]
        else:
            return default

    @staticmethod
    def set_attribute(attributes, name, value):
        name = name.lower()
        return [((x[0], value) if x[0].lower() == name else x) for x in attributes]

    @staticmethod
    def render_attributes(attributes, attr_whitelist):
        attr_string = ''
        for attr in attributes:
            attr_name = attr[0].lower()
            if attr_name not in attr_whitelist and not re.match(r'^data-([a-z0-9\-_]+)$', attr_name):
                continue
            attr_string += ' '
            attr_string += html.escape(attr_name)
            if attr[1] is not None:
                value = attr[1]
                if attr[0] == 'id' and not value.startswith('u-'):
                    value = 'u-' + value
                elif attr[0] == 'href':
                    value = LinkNode.filter_url(value)
                attr_string += '="%s"' % html.escape(value)
        return SafeString(attr_string)
