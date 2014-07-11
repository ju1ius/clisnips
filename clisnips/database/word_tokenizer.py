"""
Unicode words SQLite FTS tokenizer 
"""
from __future__ import print_function, unicode_literals

import sys
import ctypes
from ctypes import POINTER, CFUNCTYPE
import struct
import re
import unicodedata


SQLITE_OK = 0
SQLITE_DONE = 101


class UnicodeWordsTokenizer(object):
    """
    An FTS tokenizer mimicking the sqlite's unicode61 tokenizer,
    not compiled by default in python's sqlite version.
    """

    def __init__(self, min_len=1):
        pattern = r'\w{%s,}' % min_len
        self.regexp = re.compile(pattern, re.UNICODE)

    def tokenize(self, input_str):
        for m in self.regexp.finditer(input_str):
            orig_token = m.group()
            normalized = self.normalize(orig_token).encode('utf-8')
            start = len(input_str[:m.start()].encode('utf-8'))
            end = start + len(orig_token.encode('utf-8'))
            yield normalized, len(normalized), start, end

    def normalize(self, token):
        token = token.lower()
        nfkd_form = unicodedata.normalize('NFKD', token)
        return ''.join(c for c in nfkd_form if not unicodedata.combining(c))


class _TokenizerModule(ctypes.Structure):
    pass


class _Tokenizer(ctypes.Structure):
    _fields_ = [
        ("pModule", POINTER(_TokenizerModule)),
        ("t", ctypes.py_object)
    ]


class _TokenizerCursor(ctypes.Structure):
    _fields_ = [
        ("pTokenizer", POINTER(_Tokenizer)),
        ("nodes", ctypes.py_object),
        ("offset", ctypes.c_int),
        ("pos", ctypes.c_int)
    ]


_xCreate = CFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    POINTER(ctypes.c_char_p),
    POINTER(POINTER(_Tokenizer))
)

_xDestroy = CFUNCTYPE(
    ctypes.c_int,
    POINTER(_Tokenizer)
)

_xOpen = CFUNCTYPE(
    ctypes.c_int,
    POINTER(_Tokenizer),
    ctypes.c_char_p,
    ctypes.c_int,
    POINTER(POINTER(_TokenizerCursor))
)

_xClose = CFUNCTYPE(
    ctypes.c_int,
    POINTER(_TokenizerCursor)
)

_xNext = CFUNCTYPE(
    ctypes.c_int,
    POINTER(_TokenizerCursor),
    POINTER(ctypes.c_char_p),
    POINTER(ctypes.c_int),
    POINTER(ctypes.c_int),
    POINTER(ctypes.c_int),
    POINTER(ctypes.c_int)
)

_TokenizerModule._fields_ = [
    ("iVersion", ctypes.c_int),
    ("xCreate", _xCreate),
    ("xDestroy", _xDestroy),
    ("xOpen", _xOpen),
    ("xClose", _xClose),
    ("xNext", _xNext)
]


