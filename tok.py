#!/usr/bin/env python3

import sys
import re

def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def break_token(tok):
    s = tok
    while s and s[0] in '"\'':
        yield s[0]
        s = s[1:]
    hyphs = s.split('-')
    for h in hyphs[:-1]:
        yield h
    s = hyphs[-1]
    if not s: print("#TOK:",tok)
    yield s


def tokens(fn):
    with open(fn) as f:
        ws = (word.strip() for line in f for word in line.split() if word.strip())
        for w in ws:
            for t in break_token(w):
                yield t


def next_token(s):
    skip = lambda m,s: (None,s)
    ret = lambda m,s: (m,s)
    rules = [
        ('\s+', skip),
        ('["\',]', ret),
        ('-+', ret),
        # ('\w+\.', ??),
        ('\w+', ret),
        ('.', ret)
    ]
    def apply(r, s):
        p,a = r
        m = re.match(p, s)
        if m:
            return a(m.group(), s[m.end():])
        else:
            return (None, s)
    if not s:
        raise Error('stop')
    for r in rules:
        m,s = apply(r,s)
        if m:
            return (m,s)
    return (s, '')

class Rule(object):
    def __init__(self, pattern, action):
        self.pattern = pattern
        self.action = action

    def __call__(self, s):
        m = re.match(self.pattern, s)
        if m:
            return [self.action(m, s[m.end():])]
        else:
            return []

    @staticmethod
    def skip(m, s):
        return ([], s)
    @staticmethod
    def ret(m, s):
        return ([m.group()], s)

class State(object):
    def __init__(self, tokens, remaining):
        self.tokens = tokens
        self.remaining = remaining

    def extend(self, rule):
        res = rule(self.remaining)
        return [
            State(self.tokens + t, s)
            for t,s in res
        ]
        # if not res:
        #     return []
        # t,s = res[0]
        # return [State(self.tokens + t, s)]

    def __repr__(self):
        return "State<tokens:{} remaining:'{}'>".format(self.tokens, self.remaining)

def concat(ys):
    xs = []
    for y in ys:
        xs.extend(y)
    return xs

def do_search(rules, s):
    final_states = []
    states = [State([], s)]
    while states:
        # log('states:',states)
        # ns = list(filter(lambda x: x, (st.extend(r) for r in rules for st in states)))
        ns = concat(st.extend(r) for r in rules for st in states)
        # log('ns:',ns)
        for st in ns:
            if not st.remaining:
                final_states.append(st)
        # if not ns:
        #     log('no more states!\nstates:\n', states)
        #     log('ns:\n', ns)
        states = [st for st in ns if st.remaining]

    return final_states

def paragraphs(f):
    para = []
    for line in f:
        line = line.strip()
        if line:
            para.append(line)
        else:
            if para:
                yield ' '.join(para)
                para = []

def main(args):
    fn = args[0]
    with open(fn) as f:
        for p in paragraphs(f):
            print('#PARA_START')

            rules = [
                Rule('\s+', Rule.skip),
                # Rule('["\',]', Rule.ret),
                Rule('-+', Rule.ret),
                Rule('\w+', Rule.ret),
                Rule('\'s', Rule.ret),
                # Rule('\w+(-\w+)+', Rule.ret),
                Rule('\w+(\.\w+)+', Rule.ret),
                Rule('\w+(\.\w+)+\.', Rule.ret),
                Rule('\w+\.', Rule.ret),
                Rule('[^\w\s]', Rule.ret)
            ]
            states = do_search(rules, p)
            for st in states:
                print(st.tokens)

            # m,s = next_token(p)
            # while m and s:
            #     print(m)
            #     m,s = next_token(s)
            print()

if __name__ == "__main__":
    main(sys.argv[1:])
