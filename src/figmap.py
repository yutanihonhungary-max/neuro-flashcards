# 「読む」の図の再表示:src/figures.txt の用語(キー)が本文に出てくるページに、同じ図を自動で付ける。
# build_day.py から呼ぶ。各ページに ax = [{f:ファイル, c:説明, k:見つけた用語, at:段落番号, o:元のページ}] を足す。
# 本文(b)は変えない(蛍光ペンが段落番号で保存しているため)。
import re, pathlib, collections

MAX_PER_PAGE = 3
IMG = re.compile(r'^!img\s+(\S+)\s*\|')
LIST = re.compile(r'^(-\s|\d+\.\s)')


def load(path):
    figs = []
    for raw in open(path, encoding='utf-8'):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        cols = [c.strip() for c in line.split('|')]
        cols += [''] * (4 - len(cols))
        f, cap, keys, group = cols[:4]
        ks = []
        for k in keys.split(','):
            k = k.strip()
            if not k:
                continue
            word, *excl = [x.strip() for x in k.split('!')]
            ks.append((word, excl))
        figs.append({'f': f, 'c': cap, 'keys': ks, 'g': group})
    return figs


def _pattern(word):
    # 英字は単語の途中に一致させない・大文字小文字を区別しない
    p = re.escape(word)
    if re.match(r'[A-Za-z]', word):
        p = r'(?<![A-Za-z])' + p
    if re.search(r'[A-Za-z]$', word):
        p = p + r'(?![A-Za-z])'
    return re.compile(p, re.I)


def _count(text, word, excl):
    for e in excl:  # 除く言葉の中の一致は数えない
        text = text.replace(e, '\0' * len(e))
    return len(_pattern(word).findall(text))


def assign(D, path):
    figs = load(path)
    byfile = {x['f']: x for x in figs}
    home = {}  # 図 → 最初に出てくるページ
    for d in D:
        for pg in d.get('lesson', []):
            for l in pg['b']:
                m = IMG.match(l)
                if m and m.group(1) not in home:
                    home[m.group(1)] = (d, pg)
    stats = collections.Counter()
    for d in D:
        for pg in d.get('lesson', []):
            own = {m.group(1) for m in (IMG.match(l) for l in pg['b']) if m}
            groups = {byfile[f]['g'] for f in own if f in byfile and byfile[f]['g']}
            cands = []
            for fi, fg in enumerate(figs):
                if fg['f'] in own or not fg['keys'] or fg['f'] not in home:
                    continue
                score, first, key = 0, None, None
                for bi, l in enumerate(pg['b']):
                    if IMG.match(l):
                        continue
                    for word, excl in fg['keys']:
                        n = _count(l, word, excl)
                        if n:
                            score += n
                            if first is None:
                                first, key = bi, word
                if score:
                    cands.append((-score, first, fi, key))
            cands.sort()
            ax = []
            for _, first, fi, key in cands:
                fg = figs[fi]
                if fg['g'] and fg['g'] in groups:
                    continue
                if len(ax) >= MAX_PER_PAGE:
                    break
                # 箇条書きの途中なら、その箇条書きの始まりの手前に置く
                at = first
                if LIST.match(pg['b'][at]):
                    kind = pg['b'][at][0] == '-'
                    while at > 0 and LIST.match(pg['b'][at - 1]) and (pg['b'][at - 1][0] == '-') == kind:
                        at -= 1
                hd, hp = home[fg['f']]
                n = re.match(r'\s*(\d+)', hd['title'])
                origin = ('Day ' + n.group(1) if n else hd['title']) + '「' + hp['h'] + '」'
                ax.append({'f': fg['f'], 'c': fg['c'], 'k': key, 'at': at, 'o': origin})
                if fg['g']:
                    groups.add(fg['g'])
            ax.sort(key=lambda a: a['at'])
            if ax:
                pg['ax'] = ax
                stats['pages'] += 1
                stats['figs'] += len(ax)
            else:
                pg.pop('ax', None)
    missing = [x['f'] for x in figs if not (pathlib.Path(path).parent.parent / 'img' / x['f']).exists()]
    assert not missing, missing
    return stats
