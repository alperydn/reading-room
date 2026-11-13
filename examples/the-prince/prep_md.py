import re, sys
L = open('src/prince.txt', encoding='utf-8').read().splitlines()
a = next(i for i,l in enumerate(L) if 'START OF THIS PROJECT' in l) + 1
b = next(i for i,l in enumerate(L) if 'END OF THIS PROJECT' in l)
L = L[a:b]
paras, cur = [], []
for l in L:
    if l.strip(): cur.append(l)
    elif cur: paras.append(cur); cur = []
if cur: paras.append(cur)
HEAD = re.compile(r'^(INTRODUCTION|THE MAN AND HIS WORKS|DEDICATION|CHAPTER [IVXL]+.*|DESCRIPTION OF THE METHODS.*|THE LIFE OF CASTRUCCIO.*)$')
NOTE = re.compile(r'^\s+\(([*+#]|\d+)\)\s+(.*)$')
out, pending, n = [], [], 0
started = False
for p in paras:
    first = p[0].strip()
    if HEAD.match(first) and p[0] == p[0].lstrip():
        started = True
        title = ' '.join(x.strip() for x in p)
        title = title.replace(' -- ', ' — ')
        def mk(m):
            global n; n += 1; pending.append((m.group(1), 'n%d' % n)); return '[^n%d]' % n
        title = re.sub(r'\(([*+#])\)', mk, title)
        out.append('# ' + title); continue
    if not started: continue
    if first in ('THE PRINCE', 'BY'): continue
    if first in ('NICOLO MACHIAVELLI', 'WRITTEN BY NICOLO MACHIAVELLI') and len(p) == 1:
        out.append('## Nicolo Machiavelli'); continue
    m = NOTE.match(p[0])
    if m:
        sym, txt = m.group(1), ' '.join([m.group(2)] + [x.strip() for x in p[1:]])
        idx = next((i for i,(s,_) in enumerate(pending) if s == sym), None)
        if idx is None:
            print('ESLESMEYEN NOT:', txt[:60], file=sys.stderr); continue
        _, nid = pending.pop(idx)
        out.append('[^%s]: %s' % (nid, txt)); continue
    text = ' '.join(x.strip() for x in p)
    def mk(m):
        global n; n += 1; pending.append((m.group(1), 'n%d' % n)); return '[^n%d]' % n
    text = re.sub(r'\(([*+#])\)', mk, text)
    out.append(text)
print('kalan eşleşmeyen işaret:', len(pending), pending[:5], file=sys.stderr)
open('prince.md', 'w', encoding='utf-8').write('\n\n'.join(out) + '\n')
