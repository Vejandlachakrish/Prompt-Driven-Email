import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT, '..'))

def has_null_bytes(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
        return 0 in data, data.count(b'\x00')
    except Exception as e:
        return False, 0

problem_files = []
for dirpath, _, filenames in os.walk(PROJECT_ROOT):
    for name in filenames:
        if name.endswith('.py'):
            full = os.path.join(dirpath, name)
            contains, count = has_null_bytes(full)
            if contains:
                problem_files.append((full, count))

if not problem_files:
    print('No null bytes detected in any .py source file.')
else:
    print('Null byte corruption detected in the following files:')
    for f, c in problem_files:
        print(f'  {f} (null byte count: {c})')
    print('\nRecommended remediation steps:')
    print('1. Open the file in a hex editor and remove null bytes, or re-create the file.')
    print('2. Delete __pycache__ directories:')
    print('   PowerShell: Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force')
    print('3. Re-run: streamlit run app.py')

# Exit code signals issue
sys.exit(1 if problem_files else 0)
