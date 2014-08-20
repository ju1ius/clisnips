import re
from collections import deque
import inspect

from doc_tokens import *


_PATTERN_TYPE = type(re.compile("", 0))
_RE_CACHE = {}

WSP_CHARS = '\t\f\x20'
WSP_RX = re.compile(r'[\t\f ]*')

PARAM_START_RX = re.compile(r'^[\t\f ]*(?=\{)', re.MULTILINE)
CODEBLOCK_START_RX = re.compile(r'^[\t\f ]*(?=```$)', re.MULTILINE)
FREETEXT_BOUNDS_RX = re.compile(
    r'''
        ^               # start of string or line
        [\x20\t\f]*     # any whitespace except newline
        (?=             # followed by
            {           # parameter start char
            |           # or
            ```$        # codeblock start marker
        )
    ''',
    re.MULTILINE | re.X
)

IDENT_RX = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
FLAG_RX = re.compile(r'--?[a-zA-Z0-9][\w-]*')
PARAM_RX = re.compile(r'(\d+)|({ident})'.format(ident=IDENT_RX.pattern))
INTEGER_RX = re.compile(r'\d+')
FLOAT_RX = re.compile(r'\d*\.\d+')
TYPEHINT_RX = re.compile(r'\(\s*({ident})\s*\)'.format(ident=IDENT_RX.pattern))
DIGIT_RX = re.compile(
    r'-?(?:({float})|({int}))'.format(float=FLOAT_RX.pattern,
                                      int=INTEGER_RX.pattern)
)
STRING_RX = re.compile(r'"((?:\\"|[^"])*)"')
DSTR_RX = re.compile(r'"(?:\\.|[^"])*"')
SSTR_RX = re.compile(r"'(?:\\.|[^'])*'")
TSTR_RX = re.compile(r'(\'\'\'|""")(?:\\.|[^\\])*\1')


class StringLexer(object):
    """
    A simple String lexer
    """

    def __init__(self, text=None):
        if text is not None:
            self.set_text(text)

    def set_text(self, text):
#{{{
        self.text = text
        self.length = len(self.text)
        self.reset()
#}}}

    def reset(self):
#{{{
        self.pos = -1
        self.col = -1
        self.line = 0
        self.char = None
        self.newline_pending = False
#}}}

    def lookahead(self, n=1, accumulate=False):
#{{{
        pos = self.pos + n
        if pos < self.length:
            if accumulate:
                return self.text[self.pos+1:pos+1]
            return self.text[pos]
        if accumulate:
            return self.text[self.pos+1:]
#}}}

    def lookbehind(self, n=1, accumulate=False):
#{{{
        pos = self.pos - n
        if pos >= 0:
            if accumulate:
                return self.text[pos:self.pos]
            return self.text[pos]
        if accumulate:
            return self.text[:self.pos]
#}}}

    def advance(self, n=1):
#{{{
        if self.newline_pending:
            self.line += 1
            self.col = -1
        if self.pos + n >= self.length:
            self.char = None
            self.pos = self.length
            return self.char
        if n == 1:
            self.pos += 1
            self.col += 1
            self.char = self.text[self.pos]
            #self.newline_pending = "\n" == self.char
            return self.char
        text = self.text
        old_pos = self.pos
        new_pos = old_pos + n
        # count newlines between:
        # oldpos (+1 since it should have been handled by self.newline_pending)
        # and newpos (not -1 since we will set the last to be pending)
        line_count = text.count("\n", old_pos, new_pos + 1)
        #print text[old_pos:new_pos+1], line_count
        if line_count > 0:
            last_line_pos = text.rfind("\n", old_pos, new_pos + 1)
            #print last_line_pos
            self.line += line_count
            self.col = new_pos - last_line_pos
        else:
            self.col += n
        self.pos = new_pos
        self.char = text[new_pos]
        #self.newline_pending = "\n" == self.char
        return self.char
#}}}

    def recede(self, n=1):
#{{{
        if self.pos - n < 0:
            self.char = None
            return self.char
        old_pos = self.pos
        text = self.text
        new_pos = self.pos - n
        # count newlines between:
        # new_pos and old_pos (not+1 since it has been handled by advance
        # already)
        line_count = text.count("\n", new_pos, old_pos)
        #print old_pos, new_pos, line_count, text[new_pos:old_pos+1]
        if line_count > 0:
            self.line -= line_count
            first_line_pos = text.find("\n", new_pos, old_pos)
            self.col = old_pos - first_line_pos - 1
            if first_line_pos == new_pos:
                self.col += 1
        else:
            self.col -= n
        self.pos = new_pos
        self.char = text[new_pos]
        return self.char
