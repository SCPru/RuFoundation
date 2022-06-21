from . import Node
from .list_item import ListItemNode
from ..tokenizer import TokenType


class ListNode(Node):
    @classmethod
    def parse(cls, p, lstype='ul'):
        # # or * has already been parsed
        if not p.check_newline():
            return None
        if not p.check_whitespace(0):
            return None
        p.tokenizer.skip_whitespace(also_newlines=False)
        token_type = TokenType.Hash if lstype == 'ol' else TokenType.Asterisk
        result = ListNode(lstype)
        result.append_child(ListItemNode())
        append_to = result
        while True:
            tk = p.tokenizer.peek_token()
            if tk.type == TokenType.Newline or tk.type == TokenType.Null:
                append_to = result
                # check if next after newline is list
                p.tokenizer.position += 1
                pos = p.tokenizer.position
                p.tokenizer.skip_whitespace(also_newlines=False)
                whitespace_size = p.tokenizer.position - pos
                tk2 = p.tokenizer.read_token()
                read_next = p.tokenizer.position
                p.tokenizer.position = pos
                if tk2.type != token_type and (tk2.type not in [TokenType.Asterisk, TokenType.Hash] or not whitespace_size):
                    return result
                next_type = 'ul' if tk2.type == TokenType.Asterisk else 'ol'
                # next line is also list line
                p.tokenizer.position = read_next
                for i in range(whitespace_size):
                    if not append_to.children:
                        append_to.append_child(ListItemNode())
                    # last node in append_to must be a ListNode. if not, we should append it.
                    if not append_to.children[-1].children or not isinstance(append_to.children[-1].children[-1], ListNode) or\
                            (i == whitespace_size-1 and append_to.children[-1].children[-1].type != next_type):
                        child_list = ListNode(next_type)
                        append_to.children[-1].append_child(child_list)
                    append_to = append_to.children[-1].children[-1]
                append_to.append_child(ListItemNode())
                p.tokenizer.skip_whitespace(also_newlines=False)
                continue
            new_children = p.parse_nodes()
            if not new_children:
                return result
            for child in new_children:
                append_to.children[-1].append_child(child)

    def __init__(self, lstype):
        super().__init__()
        self.block_node = True
        self.type = lstype
        self.paragraphs_set = True

    def render(self, context=None):
        tag = self.type
        output = '<%s>' % tag
        for child in self.children:
            output += '<li>'
            output += child.render(context)
            output += '</li>'
        output += '</%s>' % tag
        return output
