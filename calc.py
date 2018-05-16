#!/usr/bin/python3

import re
from functools import reduce
from enum import Enum, auto
import readline

MILES_PER_KM = 0.621371

class State(Enum):
    INITIAL = auto()
    NUMBER = auto()
    TIME = auto()
    OPS = auto()

class BaseError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

    def __str__(self):
        name = type(self).__name__
        words = re.findall(r'[A-Z][^A-Z]*', name)
        desc = reduce(lambda x, y: x + ' ' + y, words)
        
        return '{:s}: {:s}'.format(desc, self.msg)

class SyntaxError(BaseError):
    pass

class EvalError(BaseError):
    pass

class Token():
    def __init__(self, s):
        self.s = s
        
    def __str__(self):
        return self.s
    
class Number(Token):
    def __init__(self, s):
        super().__init__(s)
        self.val = float(s)

    def __str__(self):
        return '{:0.2f}'.format(self.val)

class Time(Token):
    def __init__(self, s):
        super().__init__(s)
        
        self.val = 0
        parts = s.split(':')
        for i in range(len(parts)):
            self.val += float(parts[i]) * (60 ** (len(parts) - i - 1))

    @staticmethod
    def from_val(val):
        hh = int(val / 60 ** 2)
        mm = int((val % (60 ** 2)) / 60)
        ss = val % 60

        s = '{:02.0f}'.format(ss)
        s = '{:02d}:{:s}'.format(mm, s)

        if hh:
            s = '{:02d}:{:s}'.format(hh, s)
        
        return Time(s)
        
class Op(Token):
    def __init__(self, s):
        super().__init__(s)

        self.val = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y,
            'to_km': lambda x: x / MILES_PER_KM,
            'to_miles': lambda x: x * MILES_PER_KM,
            '(': None,
            ')': None,
        }[s]

        self.arity = {
            '+': 2,
            '-': 2,
            '*': 2,
            '/': 2,
            'to_km': 1,
            'to_miles': 1,
            '(': None,
            ')': None,
        }[s]

        self.prec = {
            'to_km': 3,
            'to_miles': 3,
            '*': 2,
            '/': 2,
            '+': 1,
            '-': 1,
            '(': 0,
            ')': 0,
        }[s]

ops = ['+', '-', '*', '/', '(', ')', 'to_km', 'to_miles']

def tokenize(line):
    state = State.INITIAL
    tokens = []
    cur = ''
    i = 0
    while i < len(line):
        c = line[i]
        if state == State.INITIAL:
            if c.isdigit():
                cur += c
                state = State.NUMBER
                
            elif c in ops:
                tokens.append(Op(c))

            elif c in map(lambda o: o[0], ops):
                cur += c
                state = state.OPS

            elif c != ' ':
                raise SyntaxError('Unexpected "{:s}" (char {:d})'.format(c, i + 1))

        elif state == State.OPS:
            if cur + c in ops:
                tokens.append(Op(cur + c))
                cur = ''
                state = state.INITIAL
                
            elif cur + c in map(lambda o: o[:len(cur) + 1], ops):
                cur += c

            else:
                raise SyntaxError('Unknown symbol beginning with "{:s}" (starting at char {:d})'.format(cur + c, i + 1))
        
        elif state == State.NUMBER:
            if c.isdigit():
                cur += c
                
            elif c == '.':
                if '.' in cur:
                    raise SyntaxError('Multiple "." in number.')
                else:
                    cur += c

            elif c == ':':
                if '.' in cur:
                    raise SyntaxError('Invalid time format.')
                else:
                    cur += c
                    state = State.TIME
                
            elif c in ops:
                if cur.endswith('.'):
                    raise SyntaxError('Trailing "." in number.')
                else:
                    tokens.append(Number(cur))
                    cur = ''
                    tokens.append(Op(c))
                    state = State.INITIAL

            elif c == ' ':
                if cur.endswith('.'):
                    raise SyntaxError('Trailing "." in number.')
                else:
                    tokens.append(Number(cur))
                    cur = ''
                    state = State.INITIAL

        elif state == State.TIME:
            if c.isdigit():
                cur += c
                
            elif c == '.':
                if '.' in cur:
                    raise SyntaxError('Multiple "." in number.')
                else:
                    cur += c

            elif c == ':':
                if '.' in cur:
                    raise SyntaxError('Invalid time format.')
                elif cur.count(':') == 2: #which means that with the current char we now have 3 ':'s
                    raise SyntaxError('Invalid number (too many ":" delimiters).')
                elif cur.endswith(':'):
                    raise SyntaxError('Consecutive ":" chars.')
                else:
                    cur += c

            elif c in ops:
                if cur.endswith('.'):
                    raise SyntaxError('Trailing "." in number.')
                elif cur.endswith(':'):
                    raise SyntaxError('Trailing ":" in number.')
                else:
                    tokens.append(Time(cur))
                    cur = ''
                    tokens.append(Op(c))
                    state = State.INITIAL

            elif c == ' ':
                if cur.endswith('.'):
                    raise SyntaxError('Trailing "." in number.')
                elif cur.endswith(':'):
                    raise SyntaxError('Trailing ":" in number.')
                else:
                    tokens.append(Time(cur))
                    cur = ''
                    state = State.INITIAL
                
        i += 1

    if cur.endswith('.'):
        raise SyntaxError('Trailing "." in number.')
    elif cur.endswith(':'):
        raise SyntaxError('Trailing ":" in number.')

    if ':' in cur:
        tokens.append(Time(cur))
    elif cur:
        tokens.append(Number(cur))

    return tokens

