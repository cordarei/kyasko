#!/usr/bin/env python3

import collections
import itertools
import sys

import ptb


MAX_CONSTITUENT_LENGTH = 3

def transform(t):
    ptb.remove_empty_elements(t)
    ptb.simplify_labels(t)
    return ptb.add_root(t, 'ROOT')
def trees(filename):
    with open(filename) as f:
        for t in ptb.parse(f):
            yield transform(t)

def make_grammar(trainfile):
    rules = collections.Counter(
        (r)
        for t in trees(trainfile)
        for r in ptb.all_rules(t)
        if len(r.children) <= MAX_CONSTITUENT_LENGTH
    )
    rs = list(rules)
    rs.sort(key=lambda r:r.head)
    heads = dict(
        (h, sum(rules[r] for r in rs))
        for (h,rs) in itertools.groupby(rs, lambda r:r.head)
    )
    for r in rules:
        r.prob = rules[r] / heads[r.head]
    return rules

def main(args):
    trainfile,testfile = args
    rules = make_grammar(trainfile)
    # rs = list((r,c,r.prob) for (r,c) in rules.most_common())
    # rs.sort(key=lambda x:x[2], reverse=True)
    # for r,c,p in rs:
    #     print(r, c, '{:.3f}'.format(p), sep='\t')
    sents = list(ptb.make_parsed_sent(t) for t in trees(testfile))
    indices = [(s,i) for s in sents for i in range(sum(1 for _ in s.words()))]
    for s,i in indices:
        print(i, next( s.words(i,i+1) ))

if __name__ == "__main__":
    main(sys.argv[1:])
