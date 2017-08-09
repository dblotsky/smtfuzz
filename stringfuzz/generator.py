import re

from stringfuzz.constants import SMT_20, SMT_20_STRING, SMT_25_STRING
from stringfuzz.scanner import scan, ALPHABET, WHITESPACE
from stringfuzz.ast import *

__all__ = [
    'generate',
    'generate_file',
]

# exceptions
class NotSupported(ValueError):
    def __init__(self, e, language):
        message = 'can\'t generate {!r} in language {!r}'.format(e, language)
        super(NotSupported, self).__init__(message)

# functions
def needs_encoding(c):
    return c not in ALPHABET

def encode_char(c, language):
    if c == '"':
        if language == SMT_25_STRING:
            return '""'
        else:
            return '\\"'
    elif c == '\\':
        return '\\\\'
    elif c in WHITESPACE:
        return repr(c)
    elif needs_encoding(c):
        return '\\x{:0>2x}'.format(ord(c))
    return c

def encode_string(s, language):
    encoded = ''.join(encode_char(c, language) for c in s)
    return '"' + encoded + '"'

def generate_node(node, language):

    # generate each known node
    if isinstance(node, ExpressionNode):
        return generate_expr(node, language)

    elif isinstance(node, LiteralNode):
        return generate_lit(node, language)

    elif isinstance(node, IdentifierNode):
        return node.name

    elif isinstance(node, SortNode):
        return node.sort

    elif isinstance(node, ArgsNode):
        return '()'

    # error out on all others
    else:
        raise NotImplementedError('no generator for {}'.format(type(node)))

def generate_lit(lit, language):
    if isinstance(lit, StringLitNode):
        return encode_string(lit.value, language)

    elif isinstance(lit, BoolLitNode):
        return str(lit.value).lower()

    elif isinstance(lit, IntLitNode):
        return str(lit.value)

    else:
        raise NotImplementedError('unknown literal type {!r}'.format(lit))

def generate_expr(e, language):
    components = []

    # special expressions
    if isinstance(e, ConcatNode):
        if language == SMT_20_STRING:
            components.append('Concat')
        elif language == SMT_25_STRING:
            components.append('str.++')
        else:
            raise NotSupported(e, language)

    elif isinstance(e, AtNode):
        if language == SMT_20_STRING:
            components.append('CharAt')
        elif language == SMT_25_STRING:
            components.append('str.at')
        else:
            raise NotSupported(e, language)

    elif isinstance(e, LengthNode):
        if language == SMT_20_STRING:
            components.append('Length')
        elif language == SMT_25_STRING:
            components.append('str.len')
        else:
            raise NotSupported(e, language)

    # all other expressions
    else:
        components.append(e.symbol)

    # generate args
    components.extend(generate_node(node, language) for node in e.body)

    return '({})'.format(' '.join(components))

# public API
def generate_file(ast, language, path):
    with open(path, 'w+') as file:
        file.write(generate(ast, language))

def generate(ast, language):
    return '\n'.join(generate_expr(e, language) for e in ast)
