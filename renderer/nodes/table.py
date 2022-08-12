from . import Node
from .html_plain import HTMLPlainNode
from .newline import NewlineNode
from ..tokenizer import TokenType


class TableNode(Node):
    starting_token_type = TokenType.DoublePipe

    @classmethod
    def parse(cls, p):
        # || has already been parsed
        if not p.check_newline():
            return None
        rows = []
        table_complete = False
        while not table_complete:
            # read row until newline
            row = []
            col_type = 'td'
            col_content = []
            col_span = 1
            col_align = 'left'
            while True:
                pos = p.tokenizer.position
                tk = p.tokenizer.read_token()
                if tk.type == TokenType.DoublePipe:
                    if col_content:
                        col_attrs = \
                            ([('colspan', col_span)] if col_span > 1 else []) +\
                            ([('style', 'text-align: %s' % col_align)] if col_align != 'left' else [])
                        row.append(HTMLPlainNode(col_type, col_attrs, col_content, True))
                        col_content = []
                        col_type = 'td'
                    else:
                        col_span += 1
                elif tk.type == TokenType.Underline:
                    if p.tokenizer.peek_token().type == TokenType.Newline:
                        col_content.append(NewlineNode())
                        p.tokenizer.position += 1
                elif tk.type == TokenType.Newline:
                    if p.tokenizer.peek_token().type != TokenType.DoublePipe:
                        table_complete = True
                        p.tokenizer.position -= 1
                    else:
                        p.tokenizer.position += 1
                    break
                elif tk.type == TokenType.Tilde and not col_content:
                    col_type = 'th'
                elif tk.type == TokenType.Equals and not col_content:
                    col_align = 'center'
                else:
                    p.tokenizer.position = pos
                    new_children = p.parse_nodes()
                    if not new_children:
                        table_complete = True
                        break
                    col_content += new_children
            rows.append(HTMLPlainNode('tr', [], row, True, True))
        table_node = HTMLPlainNode('table', [('class', 'wiki-content-table')], rows)
        table_node.allow_cache = False
        return table_node
