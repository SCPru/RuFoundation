from .tokenizer import TokenType, StaticTokenizer, Token
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from web import threadvars


User = get_user_model()


class RenderContext(object):
    def __init__(self, article, source_article, path_params, user):
        self.article = article
        self.source_article = source_article
        self.path_params = path_params
        self.user = user or AnonymousUser()
        self.redirect_to = None


class ParseResult(object):
    def __init__(self, context, root):
        self.parser = context.parser
        self.root = root
        self.code_blocks = context.code_blocks


class ParseContext(object):
    def __init__(self, parser, root_node):
        self.parser = parser
        self.code_blocks = []
        self.root = root_node
        self._in_tabview = False


class Parser(object):
    def __init__(self, tokenizer: StaticTokenizer, context=None):
        self.tokenizer = tokenizer
        self.node_cache = dict()
        self._context = context

    def parse(self):
        from .nodes import Node
        from .nodes.root import RootNode
        from .nodes.footnote_block import FootnoteBlockNode

        with threadvars.context():
            self.tokenizer.position = 0

            is_subtree = False

            root_node = RootNode()
            root_node.block_node = True
            if self._context is None:
                context = ParseContext(self, root_node)
                self._context = context
            else:
                is_subtree = True

            threadvars.put('parser_context', self._context)

            self.node_cache = dict()
            while True:
                new_children = self.parse_nodes()
                if not new_children:
                    break
                for child in new_children:
                    root_node.append_child(child)

            self.create_paragraphs(root_node.children)
            root_node.paragraphs_set = True

            if not is_subtree:
                # if there is no footnote block, append it.
                if Node.find_node_recursively(root_node, FootnoteBlockNode) is None:
                    root_node.append_child(FootnoteBlockNode('footnoteblock', [], []))

            # set root for all nodes. this is needed in rendering
            def set_root(node):
                node.root = root_node
                for c in node.children:
                    set_root(c)

            set_root(root_node)

            result = ParseResult(self._context, root_node)
            self._context = None
            return result

    def wrap_text_nodes_in_span(self, node, wrap_with):
        from .nodes.html_literal import HTMLLiteralNode
        from .nodes.text import TextNode

        # node should be a block node. wrap_with should be a span node
        new_nodes = []
        for child in node.children:
            if isinstance(child, TextNode) or isinstance(child, HTMLLiteralNode):
                spanned = wrap_with.clone()
                spanned.parent = node
                spanned.append_child(child)
                new_nodes.append(spanned)
            else:
                self.wrap_text_nodes_in_span(child, wrap_with)
                new_nodes.append(child)
        node.children[:] = new_nodes

    def flatten_inline_node(self, node):
        from .nodes import Node
        from .nodes.html_plain import HTMLPlainNode
        from .nodes.newline import NewlineNode

        if node.trim_paragraphs:
            node.children[:] = Node.strip(node.children)
        self.flatten_inline_nodes(node.children)
        if node.block_node:
            return [node]
        new_nodes = []
        children_so_far = []
        i = -1
        while i < len(node.children)-1:
            i += 1
            child = node.children[i]
            if not child.block_node:
                children_so_far.append(child)
            elif not node.trim_paragraphs and isinstance(child, NewlineNode) and\
                    (i+1 < len(node.children) and not isinstance(node.children[i+1], NewlineNode)) and\
                    (i-1 < 0 or not isinstance(node.children[i-1], NewlineNode)):
                children_so_far.append(child)
            else:
                if children_so_far:
                    new_node = node.clone()
                    for new_child in children_so_far:
                        new_node.append_child(new_child)
                    new_nodes.append(new_node)
                    children_so_far = []
                new_nodes.append(child)
                if isinstance(node, HTMLPlainNode) and node.name == 'span':
                    self.wrap_text_nodes_in_span(child, node)
        if children_so_far:
            new_node = node.clone()
            for new_child in children_so_far:
                new_node.append_child(new_child)
            new_nodes.append(new_node)
        if not new_nodes:
            new_nodes.append(node)
        return new_nodes

    def flatten_inline_nodes(self, nodes):
        new_nodes = []
        for node in nodes:
            new_nodes += self.flatten_inline_node(node)
        nodes[:] = new_nodes[:]

    def create_paragraphs(self, nodes):
        from .nodes import Node
        from .nodes.newline import NewlineNode
        from .nodes.paragraph import ParagraphNode
        from .nodes.text import TextNode

        # flatten inline first
        self.flatten_inline_nodes(nodes)
        #
        new_nodes = []
        last_paragraph = []
        i = -1
        while i < len(nodes)-1:
            i += 1
            node = nodes[i]
            if isinstance(node, NewlineNode):
                new_nodes.append(TextNode('\n'))
            prev_prev_node = nodes[i-2] if i >= 1 else None
            prev_node = nodes[i-1] if i >= 0 else None
            next_node = nodes[i+1] if i+1 < len(nodes) else None
            # generate forced line breaks from <non-\n>\n@@@@.
            # because @@@@ is "inline", it is guaranteed to be on the bottom level
            if TextNode.is_literal(node) and isinstance(prev_node, NewlineNode) and not isinstance(prev_prev_node, NewlineNode):
                if TextNode.is_literal(prev_prev_node) or last_paragraph:
                    last_paragraph.append(NewlineNode(True))
                else:
                    new_nodes.append(NewlineNode(True))
            # the other way around, if we have newline + @@@@, do not render newline. this is needed elsewhere
            if isinstance(node, NewlineNode) and TextNode.is_literal(next_node):
                continue
            # so:
            # if we have newline+newline it's a paragraph
            if (isinstance(node, NewlineNode) and isinstance(next_node, NewlineNode)) or (node.block_node and not isinstance(node, NewlineNode)):
                last_paragraph = Node.strip(last_paragraph)
                if last_paragraph:
                    p_node = ParagraphNode(last_paragraph)
                    last_paragraph = []
                    new_nodes.append(p_node)
                if not isinstance(node, NewlineNode):
                    if not node.paragraphs_set:
                        self.create_paragraphs(node.children)
                        # special handling
                        # if current node is div_, collapse first and last paragraph
                        if node.trim_paragraphs and node.children:
                            if isinstance(node.children[0], ParagraphNode):
                                node.children[0].collapsed = True
                            if isinstance(node.children[-1], ParagraphNode):
                                node.children[-1].collapsed = True
                    new_nodes.append(node)
                else:
                    # double newline, i.e. <p>, skip it for next node
                    i += 1
            else:
                last_paragraph.append(node)
        last_paragraph = Node.strip(last_paragraph)
        if last_paragraph:
            p_node = ParagraphNode(last_paragraph)
            new_nodes.append(p_node)
        nodes[:] = new_nodes[:]
        for node in nodes:
            node.paragraphs_set = True

    def parse_node(self):
        from .nodes import Node
        from .nodes.text import TextNode

        token = self.tokenizer.peek_token()
        if token.type == TokenType.Null:
            return None
        else:
            node = Node.parse(self)
            if node is not None:
                return node
        self.tokenizer.position += 1
        return TextNode(token.raw)

    def parse_nodes(self):
        pos = self.tokenizer.position
        if pos in self.node_cache:
            node = self.node_cache[pos]['node']
            self.tokenizer.position = self.node_cache[pos]['next_pos']
            return [node]
        else:
            node = self.parse_node()
            if node is None:
                return []
            if node.allow_cache:
                self.node_cache[pos] = {'node': node, 'next_pos': self.tokenizer.position}
            return [node]

    def read_simple_arg(self):
        value = self.read_as_value_until([TokenType.CloseDoubleBracket, TokenType.Whitespace])
        if value is None:
            return Token.null()
        return Token(value, TokenType.String, value)

    def read_quoted_arg(self):
        t = self.tokenizer
        pos = t.position
        if t.peek_token().type != TokenType.Quote:
            return self.read_simple_arg()
        raw = '"'
        content = ''
        t.position += 1
        while t.position < len(t.tokens):
            token = t.peek_token()

            if token.type == TokenType.Quote:
                # check if we really want to stop
                # we want to stop, if:
                # - after " we have whitespace then `]]`
                # - after " we have valid attribute name then `=`

                pos2 = t.position
                t.position += 1
                t.skip_whitespace()
                t2 = t.read_token()
                t.skip_whitespace()
                t3 = t.read_token()
                t.position = pos2

                if t2.type == TokenType.Null or t2.type == TokenType.CloseDoubleBracket or\
                        (t2.type == TokenType.String and t3.type == TokenType.Equals) or\
                        t2.type == TokenType.Pipe:
                    raw += '"'
                    t.position += 1
                    break

            elif token.type == TokenType.Newline:
                raw = ''
                break

            content += token.raw
            raw += token.raw
            t.position += 1

        if len(raw) > 1 and raw[-1] == '"':
            return Token(raw, TokenType.QuotedString, content)
        else:
            # re-read as string instead.
            t.position = pos
            return self.read_simple_arg()

    def read_as_value_until(self, t):
        text = ''
        while True:
            pos = self.tokenizer.position
            tk = self.tokenizer.read_token()
            print(repr(tk))
            if tk.type in t:
                self.tokenizer.position = pos
                return text
            elif tk.type == TokenType.Null:
                return None
            text += tk.raw

    def check_whitespace(self, offset):
        prev_pos = self.tokenizer.position+offset
        if prev_pos >= 0 and prev_pos < len(self.tokenizer.tokens):
            tt = self.tokenizer.tokens[prev_pos].type
            return tt == TokenType.Whitespace or tt == TokenType.Newline
        return True

    def check_newline(self, size=1):
        prev_pos = self.tokenizer.position - size - 1
        if prev_pos <= 0:
            return self.tokenizer.position == size
        check_pos = prev_pos
        while check_pos >= 0:
            c = self.tokenizer.tokens[check_pos]
            check_pos -= 1
            if c.type == TokenType.Whitespace:
                continue
            if c.type == TokenType.Newline:
                return True
            return False
        return True

    def parse_subtree(self, code):
        p = Parser(StaticTokenizer(code), context=self._context)
        result = p.parse()
        return result.root.children