def to_postfix(tokens):
    stack = []
    post = []

    i = 0
    while i < len(tokens):
        t = tokens[i]
        
        if isinstance(t, Number) or isinstance(t, Time):
            post.append(t)

        elif isinstance(t, Op):
            if not stack or stack[-1] == '(':
                stack.append(t)

            elif t.s == '(':
                stack.append(t)

            elif t.s == ')':
                try:
                    op = stack.pop()
                    while op.s != '(':
                        post.append(op)
                        op = stack.pop()
                except IndexError:
                    raise EvalError('Unbalanced parentheses.')

            elif t.prec > stack[-1].prec:
                stack.append(t)

            elif t.prec == stack[-1].prec:
                if t.arity == 2:
                    post.append(stack.pop())
                    stack.append(t)
                elif t.arity == 1:
                    stack.append(t)
                else:
                    raise EvalError('Unknown operator arity.')

            elif t.prec < stack[-1].prec:
                post.append(stack.pop())
                i -= 1

        i += 1

    while stack:
        post.append(stack.pop())

    return post

def eval_expr(tokens):
    i = 0
    while len(tokens) > 1:
        if isinstance(tokens[i], Op):
            op = tokens[i]
            operands = tokens[i - op.arity: i]
                
            result = op.val(*map(lambda x: x.val, operands))

            j = 0
            while j < len(operands) and not isinstance(operands[j], Time):
                j += 1
            
            if j < len(operands): #if one or more of the operands is a time
                result = Time.from_val(result)

            else:
                result = Number(result)

            tokens = tokens[:i - op.arity] + [result] + tokens[i + 1:]
            
            i -= op.arity
        else:
            i += 1

    return tokens[0].__str__()
    
def print_tokens(title, tokens):
    s = title + ' '
    for i in range(len(tokens)):
        s += tokens[i].__str__()
        if i < len(tokens) - 1:
            s += ', '

    print(s)

def main():
    print('Time format: "hh:mm:ss" (can omit unnecessary parts).')
    print('Use to_km(<miles>) and to_miles(<km>) to convert distances.')
    
    prompt = '> '
    done = False
    while not done:
        try:
            line = input(prompt)
            tokens = tokenize(line)
            tokens = to_postfix(tokens)
            result = eval_expr(tokens)
            print('=> {:s}'.format(result))

        except SyntaxError as error:
            print(error)
            
        except EOFError:
            print('Bye!')
            done = True

main()
