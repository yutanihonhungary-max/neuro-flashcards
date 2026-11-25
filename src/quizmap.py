# 「読む」の各ページの最後に出す確認問題(チェックボックスだけ。暗記の予定は付けない)。
# build_day.py から、linkmap.assign のあとに呼ぶ。各ページに qz = [{q, a, t}] を足す(t は 確認/部品/まとめ)。
# 方針:そのページを読めば答えられる問いだけを出す(2026-11-26。それ以前は言葉の重なりだけで選んでいて、
#       ページに書いていない答えの問いが混じっていた)。
#  - content の @quiz に書いた問い(pg['qown']、t=確認):そのページの本文から答えられるように書いたもの。
#  - 部品とまとめのカード:答えの言葉(英単語と漢字・カタカナの2文字の組)の COVER 以上がそのページの本文に
#    書いてあるものだけ。「読むで確認」のリンク先のページで満たせばそこに、満たさなければ、答えの言葉が
#    いちばん多く書いてあるページに(満たせば)。どのページでも満たさないカードは出さない。
#  - 「今日学ぶこと」(その日の概要)と、!nolink の補足のページには、カードの問いは出さない。
import re
from collections import Counter
import linkmap

COVER = 0.7


def _page_tokens(pg):
    lines = [re.sub(r'^!img\s+\S+\s*\|\s*', '', l) for l in pg['b']]
    return set(linkmap.tokens(pg['h'] + '\n' + '\n'.join(lines)))


def cover(card, ptoks):
    t = set(linkmap.tokens(card['a']))
    return len(t & ptoks) / len(t) if t else 0.0


def assign(D):
    st = Counter()
    for d in D:
        lesson = d.get('lesson') or []
        if not lesson:
            continue
        heads = [p['h'] for p in lesson]
        ok = [not (p['h'] == '今日学ぶこと' or p.get('nolink')) for p in lesson]
        P = [_page_tokens(p) for p in lesson]
        got = [[] for _ in lesson]
        cards = [('部品', c) for c in d.get('facts') or []] + [('まとめ', c) for s in d['secs'] for c in s['cards']]
        for k, (t, c) in enumerate(cards):
            cs = [cover(c, P[i]) if ok[i] else 0.0 for i in range(len(lesson))]
            i = heads.index(c['pg']) if c.get('pg') in heads else -1
            if i < 0 or cs[i] < COVER:
                i = max(range(len(lesson)), key=cs.__getitem__)
            if cs[i] >= COVER:
                got[i].append(k); st['cards'] += 1
            else:
                st['cards_not_shown'] += 1
        for i, pg in enumerate(lesson):
            items = [dict(x, t='確認') for x in pg.get('qown', [])]
            items += [{'q': cards[k][1]['q'], 'a': cards[k][1]['a'], 't': cards[k][0]}
                      for k in sorted(got[i], key=lambda k: (cards[k][0] != '部品', k))]
            if items:
                pg['qz'] = items
                st['pages'] += 1
            elif pg['h'] != '今日学ぶこと':
                st['empty'] += 1
    return st
