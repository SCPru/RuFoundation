from . import Node
from .html import HTMLNode


class HTMLBaseNode(Node):
    # whether this node should be parsed as text (like in module content or code) or subnodes (everything else)
    is_raw_text = False
    # this is used for user and tab tag, where basically everything after name is single line of text until the end
    is_single_argument = False
    # this is used for include only
    pipe_separated_attributes = False

    @classmethod
    def is_allowed(cls, tag, _parser):
        return False

    @classmethod
    def is_single_tag(cls, _tag, _attributes):
        return False
