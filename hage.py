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

def gather(xs, key):
    ys = list(xs)
    ys.sort(key=key)
    return dict((k,list(vs)) for k,vs in itertools.groupby(ys, key))

def main(args):
    probstr = lambda p: '{:.5f}'.format(p) if p > 0.0 else '#ZERO#'
    trainfile,testfile = args
    rules = make_grammar(trainfile)
    left_corner = gather(rules, lambda r:r.children[0])
    unaries = [r for r in rules if len(r.children) == 1]
    # rs = list((r,c,r.prob) for (r,c) in rules.most_common())
    # rs.sort(key=lambda x:x[2], reverse=True)
    # for r,c,p in rs:
    #     print(r, c, '{:.3f}'.format(p), sep='\t')
    word = lambda s,i: next(s.words(i, i+1))
    sents = list(ptb.make_parsed_sent(t) for t in trees(testfile))
    indices = [(s,i) for s in sents for i in range(sum(1 for _ in s.words()))]
    words = [word(s,i) for s,i in indices]
    # for s,i in indices:
    #     print(i, next( s.words(i,i+1) ))
    chart = collections.defaultdict(lambda: collections.defaultdict(lambda:(0.0,[])))
    agenda = collections.defaultdict(list)
    # def update(d,x,p):
    #     if (d[x][0] < p):
    #         d[x] = (p, [])
    # def introduce(rule, span, p):
    #     agenda[(span)].append((rule, 1, [span[1]], p))
    def complete(rule, span, prob, offsets):
        if chart[span][rule.head][0] < prob:
            chart[span][rule.head] = (prob, offsets)
            for r in left_corner.get(rule.head, []):
                # introduce(r, span, prob * r.prob)
                if len(r.children) > 1:
                    agenda[(span)].append((r, 1, prob * r.prob, [span[1]]))
                else:
                    pass
    for i in range(len(words)):
        for r in unaries:
            if r.children[0] == words[i]:
                # update(chart[(i,i+1)], r.head, r.prob)
                complete(r, (i,i+1), r.prob, [])
    for l in range(2, MAX_CONSTITUENT_LENGTH + 1):
        for i in range(len(words) - l):
            for k in range(i+1, i+l):
                for r,dot,p,off in agenda[(i,k)]:
                    if dot >= len(r.children): print ("Error:",r,dot)
                    if r.children[dot] in chart[(k, i+l)]:
                        q = p * chart[(k,i+l)][r.children[dot]][0]
                        if dot+1 == len(r.children):
                            complete(r, (i,i+l), q, off)
                        else:
                            # introduce(r, (i, i+l), q, off+[i+l])
                            agenda[(i,i+l)].append((r, dot+1, q, off+[i+l]))


    for sp in sorted(chart):
        for c in chart[sp]:
            print(sp, c, probstr(chart[sp][c][0]), ' '.join(words[sp[0]:sp[1]]), sep='\t')

if __name__ == "__main__":
    main(sys.argv[1:])