def _make_tokenizer_module():
    tokenizers = {}
    cursors = {}

    def xcreate(argc, argv, ppTokenizer):
        '''
        Create a new tokenizer.

        The values in the argv[] array are the arguments passed
        to the "tokenizer" clause of the CREATE VIRTUAL TABLE statement
        that created the fts3 table.
        For example, if the following SQL is executed:

        CREATE .. USING fts3( ... , tokenizer <tokenizer-name> arg1 arg2)

        then argc is set to 2, and the argv[] array contains pointers
        to the strings "arg1" and "arg2".

        This method should return either SQLITE_OK (0), or an SQLite error 
        code. If SQLITE_OK is returned, then *ppTokenizer should be set
        to point at the newly created tokenizer structure. The generic
        sqlite3_tokenizer.pModule variable should not be initialised by
        this callback. The caller will do so.

        :argc: Size of argv list
        :argv: Tokenizer argument strings
        :ppTokenizer: (OUT) created tokenizer
        '''
        tokenizer = _Tokenizer()

        # Create our tokenizer instance
        tokenizer.t = UnicodeWordsTokenizer()

        tokenizers[ctypes.addressof(tokenizer)] = tokenizer
        ppTokenizer[0] = ctypes.pointer(tokenizer)
        return SQLITE_OK

    def xdestroy(pTokenizer):
        '''
        Destroy an existing tokenizer.
        The fts3 module calls this method exactly once
        for each successful call to xCreate().
        '''
        del(tokenizers[ctypes.addressof(pTokenizer[0])])
        return SQLITE_OK

    def xopen(pTokenizer, pInput, nInput, ppCursor):
        '''
        Create a tokenizer cursor to tokenize an input buffer.
        The caller is responsible for ensuring that the input buffer
        remains valid until the cursor is closed (using the xClose() method).

        :pTokenizer: Tokenizer object
        :pInput: Input Buffer
        :nInput: Size of the input buffer
        :ppCursor: (OUT) Created tokenizer cursor
        '''
        cursor = _TokenizerCursor()
        cursor.pTokenizer = pTokenizer
        # turn results of findall into an iterator
        tokenizer = pTokenizer[0].t
        cursor.nodes = tokenizer.tokenize(pInput.decode('utf-8'))
        cursor.pos = 0
        cursor.offset = 0
        cursors[ctypes.addressof(cursor)] = cursor
        ppCursor[0] = ctypes.pointer(cursor)
        return SQLITE_OK

    def xclose(pCursor):
        '''
        Destroy an existing tokenizer cursor.
        The fts3 module calls this method exactly once
        for each successful call to xOpen().
        '''
        del(cursors[ctypes.addressof(pCursor[0])])
        return SQLITE_OK

    def xnext(pCursor, ppToken, pnBytes,
              piStartOffset, piEndOffset, piPosition):
        '''
        Retrieve the next token from the tokenizer cursor pCursor.
        This method should either return:
          * SQLITE_OK and set the values of the
            "OUT" variables identified below,
          * SQLITE_DONE to indicate that the end of the buffer
            has been reached
          * an SQLite error code.

        `ppToken` should be set to point at a buffer containing the
        normalized version of the token (i.e. after any case-folding and/or
        stemming has been performed).
        
        `pnBytes` should be set to the length of this buffer in bytes.
        The input text that generated the token is identified
        by the byte offsets returned in `piStartOffset` and `piEndOffset`.
        
        `piStartOffset` should be set to the index of the first byte
        of the token in the input buffer.
        
        `piEndOffset` should be set to the index of the first byte
        just past the end of the token in the input buffer.

        The buffer `ppToken` is set to point at is managed by the tokenizer
        implementation. It is only required to be valid until the next call
        to xNext() or xClose(). 

        :pCursor: Tokenizer cursor
        :ppToken: (OUT) Normalized text for token
        :pnBytes: (OUT) Size of the token
        :piStartOffset: (OUT) Byte offset of token in input buffer
        :piEndOffset: (OUT) Byte offset of end of token in input buffer
        :piPosition: (OUT) Number of tokens returned before this one
        '''
        cursor = pCursor[0]
        try:
            token, token_len, start, end = next(cursor.nodes)
        except StopIteration:
            return SQLITE_DONE
        ppToken[0] = token
        pnBytes[0] = token_len
        piStartOffset[0] = start
        piEndOffset[0] = cursor.offset = end 
        piPosition[0] = cursor.pos
        cursor.pos += 1
        return SQLITE_OK

    return _TokenizerModule(
        0,
        _xCreate(xcreate),
        _xDestroy(xdestroy),
        _xOpen(xopen),
        _xClose(xclose),
        _xNext(xnext)
    )


_TOKENIZER_MODULE = _make_tokenizer_module()


def register(con):
    if sys.version_info.major == 2:
        global buffer
    else:
        buffer = lambda x: x
    address_blob = buffer(
        struct.pack("P", ctypes.addressof(_TOKENIZER_MODULE))
    )
    con.execute('SELECT fts3_tokenizer(?, ?)', ('unicode_words', address_blob))
