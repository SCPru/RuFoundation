import copy

from .. import utils
from ..tokenizer import WHITESPACE_CHARS
import threading
import pkgutil
import sys
import logging
from web import threadvars


from ..parser import Parser


AST_VERSION = 6

NODE_CLASSES = None
_NODE_CLASSES_LOCK = threading.RLock()


class Node(object):
    starting_token_type = None

    def __init__(self):
        self.children = []
        self.parent = None
        self.root = None
        # Block node is a node that will always close current paragraph
        self.block_node = False
        # Complex node is a node that prevents treating the line as plain text paragraph
        # (based on Wikidot's weird treating of lines that start with [[, [, or something similar)
        self.complex_node = False
        # This enforces newlines for literals
        self.force_render = False
        # This handles [[div_]] hack (and [[span_]], and god knows what else)
        self.trim_paragraphs = False
        # Internal
        self.paragraphs_set = False
        # Some things are bad to cache. For example tables, where trying to cache it from the middle can cause partial structure to be parsed.
        self.allow_cache = True

    @classmethod
    def get_node_classes(cls):
        with _NODE_CLASSES_LOCK:
            global NODE_CLASSES
            if NODE_CLASSES is None:
                NODE_CLASSES = []
                package = sys.modules[__name__]
                for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                    if ispkg:
                        continue
                    try:
                        fullname = 'renderer.nodes.%s' % modname
                        if fullname in sys.modules:
                            m = sys.modules[fullname]
                        else:
                            m = importer.find_module(fullname).load_module(fullname)
                    except:
                        logging.error('Failed to load module \'%s\':', modname.lower(), exc_info=True)
                        continue
                    # look for classes inside the module. should inherit Node
                    for k in m.__dict__:
                        v = m.__dict__[k]
                        if isinstance(v, type) and issubclass(v, Node) and v not in NODE_CLASSES:
                            NODE_CLASSES.append(v)
        return NODE_CLASSES

    @classmethod
    def parse(cls, p: Parser):
        node_classes = cls.get_node_classes()
        pos = p.tokenizer.position
        t = p.tokenizer.read_token()
        for f_cls in node_classes:
            # I'm not sure if this does what I think it does
            if f_cls == cls or f_cls.parse == cls.parse:
                continue
            if f_cls.starting_token_type is None or f_cls.starting_token_type != t.type:
                continue
            node = f_cls.parse(p)
            if node:
                return node
            break
        p.tokenizer.position = pos
        return None

    def clone(self):
        new_node = copy.copy(self)
        new_node.children = []
        return new_node

    def append_child(self, child):
        from .text import TextNode

        if isinstance(child, TextNode) and self.children and isinstance(self.children[-1], TextNode)\
                and child.literal == self.children[-1].literal:
            self.children[-1].text += child.text
            return
        child.parent = self
        child.root = self.root
        self.children.append(child)

    @staticmethod
    def whitespace_node(child):
        from .text import TextNode
        from .newline import NewlineNode
        from .comment import CommentNode

        if child.force_render:
            return False
        return isinstance(child, NewlineNode) or (isinstance(child, TextNode) and not child.text.strip(WHITESPACE_CHARS)) or isinstance(child, CommentNode)

    @staticmethod
    def is_only_whitespace(children):
        for child in children:
            if not Node.whitespace_node(child):
                return False
        return True

    @staticmethod
    def strip(children):
        if not children:
            return []
        # this deletes leading and trailing newline (not whitespace though)
        first_non_whitespace = 0
        last_non_whitespace = len(children)
        any_non_whitespace = False
        for i in range(len(children)):
            child = children[i]
            if not Node.whitespace_node(child):
                first_non_whitespace = i
                any_non_whitespace = True
                break
        for i in reversed(range(len(children))):
            child = children[i]
            if not Node.whitespace_node(child):
                last_non_whitespace = i
                any_non_whitespace = True
                break
        if not any_non_whitespace:
            return []
        else:
            return children[first_non_whitespace:last_non_whitespace+1]

    @staticmethod
    def find_node_recursively(root, node_type):
        def find_node(node):
            for child in node.children:
                if type(child) == node_type:
                    return child
                found = find_node(child)
                if found is not None:
                    return found

        return find_node(root)

    @staticmethod
    def find_nodes_recursively(root, node_type):
        lst = []

        def find_node(node):
            for child in node.children:
                if type(child) == node_type:
                    lst.append(child)
                find_node(child)

        find_node(root)
        return lst

    @classmethod
    def render_template(cls, template, **context):
        return utils.render_template_from_string(template, **context)

    def pre_render(self, context=None):
        pass

    def render(self, context=None):
        for node in self.children:
            node.pre_render(context=context)
        return self.render_template(
            '{% for node in nodes %}{{ node }}{% endfor %}',
            nodes=self.children
        )

    def plain_text(self, context=None):
        for node in self.children:
            node.pre_render(context=context)
        text = ''
        for node in self.children:
            text += node.plain_text(context=context)
        return text

    def __str__(self):
        context = threadvars.get('render_context', None)
        return self.render(context=context)

    def to_json(self):
        base = {'__ClassType': str(type(self)), '__ASTVersion': AST_VERSION, 'children': [x.to_json() for x in self.children]}
        for k in self.__dict__:
            if k in ['parent', 'children', 'root']:
                continue
            base[k] = self.__dict__[k]
        return base

    @classmethod
    def _unpack_object(cls, obj, root=None):
        if obj.get('__ASTVersion') != AST_VERSION:
            raise TypeError('Invalid AST Version %d (current: %d)' % (obj['__ASTVersion'], AST_VERSION))
        node_cls = None
        node_classes = cls.get_node_classes()
        for c in node_classes:
            if str(c) == obj.get('__ClassType'):
                node_cls = c
                break
        if node_cls is None:
            raise TypeError('Unknown node type \'%s\' in AST' % obj.get('type'))
        node = node_cls.__new__(node_cls)
        for k in obj:
            if k in ['__ClassType', 'children', '__ASTVersion']:
                continue
            node.__dict__[k] = obj[k]
        node.__dict__['children'] = []
        if root is None:
            root = node
        node.root = root
        for child_obj in obj.get('children', []):
            child_node = cls._unpack_object(child_obj, root=root)
            node.append_child(child_node)
        return node

    @classmethod
    def from_json(cls, root_object):
        return cls._unpack_object(root_object)
