# 口頭練習の問い(src/oral.txt)に、「入れたい要点」として、そのDayの「部品」「まとめ」カードを付ける。
# build_day.py から呼ぶ。返り値 = [{q, ja, days, star, fu:[続けて聞かれた質問], pts:[{q, a, s}]}]
# 選び方:キーワードがカードの問いにあれば3点、答えにあれば1点(同じキーワードは1回だけ)、★の数を足す。
#        問いにキーワードが1つもないカードは使わない。点の高い順に最大 MAXP 枚、Day と元の並び順で表示。
import re

MAXP = 8


def load(path):
    items = []
    for raw in open(path, encoding='utf-8'):
        line = raw.rstrip('\n')
        if not line.strip():
            continue
        if line.startswith('## '):
            cols = [c.strip() for c in line[3:].split('|')]
            cols += [''] * (5 - len(cols))
            q, ja, days, keys, star = cols[:5]
            items.append({'q': q, 'ja': ja, 'days': [int(x) for x in days.split(',') if x.strip()],
                          'keys': [k.strip() for k in keys.split(',') if k.strip()], 'star': star == '★', 'fu': []})
        elif line.startswith('#'):
            continue
        elif line.startswith('- ') and items:
            items[-1]['fu'].append(line[2:].strip())
    return items


def _has(text, key):
    if re.match(r'[A-Za-z0-9]', key):
        return re.search(r'(?<![A-Za-z])' + re.escape(key) + r'(?![A-Za-z])', text, re.I) is not None
    return key in text


def assign(D, path):
    items = load(path)
    out = []
    for it in items:
        cands = []
        n = 0
        for day in it['days']:
            d = D[day - 1]
            cards = list(d.get('facts') or []) + [c for s in d['secs'] for c in s['cards']]
            for c in cards:
                n += 1
                inq = [k for k in it['keys'] if _has(c['q'], k)]
                if not inq:
                    continue
                ina = [k for k in it['keys'] if k not in inq and _has(c['a'], k)]
                score = 3 * len(inq) + len(ina) + c.get('s', 0)
                cands.append((-score, n, day, c))
        seen = set()
        pick = []
        for _, n, day, c in sorted(cands, key=lambda x: (x[0], x[1])):
            if c['q'] in seen:
                continue
            seen.add(c['q'])
            pick.append((n, day, c))
            if len(pick) >= MAXP:
                break
        pick.sort(key=lambda x: x[0])
        assert pick, ('no points for oral question', it['q'])
        out.append({'q': it['q'], 'ja': it['ja'], 'days': it['days'], 'star': it['star'], 'fu': it['fu'],
                    'pts': [{'q': c['q'], 'a': c['a'], 's': c.get('s', 0), 'd': day} for _, day, c in pick]})
    return out
