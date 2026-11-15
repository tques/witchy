"""Start a new character from the template.

  python tools/new_character.py NAME
creates characters/NAME.py (expects sprites/NAME.png from tools/prep_sprite.py).
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[1]
dst = os.path.join(ROOT, 'characters', f'{name}.py')
if os.path.exists(dst):
    sys.exit(f'{dst} already exists')
src = open(os.path.join(ROOT, 'characters', '_template.py')).read()
src = src.replace('__NAME__', name).replace('TEMPLATE: copy with  python tools/new_character.py NAME  (don\'t edit this file directly).', f'{name}')
open(dst, 'w').write(src)
if not os.path.exists(os.path.join(ROOT, 'sprites', f'{name}.png')):
    print(f'note: sprites/{name}.png not found yet; run tools/prep_sprite.py on the source image first')
print(f'created characters/{name}.py\nnext: python -m spritestack.build characters/{name}.py --quick --views 0,35,90,180')
