from . import Node
from ..tokenizer import TokenType


class BlockquoteNode(Node):
    starting_token_type = TokenType.Blockquote

    @classmethod
    def parse(cls, p):
        # > has already been parsed
        if not p.check_newline():
            return None

        blockquote_content = ''

        while True:
            tk = p.tokenizer.peek_token()
            if tk.type == TokenType.Null:
                break
            elif tk.type == TokenType.Newline:
                # check if next token is >, if not, break out
                if p.tokenizer.peek_token(offset=1).type != TokenType.Blockquote:
                    break
                else:
                    p.tokenizer.position += 2
                    blockquote_content += '\n'
            else:
                content = p.read_as_value_until([TokenType.Newline, TokenType.Null])
                blockquote_content += content

        # remove one space to the left of blockquote. hack, but wikidot did this.
        blockquote_lines = blockquote_content.split('\n')
        for i in range(len(blockquote_lines)):
            if blockquote_lines[i] and blockquote_lines[i][0] == ' ':
                blockquote_lines[i] = blockquote_lines[i][1:]
        blockquote_content = '\n'.join(blockquote_lines)

        children = p.parse_subtree(blockquote_content)
        return BlockquoteNode(children)

    def __init__(self, children):
        super().__init__()
        self.block_node = True
        self.complex_node = True
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        return self.render_template('<blockquote>{{content}}</blockquote>', content=super().render(context=context))
