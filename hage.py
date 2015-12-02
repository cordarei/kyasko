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
    probstr = lambda p: '{:.6g}'.format(p) if p > 0.0 else '#ZERO#'
    trainfile,testfile = args
    rules = make_grammar(trainfile)
    left_corner = gather(
        (r for r in rules if r.children[1:]),
        lambda r:r.children[0]
    )
    lexrules = [r for r in rules if r.islex]
    unary_rules = [r for r in rules if len(r.children) == 1 and not r.islex]
    unary_matrix = dict(((r.head, r.children[0]), r.prob) for r in unary_rules)

    def closure(path, cur):
        rs = [r for r in unary_rules if r.children[0] == cur]
        xs = [(r,c) for r in rs for c in path]
        upd = dict()
        for r,c in xs:
            edge = (r.head, c)
            p = unary_matrix[(cur,c)] * r.prob
            if edge not in unary_matrix:
                upd[edge] = p
            elif unary_matrix[edge] < p:
                upd[edge] = p
            else:
                pass
        unary_matrix.update(upd)
        for h,c in upd:
            closure(path + [cur], h)

    # before = dict(unary_matrix)
    for r in unary_rules:
        closure(r.children, r.head)
    closed_unary_rules = dict(
        (c, [ptb.Rule(h, [c], unary_matrix[(h,c)]) for h,k in unary_matrix if k == c])
        for c in set(c for h,c in unary_matrix)
    )

    # for edge in unary_matrix:
    #     if edge in before and unary_matrix[edge] == before[edge]:
    #         print('SAME:', edge)
    #     elif edge in before:
    #         print('CHANGED:', edge, before[edge], '->', unary_matrix[edge])
    #     else:
    #         print('NEW:', edge, unary_matrix[edge])
    # CHANGED: ('ROOT', 'SBAR') 0.0005027652086475615 -> 0.0005586280096084018

    # rs = list((r,c,r.prob) for (r,c) in rules.most_common())
    # rs.sort(key=lambda x:x[2], reverse=True)
    # for r,c,p in rs:
    #     print(r, c, '{:.3f}'.format(p), sep='\t')

    word = lambda s,i: next(s.words(i, i+1))
    sents = list(ptb.make_parsed_sent(t) for t in trees(testfile))
    indices = [(s,i) for s in sents for i in range(sum(1 for _ in s.words()))]
    words = [word(s,i) for s,i in indices]

    chart = collections.defaultdict(lambda: collections.defaultdict(lambda:(0.0,None,[])))
    agenda = collections.defaultdict(list)

    def get_tree(chart, span, head):
        # print('LOG: Called get_tree with span={} head={}'.format(span, head), file=sys.stderr)
        p,r,os = chart[span][head]
        # print('LOG: get_tree p={} r={} os={}'.format(p, r, os), file=sys.stderr)
        if r.islex:
            return '({} {})'.format(r.head, r.children[0])
        cs = lambda: zip(r.children, [span[0]] + os, os + [span[1]])
        # print('LOG: get_tree cs={}'.format(list(cs())), file=sys.stderr)
        return '({} {})'.format(
            head,
            ' '.join(get_tree(chart, (b,e), c) for c,b,e in cs())
        )

    def complete(rule, span, prob, offsets):
        if chart[span][rule.head][0] < prob:
            chart[span][rule.head] = (prob, rule, offsets)
            for r in closed_unary_rules.get(rule.head, []):
                complete(r, span, prob * r.prob, [])
            for r in left_corner.get(rule.head, []):
                agenda[(span)].append((r, 1, prob * r.prob, [span[1]]))

    for i in range(len(words)):
        for r in lexrules:
            if r.children[0] == words[i]:
                complete(r, (i,i+1), r.prob, [])
    for l in range(2, MAX_CONSTITUENT_LENGTH + 1):
        for i in range(len(words) - l + 1):
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


    # for sp in sorted(chart):
    #     for c in chart[sp]:
    #         print(sp, c, probstr(chart[sp][c][0]), ' '.join(words[sp[0]:sp[1]]), sep='\t')
    for sp in sorted(chart):
        if sp[1] - sp[0] > 1:
            for c in chart[sp]:
                print(sp, c, probstr(chart[sp][c][0]), ' '.join(words[sp[0]:sp[1]]), get_tree(chart, sp, c), sep='\t')

if __name__ == "__main__":
    main(sys.argv[1:])
