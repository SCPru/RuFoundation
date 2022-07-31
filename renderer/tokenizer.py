from enum import Enum, unique
import re
from django.conf import settings


WHITESPACE_CHARS = ' \u00a0'
ALL_WHITESPACE_CHARS = WHITESPACE_CHARS + '\r\n\t'


@unique
class TokenType(Enum):
    Null = -1

    String = 0
    QuotedString = 1
    Whitespace = 2

    OpenSingleBracket = '['
    CloseSingleBracket = ']'
    OpenDoubleBracket = '[['
    CloseDoubleBracket = ']]'
    OpenTripleBracket = '[[['
    CloseTripleBracket = ']]]'

    OpenComment = '[!--'
    CloseComment = '--]'

    Equals = '='
    Pipe = '|'
    Asterisk = '*'
    Hash = '#'
    Plus = '+'
    Newline = '\n'
    Slash = '/'
    Backslash = '\\'
    Tilde = '~'
    Underline = '_'

    Quote = '"'

    Blockquote = '>'

    DoubleAt = '@@'
    DoubleHash = '##'

    DoublePipe = '||'

    DoubleSup = '^^'
    DoubleSub = ',,'

    OpenHTMLLiteral = '@<'
    CloseHTMLLiteral = '>@'

    OpenInlineCode = '{{'
    CloseInlineCode = '}}'

    DoubleDash = '--'
    DoubleAsterisk = '**'
    DoubleSlash = '//'
    DoubleUnderline = '__'

    HrBeginning = '----'


def get_sorted_special_types():
    types = []
    for name, member in TokenType.__members__.items():
        if type(member.value) != str:
            continue
        types.append((member.value, member))
    types.sort(key=lambda x: len(x[0]), reverse=True)
    return types


class Token(object):
    def __init__(self, raw, t, value):
        self.raw = raw
        self.type = t
        self.value = value

    def __repr__(self):
        return '<Token type=%s, raw=%s>' % (repr(self.type), repr(self.raw))

    @staticmethod
    def null():
        return Token(None, TokenType.Null, None)


class Tokenizer(object):
    @staticmethod
    def smart_strip(line):
        line = line.rstrip()
        if not line.strip(ALL_WHITESPACE_CHARS):
            return ''
        first_non_space = re.search(r'[^%s]' % re.escape(ALL_WHITESPACE_CHARS), line)
        if first_non_space:
            first_non_space = first_non_space.start()
        else:
            first_non_space = 0
        line = (' ' * first_non_space) + line[first_non_space:]
        return line

    @staticmethod
    def prepare_source(source):
        source = (source or '')\
            .strip(ALL_WHITESPACE_CHARS)\
            .replace('\r\n', '\n')\
            .replace('\r', '\n')\
            .replace('\t', ' ')
        source = re.sub(r'\n{2,}', '\n\n', source)
        source = re.sub(r'\n\s+\n', '\n\n', source)
        source = '\n'.join([Tokenizer.smart_strip(x) for x in source.split('\n')])
        # to-do: delete this shit at some point
        for k, v in settings.ARTICLE_REPLACE_CONFIG.items():
            source = source.replace(k, v)
        return source

    def __init__(self, source):
        self.source = self.prepare_source(source)
        self.position = 0
        self.special_tokens = get_sorted_special_types()
        self.not_string_regex =\
            re.compile('^(.*?)(' + '|'.join([re.escape(x[0]) for x in self.special_tokens]) + '|' + '|'.join([re.escape(x) for x in ALL_WHITESPACE_CHARS]) + '|$)')

    def peek_chars(self, num_chars=1):
        return self.source[self.position:self.position+num_chars]

    def read_chars(self, num_chars=1):
        r = self.peek_chars(num_chars)
        self.position += num_chars

    def peek_token(self, offset=0):
        p = self.position
        self.position += offset
        token = self.read_token()
        self.position = p
        return token

    def read_token(self):
        # check if special token type. if so, add and exit
        first_chars = self.peek_chars(len(self.special_tokens[0][0]))
        for value, token_type in self.special_tokens:
            if first_chars.startswith(value):
                t = Token(value, token_type, value)
                self.position += len(value)
                return t
        # check if whitespace. this is basically only spaces
        token = self.try_read_whitespace()
        if token.type != TokenType.Null:
            return token
        # read plaintext otherwise until anything non-plaintext is found
        return self.read_string()

    def try_read_whitespace(self):
        content = ''
        while self.position < len(self.source):
            if self.source[self.position] in WHITESPACE_CHARS:
                content += self.source[self.position]
            else:
                break
            self.position += 1
        if content:
            return Token(content, TokenType.Whitespace, content)
        return Token.null()

    def read_string(self):
        #
        match = self.not_string_regex.match(self.source[self.position:])[1]
        self.position += len(match)
        if match:
            return Token(match, TokenType.String, match)
        return Token.null()

    def read_all_tokens(self):
        pos = self.position
        tokens = []
        self.position = 0
        while True:
            token = self.read_token()
            if token.type != TokenType.Null:
                tokens.append(token)
            else:
                break
        self.position = pos
        return tokens

    def skip_whitespace(self, chars=ALL_WHITESPACE_CHARS):
        while self.position < len(self.source):
            if self.source[self.position] not in chars:
                break
            self.position += 1


class StaticTokenizer(object):
    def __init__(self, source):
        t = Tokenizer(source)
        raw_tokens = t.read_all_tokens()
        # hack: convert >@@ from ">@", "@" into ">" and "@@"
        new_tokens = []
        for i in range(len(raw_tokens)):
            if raw_tokens[i].type == TokenType.CloseHTMLLiteral\
                    and i+1 < len(raw_tokens) and raw_tokens[i+1].raw\
                    and raw_tokens[i+1].type != TokenType.OpenHTMLLiteral and raw_tokens[i+1].raw[0] == '@':
                new_tokens.append(Token('>', TokenType.String, '>'))
                new_tokens.append(Token('@@', TokenType.DoubleAt, '@@'))
                raw_tokens[i+1].raw = raw_tokens[i+1].raw[1:]
            else:
                new_tokens.append(raw_tokens[i])
        self.tokens = new_tokens
        self.position = 0

    def read_token(self):
        t = self.peek_token()
        if t.type != TokenType.Null:
            self.position += 1
        return t

    def peek_token(self, offset=0):
        pos = self.position+offset
        if pos >= 0 and pos < len(self.tokens):
            return self.tokens[pos]
        return Token.null()

    def skip_whitespace(self, also_newlines=True):
        while self.position < len(self.tokens):
            if self.tokens[self.position].type != TokenType.Whitespace and\
                    (self.tokens[self.position].type != TokenType.Newline or not also_newlines):
                break
            self.position += 1

    def read_all_tokens(self):
        return list(self.tokens[:])
