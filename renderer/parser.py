from .tokenizer import TokenType
from django.utils import html
from web.controllers import articles


class RenderContext(object):
    def __init__(self, article, source_article):
        self.article = article
        self.source_article = source_article


class Node(object):
    def __init__(self):
        self.children = []
        self.parent = None
        # Block node is a node that will always close current paragraph
        self.block_node = False
        # Complex node is a node that prevents treating the line as plain text paragraph
        # (based on Wikidot's weird treating of lines that start with [[, [, or something similar)
        self.complex_node = False

    def append_child(self, child):
        if type(child) == TextNode and self.children and type(self.children[-1]) == TextNode:
            self.children[-1].text += child.text
            return
        child.parent = self
        self.children.append(child)

    def render(self, context=None):
        content = ''
        was_block = True
        was_newline = 1
        was_forced = False
        is_raw_line = False
        for child in self.children:
            child_content = child.render(context)
            # empty children are not visible
            if not child_content:
                continue
            # ignore/not ignore newline
            if type(child) == NewlineNode and self.block_node and was_newline and not was_block:
                content += '</p><p>'
            # 1. true and (false or (true and not false)) -> true and (false or (true)) -> true and (true) -> true
            # 2.
            if type(child) == NewlineNode and not was_forced and (was_newline or was_block):
                if child.forced and was_newline <= 1:
                    was_forced = True
                was_newline += 1
                continue
            elif type(child) != NewlineNode and was_newline:
                was_newline = 0
                was_forced = False
                is_raw_line = not child.complex_node
            elif type(child) == NewlineNode:
                was_newline = 1
                was_forced = False
            # close/open paragraph. ignore newline nodes here
            if type(child) != NewlineNode and self.block_node and child_content.strip():
                if child.block_node and not was_block and is_raw_line:
                    content += '</p>'
                elif not child.block_node and was_block and is_raw_line:
                    content += '<p>'
                was_block = child.block_node
            content += child_content
        if not was_block and is_raw_line:
            content += '</p>'
        return content

    def to_json(self):
        base = {'type': str(type(self)), 'children': [x.to_json() for x in self.children]}
        for k in self.__dict__:
            if k in ['parent', 'children']:
                continue
            base[k] = self.__dict__[k]
        return base


class TextNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def render(self, context=None):
        return html.escape(self.text).replace('--', '&mdash;').replace('&lt;&lt;', '&laquo;').replace('&gt;&gt;', '&raquo;')


class HTMLLiteralNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.force_render = True

    def render(self, context=None):
        return self.text.strip()


class NewlineNode(Node):
    def __init__(self, forced):
        super().__init__()
        self.forced = forced

    def render(self, context=None):
        if self.parent is not None and (self == self.parent.children[0] or self == self.parent.children[-1]):
            return ''
        return '<br>'


class ColorNode(Node):
    def __init__(self, color, content):
        super().__init__()
        self.color = color
        self.content = content

    def render(self, context=None):
        return '<span style="color: #%s">%s</span>' % (html.escape(self.color), html.escape(self.content))


class HorizontalRulerNode(Node):
    def __init__(self):
        super().__init__()
        self.block_node = True

    def render(self, context=None):
        return '<hr>'


