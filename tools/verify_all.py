"""一条命令跑完全部核验：模块导出时序审计 + 布局审计 + 三个测试模块。

用法（项目根目录）：python tools/verify_all.py
只读数据、不写文件；布局审计会重写 design/layout_audit.json，这是预期行为。
"""
import subprocess
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent


def run(command, cwd):
    print(f'\n$ {" ".join(command)}   (cwd={cwd.relative_to(ROOT) or "."})', flush=True)
    return subprocess.call(command, cwd=cwd)


def main():
    results = {}
    results['模块导出时序审计'] = run([sys.executable, 'build/audit_export_timing.py'], TOOLS)
    results['布局审计'] = run([sys.executable, 'build/audit_layout.py'], TOOLS)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite([
        loader.discover(str(TOOLS / 'viewer'), pattern='test_*.py', top_level_dir=str(TOOLS / 'viewer')),
        loader.discover(str(TOOLS / 'build'), pattern='test_*.py', top_level_dir=str(TOOLS / 'build')),
    ])
    print('\n$ unittest (tools/viewer + tools/build)', flush=True)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    results['单元测试'] = 0 if outcome.wasSuccessful() else 1

    print('\n===== 汇总 =====')
    for name, code in results.items():
        print(f'{"PASS" if code == 0 else "FAIL"}  {name}')
    return 0 if all(code == 0 for code in results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