#}}}

    def read(self, n=1):
#{{{
        startpos = self.pos
        la = self.advance(n)
        if la is None:
            return None
        return self.text[startpos:self.pos + 1]
#}}}

    def unread(self, n=1):
#{{{
        endpos = self.pos
        la = self.recede(n)
        if la is None:
            return None
        return self.text[self.pos:endpos + 1]
#}}}

    def consume(self, string):
        self.advance(len(string))

    def unconsume(self, string):
        self.recede(len(string))

    def read_until(self, pattern, negate=True, accumulate=True):
        """
        Consumes the input string until we find a match for pattern
        """
#{{{
        if not isinstance(pattern, _PATTERN_TYPE):
            cache_key = (pattern, negate)
            if cache_key not in _RE_CACHE:
                neg = '^' if negate else ''
                _RE_CACHE[cache_key] = re.compile(r'[%s%s]+' % (neg, pattern))
            pattern = _RE_CACHE[cache_key]
        m = pattern.match(self.text, self.pos)
        if m:
            self.advance(m.end() - 1 - m.start())
            return m.group(0)
        return ''
#}}}


class Lexer(StringLexer):

    def __init__(self, text):
        super(Lexer, self).__init__(text)
        self.state = self.freetext_state

    def __iter__(self):
#{{{
        self.token_queue = deque()
        while True:
            if not self.state():
                yield Token(T_EOF, self.line, self.col)
                break
            while self.token_queue:
                token = self.token_queue.popleft()
                yield token
#}}}

    def init_token(self, type, value=None):
# {{{
        token = Token(type, self.line, self.col, value)
        token.startpos = self.pos
        return token
# }}}

    def finalize_token(self, token, line=None, col=None, pos=None, value=None):
#{{{
        #caller = inspect.stack()[1][2:4]
        #if caller[1] in ('flush_attr_stack', 'emit_tokens'):
            #caller = inspect.stack()[2][2:4]
        #print "Finalize(from %s:%s)-> %s (char: %s, line: %s, col: %s)" % (
            #caller[1],caller[0],token,self.char,self.line,self.col
        #)
        if value is not None:
            token.value = value
        token.endpos = pos if pos is not None else self.pos
        token.endline = line if line is not None else self.line
        token.endcol = col if col is not None else self.col
        return token
#}}}

    def freetext_state(self):
# {{{
        #print "ENTER freetext_state"
        char = self.advance()
        if char is None:
            return False
        if char == '{':
            token = self.init_token(T_LBRACE, '{')
            self.finalize_token(token)
            self.token_queue.append(token)
            self.state = self.param_state
            return True
        if char == '`':
            if self.lookahead(2, True) == '``':
                token = self.init_token(T_CODEMARK, '```')
                self.advance(2)
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.codeblock_state
                return True
        token = self.init_token(T_TEXT)
        text = self._consume_freetext()
        if not text:
            text = self.read_until('$')
        self.finalize_token(token, value=text)
        self.token_queue.append(token)
        return True
# }}}

    def param_state(self):
# {{{
        #print "ENTER param_state"
        while True:
            char = self._skip_whitespace()
            if char == '}':
                token = self.init_token(T_RBRACE, '}')
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.after_param_state
                break 
            if char.isalnum() or char == '_':
                token = self._handle_param_identifier()
                if not token:
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
            elif char == '-':
                token = self._handle_flag()
                if not token:
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
            else:
                self.state = self.freetext_state
                break
        return True
# }}}

    def after_param_state(self):
# {{{
        #print "ENTER after_param_state"
        char = self._skip_whitespace()
        if char is None:
            return False
        if char == '(':
            token = self.init_token(T_LPAREN, '(')
            self.token_queue.append(token)
            self.state = self.typehint_state
            return True
        if char == '[':
            token = self.init_token(T_LBRACK, '[')
            self.token_queue.append(token)
            self.state = self.valuehint_state
            return True
        self.recede()
        self.state = self.freetext_state
        return True
# }}}

    def typehint_state(self):
# {{{
        while True:
            char = self._skip_whitespace()
            if char is None:
                return False
            if char == ')':
                token = self.init_token(T_RPAREN, ')')
                self.token_queue.append(token)
                self.state = self.after_param_state
                break
            m = IDENT_RX.match(self.text, self.pos)
            if not m:
                self.recede()
                self.state = self.freetext_state
                break 
            token = self.init_token(T_IDENTIFIER, m.group(0))
            self._consume_match(m)
            self.finalize_token(token)
            self.token_queue.append(token)
        return True