class HTMLNode(Node):
    def __init__(self, name, attributes, children):
        super().__init__()
        self.name = name
        self.attributes = attributes
        self.block_node = self.name in ['div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        self.complex_node = True
        for child in children:
            self.append_child(child)

    allowed_tags = ['a', 'span', 'div']

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

    def render(self, context=None):
        content = super().render(context=context)
        attr_string = ''
        attr_whitelist = ['class', 'id', 'style']
        if self.name == 'a':
            attr_whitelist.append('href')
            attr_whitelist.append('target')
        for attr in self.attributes:
            if attr[0] not in attr_whitelist:
                continue
            attr_string += ' '
            attr_string += attr[0]
            if attr[1] is not None:
                value = attr[1]
                if attr[0] == 'id' and not value.startswith('u-'):
                    value = 'u-' + value
                attr_string += '="%s"' % html.escape(value)
        return '<%s%s>%s</%s>' % (html.escape(self.name), attr_string, content, html.escape(self.name))


class ImageNode(Node):
    def __init__(self, img_type, source, attributes):
        super().__init__()
        self.img_type = img_type
        self.source = source
        self.attributes = attributes
        self.complex_node = True

    def _get_image_url(self, context=None):
        if context is None or context.source_article is None:
            return None
        return '/local--files/%s/%s' % (articles.get_full_name(context.source_article), self.source)

    def render(self, context=None):
        url = self._get_image_url(context)
        if self.img_type == 'image':
            return '<img src="%s" alt="%s">' % (html.escape(url), html.escape(self.source))
        return ''


class LinkNode(Node):
    def __init__(self, url, text, blank=False):
        super().__init__()
        self.url = url
        self.text = text
        self.blank = blank

    def render(self, context=None):
        blank = ' target="_blank"' if self.blank else ''
        return '<a href="%s"%s>%s</a>' % (html.escape(self.url), blank, html.escape(self.text))


class CommentNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def render(self, context=None):
        #return '<!-- %s -->' % html.escape(self.text)
        # This is actually not rendered
        return ''


class IncludeNode(Node):
    def __init__(self, name, attributes):
        super().__init__()
        self.name = name
        self.attributes = attributes
        self.complex_node = True

    def render(self, context=None):
        return '<div>Include is not supported yet</div>'


class IframeNode(Node):
    def __init__(self, url, attributes):
        super().__init__()
        self.url = url
        self.attributes = attributes
        self.complex_node = True
        self.block_node = True

    def render(self, context=None):
        return '<div>Iframe is not supported yet</div>'


class ModuleNode(Node):
    def __init__(self, name, attributes, content):
        super().__init__()
        self.name = name.lower()
        self.attributes = attributes
        self.content = content
        self.block_node = True
        self.complex_node = True

    @staticmethod
    def module_has_content(name):
        name = name.lower()
        print('module', repr(name))
        content_modules = ['css', 'listpages', 'listusers']
        return name in content_modules

    def render(self, context=None):
        # render only module CSS for now
        if self.name == 'css':
            return '<style>%s</style>' % html.escape(self.content)
        return '<div>Module \'%s\' is not supported yet</div>' % html.escape(self.name)


class CollapsibleNode(Node):
    def __init__(self, attributes, children):
        super().__init__()
        self.attributes = attributes
        self.block_node = True
        self.complex_node = True
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        code = '<div class="collapsible-block">'
        code += '  <div class="collapsible-block-folded" style="display: block">'
        code += '    <a class="collapsible-block-link" href="javascript:;">'
        code += HTMLNode.get_attribute(self.attributes, 'show', '+ открыть блок')
        code += '    </a>'
        code += '  </div>'
        code += '  <div class="collapsible-block-unfolded" style="display: none">'
        code += '    <div class="collapsible-block-unfolded-link">'
        code += '      <a class="collapsible-block-link" href="javascript:;">'
        code += HTMLNode.get_attribute(self.attributes, 'hide', '- закрыть блок')
        code += '      </a>'
        code += '    </div>'
        code += '    <div class="collapsible-block-content">'
        code += super().render(context=context)
        code += '    </div>'
        code += '  </div>'
        code += '</div>'
        return code


class Parser(object):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def parse(self):
        self.tokenizer.position = 0
        root_node = Node()
        root_node.block_node = True
        while True:
            new_children = self.parse_nodes()
            if not new_children:
                break
            for child in new_children:
                root_node.append_child(child)
        return root_node

    def parse_node(self):
        token = self.tokenizer.read_token()
        if token.type == TokenType.Null:
            return None
        elif token.type == TokenType.OpenDoubleBracket:
            pos = self.tokenizer.position
            new_node = self.parse_html_node()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.OpenComment:
            pos = self.tokenizer.position
            new_node = self.parse_comment_node()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.Newline:
            return NewlineNode(False)
        elif token.type == TokenType.DoubleHash:
            pos = self.tokenizer.position
            new_node = self.parse_color_node()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.DoubleAt:
            pos = self.tokenizer.position
            new_node = self.parse_literal()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.OpenHTMLLiteral:
            pos = self.tokenizer.position
            new_node = self.parse_html_literal()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.OpenSingleBracket:
            pos = self.tokenizer.position
            new_node = self.parse_external_link()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.OpenTripleBracket:
            pos = self.tokenizer.position
            new_node = self.parse_internal_link()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.DoubleAsterisk:
            pos = self.tokenizer.position
            new_node = self.parse_strong()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.HrBeginning:
            pos = self.tokenizer.position
            new_node = self.parse_hr()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        elif token.type == TokenType.Plus:
            pos = self.tokenizer.position
            new_node = self.parse_heading()
            if new_node is not None:
                return new_node
            self.tokenizer.position = pos
        return TextNode(token.raw)

    def parse_nodes(self):
        node = self.parse_node()
        if node is None:
            return []
        return [node]

    def parse_html_node(self):
        # [[ has already been parsed
        self.tokenizer.skip_whitespace()
        name_tk = self.tokenizer.read_token()
        if name_tk.type != TokenType.String:
            return None
        name = name_tk.value.lower()
        hack_tags = ['module', 'include', 'iframe', 'collapsible']
        image_tags = ['image', '=image', '>image', '<image', 'f<image', 'f>image']
        if not HTMLNode.node_allowed(name) and name not in image_tags and name not in hack_tags:
            return None
        attributes = []
        children = []
        module_content = ''
        while True:
            self.tokenizer.skip_whitespace()
            attr_name = self.read_as_value_until([TokenType.CloseDoubleBracket, TokenType.Whitespace, TokenType.Equals])
            if attr_name is None:
                return None
            attr_name = attr_name.strip()
            self.tokenizer.skip_whitespace()
            pos = self.tokenizer.position
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.CloseDoubleBracket:
                if attr_name:
                    attributes.append((attr_name, None))
                break
            else:
                # read attribute
                if tk.type != TokenType.Equals:
                    self.tokenizer.position = pos
                    if attr_name:
                        attributes.append((attr_name, None))
                    continue
                # from here, different handling for include. this is a hack in original Wikidot syntax
                if name == 'include':
                    value = ''
                    self.tokenizer.skip_whitespace()
                    while True:
                        tk = self.tokenizer.read_token()
                        if tk.type == TokenType.Null:
                            return None
                        elif tk.type == TokenType.Pipe or tk.type == TokenType.CloseDoubleBracket:
                            if tk.type == TokenType.CloseDoubleBracket:
                                self.tokenizer.position -= 2
                            break
                        value += tk.raw
                    attributes.append((attr_name, value))
                else:
                    self.tokenizer.skip_whitespace()
                    tk = self.tokenizer.read_token()
                    if tk.type != TokenType.String and tk.type != TokenType.QuotedString:
                        self.tokenizer.position = pos
                        continue
                    attributes.append((attr_name, tk.value))
        # include is a special case, it does not have/require ending tag. same for img tags. same for module tags, but not all of them
        if name == 'include' or name == 'iframe' or name in image_tags or (name == 'module' and (not attributes or not ModuleNode.module_has_content(attributes[0][0]))):
            if name == 'include':
                name = attributes[0][0]
                attributes = attributes[1:]
                return IncludeNode(name, attributes)
            elif name == 'iframe':
                url = attributes[0][0]
                attributes = attributes[1:]
                return IframeNode(url, attributes)
            elif name == 'module':
                name = attributes[0][0]
                attributes = attributes[1:]
                return ModuleNode(name, attributes, None)
            else:
                source = attributes[0][0]
                attributes = attributes[1:]
                return ImageNode(name, source, attributes)
        # tag beginning found. now iterate and check for tag ending
        while True:
            pos = self.tokenizer.position
            tk = self.tokenizer.read_token()
            # [[ / <attr_name> ]]
            if tk.type == TokenType.OpenDoubleBracket:
                self.tokenizer.skip_whitespace()
                tk = self.tokenizer.read_token()
                if tk.type == TokenType.Slash:
                    self.tokenizer.skip_whitespace()
                    tk = self.tokenizer.read_token()
                    if tk.type == TokenType.String and tk.value == name:
                        self.tokenizer.skip_whitespace()
                        tk = self.tokenizer.read_token()
                        if tk.type == TokenType.CloseDoubleBracket:
                            # all done!
                            if name == 'module':
                                name = attributes[0][0]
                                attributes = attributes[1:]
                                return ModuleNode(name, attributes, module_content)
                            elif name == 'collapsible':
                                return CollapsibleNode(attributes, children)
                            else:
                                return HTMLNode(name, attributes, children)

            if name != 'module':
                self.tokenizer.position = pos
                new_children = self.parse_nodes()
                if not new_children:  # this means we reached EOF before locating end tag
                    return None
                children += new_children
            else:
                self.tokenizer.position = pos + len(tk.raw or '')
                module_content += tk.raw

    def parse_comment_node(self):
        # [!-- has already been parsed
        content = ''
        while True:
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.CloseComment:
                return CommentNode(content)
            else:
                content += tk.raw

    def parse_color_node(self):
        # ## has already been parsed
        self.tokenizer.skip_whitespace()
        tk = self.tokenizer.read_token()
        if tk.type != TokenType.String:
            return None
        color = tk.value.strip()
        tk = self.tokenizer.read_token()
        if tk.type != TokenType.Pipe:
            return None
        content = ''
        while True:
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.DoubleHash:
                return ColorNode(color, content)
            elif tk.type == TokenType.Null:
                return None
            content += tk.raw

    def parse_literal(self):
        # @@ has already been parsed
        content = ''
        while True:
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.DoubleAt:
                if content == '':
                    return NewlineNode(True)
                return TextNode(content)
            elif tk.type == TokenType.Null:
                return None
            content += tk.raw

    def parse_html_literal(self):
        # @< has already been parsed
        content = ''
        while True:
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.CloseHTMLLiteral:
                if '<' in content or '>' in content:
                    return None
                return HTMLLiteralNode(content)
            elif tk.type == TokenType.Null:
                return None
            content += tk.raw

    def read_as_value_until(self, t):
        text = ''
        while True:
            pos = self.tokenizer.position
            tk = self.tokenizer.read_token()
            if tk.type in t:
                self.tokenizer.position = pos
                return text
            elif tk.type == TokenType.Null:
                return None
            text += tk.raw

    def parse_internal_link(self):
        # [[[ has already been parsed
        self.tokenizer.skip_whitespace()
        article = self.read_as_value_until([TokenType.CloseTripleBracket, TokenType.Pipe])
        if article is None:
            return None
        tk = self.tokenizer.read_token()
        if tk.type == TokenType.CloseTripleBracket:
            # title = article name
            return LinkNode('/'+article, article)
        elif tk.type != TokenType.Pipe:
            return None
        text = ''
        while True:
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.CloseTripleBracket:
                return LinkNode('/'+article, text.strip())
            elif tk.type == TokenType.Null:
                return None
            text += tk.raw

    def parse_external_link(self):
        # [ has already been parsed
        self.tokenizer.skip_whitespace()
        url = ''
        is_text = False
        text = ''
        while True:
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.CloseSingleBracket:
                blank = False
                if url[0:1] == '*':
                    blank = True
                    url = url[1:]
                return LinkNode(url, text.strip(), blank=blank)
            elif tk.type == TokenType.Null:
                return None
            if not is_text:
                if tk.type == TokenType.Whitespace:
                    is_text = True
                else:
                    url += tk.raw
            else:
                text += tk.raw

    def parse_strong(self):
        # ** has already been parsed
        children = []
        while True:
            pos = self.tokenizer.position
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.DoubleAsterisk:
                return HTMLNode('strong', [], children)
            self.tokenizer.position = pos
            new_children = self.parse_nodes()
            if not new_children:
                return None
            children += new_children

    def check_newline(self, size=1):
        prev_pos = self.tokenizer.position - size - 1
        if prev_pos <= 0 or self.tokenizer.source[prev_pos] != '\n':
            return False
        return True

    def parse_hr(self):
        # ---- has already been parsed.
        # we require that there is either strictly no text or a newline.
        # after this token we should have either more hyphens or a newline
        # if anything else, fail
        if not self.check_newline(4):
            return None
        content = self.read_as_value_until([TokenType.Newline])
        if content is None or content.rstrip().replace('-', '') != '':
            return None
        return HorizontalRulerNode()

    def parse_heading(self):
        # + has already been parsed (one)
        # we require one to 6 + then space then heading text
        # if more than 6, invalid input, fail
        if not self.check_newline(1):
            return None
        h_count = 1
        while True:
            tk = self.tokenizer.read_token()
            print(repr(tk))
            if tk.type == TokenType.Plus:
                h_count += 1
            elif tk.type == TokenType.Whitespace:
                break
            else:
                return None
        if h_count > 6:
            return None
        # parse nodes until newline found
        children = []
        while True:
            pos = self.tokenizer.position
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.Newline:
                return HTMLNode('h%d' % h_count, [], children)
            self.tokenizer.position = pos
            new_children = self.parse_nodes()
            if not new_children:
                return None
            children += new_children
