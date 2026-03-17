import sys
sys.path.insert(0, r'C:\Users\Edu\Documents\ClaudeWork\KeplerDB')
import kepler_interp as ki

# Tus posiciones reales (Placidus, h+off corregido)
# Sol en Libra (signo 7) casa 6 → DISTINTOS
# Luna en Tauro (signo 2) casa 12 → DISTINTOS
# Mercurio en Libra (signo 7) casa 5 → DISTINTOS
# Saturno en Leo (signo 5) casa 4 → DISTINTOS
# Jupiter en Geminis (signo 3) casa 12 → DISTINTOS

tests = [
    ('Sol',      'Libra',    6),
    ('Luna',     'Tauro',   12),
    ('Mercurio', 'Libra',    5),
    ('Saturno',  'Leo',      4),
    ('Jupiter',  'Géminis', 12),
    ('Marte',    'Escorpio', 6),
    ('Venus',    'Escorpio', 6),
]

for p, sig, casa in tests:
    rows = ki.get_planeta(p, sig, casa)
    print(f'\n{p} en {sig} · Casa {casa} → {len(rows)} textos')
    for cab, texto, tipo in rows:
        print(f'  [{tipo}] {cab}')
        print(f'  {texto[:100]}...')
