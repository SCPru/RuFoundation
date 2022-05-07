from enum import Enum, unique
import re


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
    Dash = '-'
    Asterisk = '*'
    Plus = '+'
    Newline = '\n'
    Slash = '/'
    Backslash = '\\'

    DoubleAt = '@@'
    DoubleHash = '##'

    OpenHTMLLiteral = '@<'
    CloseHTMLLiteral = '>@'

    DoubleAsterisk = '**'
    DoubleSlash = '//'

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
    def prepare_source(source):
        source = (source or '')\
            .replace('\r\n', '\n')\
            .replace('\r', '\n')\
            .replace('\t', ' ')
        source = re.sub(r'\n{2,}', '\n\n', source)
        source = re.sub(r'\n\s+\n', '\n\n', source)
        source = '\n'.join([x.lstrip(ALL_WHITESPACE_CHARS) for x in source.split('\n')])
        return source

    def __init__(self, source):
        self.source = self.prepare_source(source)
        self.position = 0
        self.special_tokens = get_sorted_special_types()

    def peek_chars(self, num_chars=1):
        return self.source[self.position:self.position+num_chars]

    def read_chars(self, num_chars=1):
        r = self.peek_chars(num_chars)
        self.position += num_chars

    def peek_token(self):
        p = self.position
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
        # check if quoted string
        token = self.try_read_quoted_string()
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

    def try_read_quoted_string(self):
        pos = self.position
        if self.position >= len(self.source) or self.source[self.position] != '"':
            return Token.null()
        raw = '"'
        content = ''
        self.position += 1
        while self.position < len(self.source):
            if self.source[self.position] == '"':
                raw += '"'
                self.position += 1
                break
            content += self.source[self.position]
            raw += self.source[self.position]
            self.position += 1
        if len(raw) > 1 and raw[-1] == '"':
            return Token(raw, TokenType.QuotedString, content)
        else:
            # re-read as string instead. expensive but works for now
            self.position = pos
            return self.read_string(ignore_quote_start=True)

    def read_string(self, ignore_quote_start=False):
        content = ''
        max_special_chars = len(self.special_tokens[0][0])
        while self.position < len(self.source):
            # expensive but works for now (2)
            # -- causes double parsing
            chars = self.peek_chars(max_special_chars)
            if chars[0:1] == '"' and (not ignore_quote_start or content):
                break
            if chars[0:1] in WHITESPACE_CHARS:
                break
            found_subtoken = False
            for value, token_type in self.special_tokens:
                if chars.startswith(value):
                    found_subtoken = True
                    break
            if found_subtoken:
                break
            content += self.source[self.position]
            self.position += 1
        if content:
            return Token(content, TokenType.String, content)
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

    def skip_whitespace(self):
        while self.position < len(self.source):
            if self.source[self.position] not in ALL_WHITESPACE_CHARS:
                break
            self.position += 1

    def inject_code(self, code):
        code = self.prepare_source(code)
        self.source = self.source[:self.position] + code + self.source[self.position:]
