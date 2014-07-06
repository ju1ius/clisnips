"""
Unicode words SQLite FTS tokenizer 
"""
from __future__ import print_function, unicode_literals

import sys
import ctypes
from ctypes import POINTER, CFUNCTYPE
import struct
import re


class UnicodeWordsTokenizer(object):

    def __init__(self, min_len=1):
        self.min_len = min_len
        self.regexp = re.compile(r'\w+', re.UNICODE)

    def tokenize(self, input):
        matches = self.regexp.findall(input)
        results = [m for m in matches if len(m) >= self.min_len]
        return iter(results)


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
        tokenizer = _Tokenizer()

        # Create our tokenizer instance
        tokenizer.t = UnicodeWordsTokenizer()

        tokenizers[ctypes.addressof(tokenizer)] = tokenizer
        ppTokenizer[0] = ctypes.pointer(tokenizer)
        return 0

    def xdestroy(pTokenizer):
        del(tokenizers[ctypes.addressof(pTokenizer[0])])
        return 0

    def xopen(pTokenizer, pInput, nInput, ppCursor):
        cur = _TokenizerCursor()
        cur.pTokenizer = pTokenizer
        # turn results of findall into an iterator
        cur.nodes = pTokenizer[0].t.tokenize(pInput.decode('utf-8'))
        cur.pos = 0
        cur.offset = 0
        cursors[ctypes.addressof(cur)] = cur
        ppCursor[0] = ctypes.pointer(cur)
        return 0

    def xnext(pCursor, ppToken, pnBytes,
              piStartOffset, piEndOffset, piPosition):
        try:
            cur = pCursor[0]
            cur_node = next(pCursor[0].nodes)
            token = cur_node.encode('utf-8')
            tokenlen = len(token)
            ppToken[0] = token
            pnBytes[0] = tokenlen
            piStartOffset[0] = cur.offset
            cur.offset += tokenlen
            piEndOffset[0] = cur.offset
            piPosition[0] = cur.pos
            cur.pos += 1
        except StopIteration:
            return 101
        return 0

    def xclose(pCursor):
        del(cursors[ctypes.addressof(pCursor[0])])
        return 0

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
