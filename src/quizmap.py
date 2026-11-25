# 「読む」の各ページの最後に出す確認問題(チェックボックスだけ。暗記の予定は付けない)。
# build_day.py から、linkmap.assign のあとに呼ぶ。各ページに qz = [{q, a, t}] を足す(t は 部品/まとめ/確認)。
#  - ページ専用に書いた問題(content の @quiz、pg['qown'])があるページは、それだけを出す。
#  - ほかのページは、「読むで確認」リンクがそのページを指す部品とまとめのカード。
#  - 3問に満たないページは、そのページとの言葉の重なりが大きいカードで3問まで補う(ほかのページと重複してよい)。
#  - 「今日学ぶこと」(その日の概要)には出さない。
from collections import Counter
import math
import linkmap

MIN = 3
EXTRA_SCORE = 0.06


def _scores(card, index):
    idf, vecs = index
    q = Counter(linkmap.tokens(card['q'] + ' ' + card['a']))
    qv = {w: (1 + math.log(c)) * idf[w] for w, c in q.items() if w in idf}
    qn = math.sqrt(sum(x * x for x in qv.values())) or 1
    return [sum(x * v.get(w, 0) for w, x in qv.items()) / (qn * n) for v, n in vecs]


def assign(D):
    st = Counter()
    for d in D:
        lesson = d.get('lesson') or []
        if not lesson:
            continue
        cards = [('部品', c) for c in d.get('facts') or []] + [('まとめ', c) for s in d['secs'] for c in s['cards']]
        index = linkmap.build_index(lesson)
        sc = [_scores(c, index) for _, c in cards]
        for i, pg in enumerate(lesson):
            if pg.get('qown'):
                pg['qz'] = [dict(x, t='確認') for x in pg['qown']]
                st['own'] += 1
                continue
            if pg['h'] == '今日学ぶこと':
                st['overview'] += 1
                continue
            got = [k for k, (_, c) in enumerate(cards) if c.get('pg') == pg['h']]
            if len(got) < MIN:
                rest = sorted((k for k in range(len(cards)) if k not in got and sc[k][i] >= EXTRA_SCORE), key=lambda k: -sc[k][i])
                got += rest[:MIN - len(got)]
            got.sort(key=lambda k: (cards[k][0] != '部品', k))
            pg['qz'] = [{'q': cards[k][1]['q'], 'a': cards[k][1]['a'], 't': cards[k][0]} for k in got]
            st['pages' if got else 'empty'] += 1
            st['items'] += len(got)
    return st