# }}}

    def valuehint_state(self):
# {{{
        #print "ENTER valuehint_state"
        while True:
            char = self._skip_whitespace()
            if char is None:
                return False
            if char == ']':
                token = self.init_token(T_RBRACK, ']')
                self.finalize_token(token)
                self.token_queue.append(token)
                self.state = self.freetext_state
                break
            elif char == '"':
                token = self._handle_quoted_string()
                if not token:
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
            elif char == ',':
                token = self.init_token(T_COMMA, ',')
                self.finalize_token(token)
                self.token_queue.append(token)
            elif char == ':':
                token = self.init_token(T_COLON, ':')
                self.token_queue.append(token)
            elif char == '*':
                token = self.init_token(T_STAR, '*')
                self.token_queue.append(token)
            else:
                token = self._handle_digit()
                if not token:
                    self.recede()
                    self.state = self.freetext_state
                    break
                self.token_queue.append(token)
        return True
# }}}

    def codeblock_state(self):
# {{{
        code = self.init_token(T_TEXT, '')
        while True:
            code.value += self.read_until(r'"\'`')
            char = self.advance()
            if not char:
                self.finalize_token(code)
                self.token_queue.append(code)
                return False
            if char == '"':
                if self.lookahead(2, True) == '""':
                    m = TSTR_RX.match(self.text, self.pos)
                    if m:
                        code.value += m.group(0)
                        self._consume_match(m)
                    else:
                        code.value += char
                    continue
                m = DSTR_RX.match(self.text, self.pos)
                if m:
                    code.value += m.group(0)
                    self._consume_match(m)
                else:
                    code.value += char
            elif char == "'":
                if self.lookahead(2, True) == "''":
                    m = TSTR_RX.match(self.text, self.pos)
                    if m:
                        code.value += m.group(0)
                        self._consume_match(m)
                    else:
                        code.value += char
                    continue
                m = SSTR_RX.match(self.text, self.pos)
                if m:
                    code.value += m.group(0)
                    self._consume_match(m)
                else:
                    code.value += char
            elif char == '`':
                if self.lookahead(2, True) == '``':
                    self.finalize_token(code)
                    self.token_queue.append(code)
                    token = self.init_token(T_CODEMARK, '```')
                    self.advance(2)
                    self.finalize_token(token)
                    self.token_queue.append(token)
                    self.state = self.freetext_state
                    break 
                code.value += char
        return True
# }}}

    def _handle_param_identifier(self):
# {{{
        m = PARAM_RX.match(self.text, self.pos)
        if not m:
            return
        if m.group(1):
            _type = T_INTEGER
        elif m.group(2):
            _type = T_IDENTIFIER
        token = self.init_token(_type, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)
# }}}

    def _handle_flag(self):
# {{{
        m = FLAG_RX.match(self.text, self.pos)
        if not m:
            return
        token = self.init_token(T_FLAG, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)
# }}}

    def _handle_quoted_string(self):
# {{{
        m = STRING_RX.match(self.text, self.pos)
        if not m:
            return
        token = self.init_token(T_STRING, m.group(1))
        self._consume_match(m)
        return self.finalize_token(token)
# }}}

    def _handle_digit(self):
# {{{
        m = DIGIT_RX.match(self.text, self.pos)
        if not m:
            print self.text[self.pos:]
            return
        if m.group(1):
            _type = T_FLOAT
        elif m.group(2):
            _type = T_INTEGER
        token = self.init_token(_type, m.group(0))
        self._consume_match(m)
        return self.finalize_token(token)
# }}}

    def _consume_freetext(self):
# {{{
        m = FREETEXT_BOUNDS_RX.search(self.text, self.pos)
        if not m:
            return ''
        end = m.end()
        text = self.text[self.pos:end]
        self.advance(end - self.pos - 1)
        return text
# }}}

    def _skip_whitespace(self):
# {{{
        char = self.advance()
        if char is None:
            return None
        if char in WSP_CHARS:
            self.read_until(WSP_RX)
            char = self.advance()
        return char
# }}}

    def _consume_match(self, match, group=0):
# {{{
        if not match:
            return
        self.advance(match.end(group) - 1 - match.start(group))
        return match.group(group)
# }}}
