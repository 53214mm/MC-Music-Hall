"""阶段 1 修订版 · 旧版 vs 新版体块对比。

只读。用法：python tools/build/compare_phase1.py
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_music_hall as B
import phase1_massing as P1


def metrics(blocks, name):
    xs = [p[0] for p in blocks]; ys = [p[1] for p in blocks]; zs = [p[2] for p in blocks]
    w, h, d = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1
    top = defaultdict(lambda: -999)
    for (x, y, z) in blocks:
        top[(x, z)] = max(top[(x, z)], y)
    buckets = Counter(v // 5 * 5 for v in top.values() if v >= 0)
    上层 = sorted((k for k in buckets if buckets[k] >= 5), reverse=True)
    return {'name': name, 'w': w, 'h': h, 'd': d, 'blocks': len(blocks),
            'hw': h / w, 'dw': d / w, 'levels': len(上层), 'buckets': buckets}


def main():
    print('=' * 76)
    print('阶段 1 修订版 · 旧版 vs 新版体块对比')
    print('=' * 76)
    print()
    print('【体块尺寸】')
    print(f'{"项目":<24}{"旧版":>14}{"新版":>14}')
    old = {'塔截面': '19×19', '塔深': '6 格', '耳堂': '无', '中央塔基座': '11 宽圆',
           '核心横墙': '无', '屋顶': '沿 X 双坡'}
    new = {'塔截面': '20×20', '塔深': '12 格', '耳堂': '两侧凸出 8 格',
           '中央塔基座': '22×18 收 16×12', '核心横墙': '外墙环 + 纵向坡屋面',
           '屋顶': '沿 Z 双坡'}
    for k in old:
        print(f'{k:<24}{old[k]:>14}{new[k]:>14}')

    print()
    print('【塔楼分级】')
    print(f'{"":<8}{"旧版":<32}{"新版":<32}')
    print(f'{"":<8}{"下段塔身 1 级 + 尖顶":<32}{"塔基座 / 塔身 / 钟室 / 尖顶 4 级":<32}')
    print(f'{"收分次数":<8}{"1 次（塔身直接收尖）":<32}{"3 次（19→17→20 挑出→尖顶）":<32}')
    print(f'{"束带层":<8}{"无":<32}{"钟室底部外挑 1~2 格":<32}')
    print()
    print('【中央塔分级】')
    print(f'{"":<8}{"旧版":<32}{"新版":<32}')
    print(f'{"分级":<8}{"鼓座 + 尖顶 2 级":<32}{"基座 / 过渡体 / 塔身 / 尖顶 4 级":<32}')
    print(f'{"收分次数":<8}{"1 次":<32}{"3 次":<32}')
    print(f'{"塔根":<8}{"落在核心屋脊上":<32}{"基座压住交叉脊线，做成收台":<32}')

    print()
    print('【总体指标】')
    cur = metrics({**B.load_modules()[0], **B.make_shell()}, '原始教堂')
    old_p1 = metrics(_old_phase1(), '阶段1 旧版')
    new_p1 = metrics(P1.generate(), '阶段1 新版')
    print(f'{"项目":<16}{"原始教堂":>14}{"阶段1 旧版":>14}{"阶段1 新版":>14}')
    for key, label in [('w', '总宽'), ('h', '总高'), ('d', '总长'), ('blocks', '方块数'),
                       ('hw', '高:宽'), ('dw', '长:宽'), ('levels', '高度层次数')]:
        fmt = '{:.2f}' if key in ('hw', 'dw') else '{}'
        print(f'{label:<16}' + ''.join(
            f'{fmt.format(m[key]):>14}' for m in (cur, old_p1, new_p1)))

    print()
    print('【高度层次分布（有多少列的顶落在各高度带，只列 ≥5 列的带）】')
    bands = sorted(set(cur['buckets']) | set(old_p1['buckets']) | set(new_p1['buckets']),
                   reverse=True)
    print(f'{"高度带":>10}{"原始教堂":>12}{"阶段1旧版":>12}{"阶段1新版":>12}')
    for b in bands:
        a, o, n = cur['buckets'].get(b, 0), old_p1['buckets'].get(b, 0), new_p1['buckets'].get(b, 0)
        if max(a, o, n) < 5:
            continue
        print(f'{f"{b}-{b+4}":>10}{a:>12}{o:>12}{n:>12}')


def _old_phase1():
    """旧版阶段 1 体块：从 git 历史里取出上一版的生成器，在同一进程里直出。

    直接读版本库，避免依赖"上一次构建的产物还在不在"。
    """
    import importlib.util
    import subprocess
    import tempfile
    root = Path(__file__).resolve().parents[2]
    try:
        source = subprocess.run(['git', 'show', 'HEAD:tools/build/phase1_massing.py'],
                                cwd=root, capture_output=True, check=True).stdout.decode('utf-8')
    except Exception:
        return {}
    folder = tempfile.mkdtemp()
    path = Path(folder) / 'old_phase1.py'
    path.write_text(source, encoding='utf-8')
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    spec = importlib.util.spec_from_file_location('old_phase1', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate()


if __name__ == '__main__':
    main()
