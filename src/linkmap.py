# Matches each fact card and summary card to the most similar reading page of the same Day.
# Used by build_day.py: assign(D) sets card['pg'] = heading of the best page (or leaves it out).
import math, re
from collections import Counter

HIRA = re.compile(r'^[぀-ゟ]+$')
JRUN = re.compile(r'[぀-ヿ一-鿿々ー]+')
EWORD = re.compile(r"[a-z][a-z0-9']+")
STOP = {'the', 'and', 'of', 'to', 'in', 'is', 'are', 'for', 'with', 'from', 'by', 'or', 'on', 'at', 'as', 'an', 'its', 'via'}


def tokens(text):
    t = text.lower()
    out = [w for w in EWORD.findall(t) if w not in STOP]
    for run in JRUN.findall(t):
        for i in range(len(run) - 1):
            bg = run[i:i + 2]
            if not HIRA.match(bg):
                out.append(bg)
    return out


def page_text(pg):
    lines = [re.sub(r'^!img\s+\S+\s*\|\s*', '', l) for l in pg['b']]
    return (pg['h'] + '\n') * 2 + '\n'.join(lines)


def build_index(lesson):
    docs = [Counter(tokens(page_text(p))) for p in lesson]
    n = len(docs)
    df = Counter()
    for d in docs:
        df.update(d.keys())
    idf = {w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()}
    vecs = []
    for d in docs:
        v = {w: (1 + math.log(c)) * idf[w] for w, c in d.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        vecs.append((v, norm))
    return idf, vecs


def best_page(card, lesson, index, skip_first=True):
    idf, vecs = index
    q = Counter(tokens(card['q'] + ' ' + card['a']))
    qv = {w: (1 + math.log(c)) * idf[w] for w, c in q.items() if w in idf}
    qn = math.sqrt(sum(x * x for x in qv.values())) or 1
    scores = []
    for i, (v, n) in enumerate(vecs):
        s = sum(x * v.get(w, 0) for w, x in qv.items()) / (qn * n)
        if skip_first and lesson[i]['h'] == '今日学ぶこと':
            s *= 0.85  # overview page: link there only when it clearly fits best
        scores.append(s)
    i = max(range(len(scores)), key=scores.__getitem__)
    return i, scores[i]


MIN_SCORE = 0.06


def assign(D):
    stats = Counter()
    for d in D:
        lesson = d.get('lesson') or []
        if not lesson:
            continue
        index = build_index(lesson)
        cards = list(d.get('facts') or [])
        for s in d['secs']:
            cards += s['cards']
        for c in cards:
            i, sc = best_page(c, lesson, index)
            if sc >= MIN_SCORE:
                c['pg'] = lesson[i]['h']
                stats['linked'] += 1
            else:
                c.pop('pg', None)
                stats['unlinked'] += 1
    return stats
