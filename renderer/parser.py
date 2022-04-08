from .tokenizer import TokenType
from django.utils import html


class Node(object):
    def __init__(self):
        self.children = []
        self.parent = None
        self.block_node = False

    def append_child(self, child):
        if type(child) == TextNode and self.children and type(self.children[-1]) == TextNode:
            self.children[-1].text += child.text
            return
        child.parent = self
        self.children.append(child)

    def render(self, context_article=None):
        content = ''
        was_block = True
        was_newline = 1
        was_forced = False
        for child in self.children:
            child_content = child.render(context_article)
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
            elif type(child) == NewlineNode:
                was_newline = 1
                was_forced = False
            # close/open paragraph. ignore newline nodes here
            if type(child) != NewlineNode and self.block_node and child_content:
                if child.block_node and not was_block:
                    content += '</p>'
                elif not child.block_node and was_block:
                    content += '<p>'
                was_block = child.block_node
            content += child_content
        if not was_block:
            content += '</p>'
        return content


class TextNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def render(self, context_article=None):
        if not self.text.strip():
            return ''
        return html.escape(self.text)


class HTMLLiteralNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.force_render = True

    def render(self, context_article=None):
        return self.text.strip()


class NewlineNode(Node):
    def __init__(self, forced):
        super().__init__()
        self.forced = forced

    def render(self, context_article=None):
        if self.parent is not None and (self == self.parent.children[0] or self == self.parent.children[-1]):
            return ''
        return '<br>'


class ColorNode(Node):
    def __init__(self, color, content):
        super().__init__()
        self.color = color
        self.content = content

    def render(self, context_article=None):
        return '<span style="color: #%s">%s</span>' % (html.escape(self.color), html.escape(self.content))


class HTMLNode(Node):
    def __init__(self, name, attributes, children):
        super().__init__()
        self.name = name
        self.attributes = attributes
        self.block_node = self.name in ['div']
        for child in children:
            self.append_child(child)

    def render(self, context_article=None):
        content = super().render(context_article=context_article)
        attr_string = ''
        for attr in self.attributes:
            attr_string += ' '
            attr_string += attr[0]
            if attr[1] is not None:
                attr_string += '="%s"' % html.escape(attr[1])
        return '<%s%s>%s</%s>' % (html.escape(self.name), attr_string, content, html.escape(self.name))


class LinkNode(Node):
    def __init__(self, url, text, blank=False):
        super().__init__()
        self.url = url
        self.text = text
        self.blank = blank

    def render(self, context_article=None):
        blank = ' target="_blank"' if self.blank else ''
        return '<a href="%s"%s>%s</a>' % (html.escape(self.url), blank, html.escape(self.text))


class CommentNode(Node):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def render(self, context_article=None):
        #return '<!-- %s -->' % html.escape(self.text)
        # This is actually not rendered
        return ''


class IncludeNode(Node):
    def __init__(self, name, attributes):
        super().__init__()
        self.name = name
        self.attributes = attributes

    def render(self, context_article=None):
        return '<div>Include is not supported yet</div>'


class ModuleNode(Node):
    def __init__(self, name, attributes, content):
        super().__init__()
        self.name = name.lower()
        self.attributes = attributes
        self.content = content
        self.block_node = True

    def render(self, context_article=None):
        # render only module CSS for now
        if self.name == 'css':
            return '<style>%s</style>' % html.escape(self.content)
        return '<div>Module is not supported yet</div>'


class Parser(object):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def parse(self):
        self.tokenizer.position = 0
        root_node = Node()
        root_node.block_node = True
        while True:
            new_node = self.parse_node()
            if new_node is None:
                break
            root_node.append_child(new_node)
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
        return TextNode(token.raw)

    def parse_html_node(self):
        # [[ has already been parsed
        self.tokenizer.skip_whitespace()
        name_tk = self.tokenizer.read_token()
        if name_tk.type != TokenType.String:
            return None
        name = name_tk.value.lower()
        allowed_tags = ['a', 'span', 'div', 'module', 'include', 'iframe']
        if name not in allowed_tags:
            return None
        attributes = []
        children = []
        module_content = ''
        while True:
            self.tokenizer.skip_whitespace()
            tk = self.tokenizer.read_token()
            if tk.type == TokenType.Null:
                break
            elif tk.type == TokenType.CloseDoubleBracket:
                break
            elif tk.type == TokenType.String:
                pos = self.tokenizer.position
                # read attribute
                attr_name = tk.value
                self.tokenizer.skip_whitespace()
                tk = self.tokenizer.read_token()
                if tk.type != TokenType.Equals:
                    attributes.append((attr_name, None))
                    self.tokenizer.position = pos
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
        # include is a special case, it does not have/require ending tag
        if name == 'include':
            name = attributes[0][0]
            attributes = attributes[1:]
            return IncludeNode(attributes, name)
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
                            return HTMLNode(name, attributes, children)
            if name != 'module':
                self.tokenizer.position = pos
                child = self.parse_node()
                if child is None:  # this means we reached EOF before locating end tag
                    return None
                children.append(child)
            else:
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
            node = self.parse_node()
            if node is None:
                return None
            children.append(node)
