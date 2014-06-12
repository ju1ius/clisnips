import re
from collections import deque
import inspect

from doc_tokens import *


_PATTERN_TYPE = type(re.compile("", 0))
_RE_CACHE = {}
WSP_CHARS = '\t\f\x20'
WSP_RX = re.compile(r'[\t\f ]*')
PARAM_START_RX = re.compile(r'\n[\t\f ]*\{')
IDENT_RX = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
INTEGER_RX = re.compile(r'0|(?:[1-9][0-9]*)')
TYPEHINT_RX = re.compile(r'\(\s*({ident})\s*\)'.format(ident=IDENT_RX.pattern))
DIGIT_RX = re.compile(r'-?[0-9]+(?:\.[0-9]+)?')
STRING_RX = re.compile(r'"((?:[^"]|\\.)*)"')


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

    def lookahead(self, n=1):
#{{{
        pos = self.pos + n
        if pos < self.length:
            return self.text[pos]
#}}}

    def lookbehind(self, n=1):
#{{{
        pos = self.pos - n
        if pos >= 0:
            return self.text[pos]
#}}}

    def advance(self, n=1):
#{{{
        if self.newline_pending:
            self.line += 1
            self.col = -1
        if self.pos + n >= self.length:
            self.char = None
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
#}}}

    def freetext_state(self):
# {{{
        #print "ENTER freetext_state"
        char = self.advance()
        if char is None:
            return False
        elif char == '{':
            t = self.init_token(T_LBRACE, '{')
            self.finalize_token(t)
            self.token_queue.append(t)
            self.state = self.param_state
        else:
            t = self.init_token(T_TEXT)
            text = self._skip_until_param()
            if not text:
                text = self.read_until('$')
            self.finalize_token(t, value=text)
            self.token_queue.append(t)
        return True
# }}}

    def param_state(self):
# {{{
        #print "ENTER param_state"
        while True:
            char = self._skip_whitespace()
            if char.isalpha():
                t = self.init_token(T_IDENT, self.read_until(IDENT_RX))
                self.finalize_token(t)
                self.token_queue.append(t)
            elif char.isdigit():
                t = self.init_token(T_IDENT, self.read_until(DIGIT_RX))
                self.finalize_token(t)
                self.token_queue.append(t)
            elif char == '}':
                t = self.init_token(T_RBRACE, '}')
                self.finalize_token(t)
                self.token_queue.append(t)
                self.state = self.after_param_state
                break
            else:
                self.state = self.freetext_state
                break
        return True
# }}}

    def after_param_state(self):
# {{{
        #print "ENTER after_param_state"
        char = self._skip_whitespace()
        if char == '(':
            m = TYPEHINT_RX.match(self.text, self.pos)
            if m:
                t = self.init_token(T_TYPEHINT, m.group(1))
                self.consume(m.group(0))
                self.finalize_token(t)
                self.token_queue.append(t)
            else:
                self.recede()
                self.state = self.freetext_state
        elif char == '[':
            t = self.init_token(T_LBRACK, '[')
            self.token_queue.append(t)
            self.state = self.valuehint_state
        else:
            self.recede()
            self.state = self.freetext_state
        return True
# }}}

    def valuehint_state(self):
# {{{
        #print "ENTER valuehint_state"
        while True:
            char = self._skip_whitespace()
            if char == ']':
                t = self.init_token(T_RBRACK, ']')
                self.finalize_token(t)
                self.token_queue.append(t)
                self.state = self.freetext_state
                break
            elif char == '"':
                token = self._handle_string()
                if token:
                    self.token_queue.append(token)
                else:
                    self.state = self.freetext_state
                    break
            elif char == ',':
                t = self.init_token(T_COMMA, ',')
                self.finalize_token(t)
                self.token_queue.append(t)
            elif char == '.':
                la = self.lookahead()
                if la == '.':
                    t = self.init_token(T_RANGE_SEP, '..')
                    self.advance()
                    self.finalize_token(t)
                    self.token_queue.append(t)
                #elif la.isdigit():
                    #self.advance()
                    #token = self._handle_digit()
                    #self.token_queue.append(token)
                else:
                    self.state = self.freetext_state
                    break
            elif char == ':':
                t = self.init_token(T_COLON, ':')
                self.token_queue.append(t)
            elif char == '*':
                t = self.init_token(T_STAR, '*')
                self.token_queue.append(t)
            else:
                token = self._handle_digit()
                if token:
                    self.token_queue.append(token)
                    continue
                self.state = self.freetext_state
                break
        return True
# }}}

    def _handle_string(self):
# {{{
        m = STRING_RX.match(self.text, self.pos)
        if not m:
            return
        t = self.init_token(T_STRING, m.group(1))
        self.advance(m.end() - 1 - m.start())
        self.finalize_token(t)
        return t
# }}}

    def _handle_digit(self):
# {{{
        m = DIGIT_RX.match(self.text, self.pos)
        if not m:
            return
        t = self.init_token(T_DIGIT, m.group(0))
        self.advance(m.end() - 1 - m.start())
        self.finalize_token(t)
        return t
# }}}

    def _skip_until_param(self):
# {{{
        m = PARAM_START_RX.search(self.text, self.pos)
        if m:
            text = self.text[self.pos:m.end() - 1]
            self.advance(m.end() - 1 - self.pos - 1)
            return text
        return ''
# }}}

    def _skip_whitespace(self):
# {{{
        char = self.advance()
        if char in WSP_CHARS:
            self.read_until(WSP_RX)
            char = self.advance()
        return char
# }}}
        

if __name__ == "__main__":

    doc = """

    This is the global description of the command.

    It's all text until a parameter is seen.

        {param_1} (file) This is parameter 1
                         It's description continues here
        {param_2} This is parameter 2
                  It's description continues here
    """

    lexer = Lexer(doc)
    for token in lexer:
        print token
