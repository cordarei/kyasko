#!/usr/bin/env python3

import sys
import re

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
            m,s = next_token(p)
            while m and s:
                print(m)
                m,s = next_token(s)

if __name__ == "__main__":
    main(sys.argv[1:])
