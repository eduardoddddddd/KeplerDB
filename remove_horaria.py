import json, shutil, re

NB = r'C:\Users\Edu\Downloads\astro_dashboard_v2.ipynb'
shutil.copy2(NB, NB.replace('.ipynb','_pre_nohoraria.ipynb'))

with open(NB, encoding='utf-8') as f:
    nb = json.load(f)

# Trabajar sobre celda 2 (la grande)
src = ''.join(nb['cells'][2]['source'])
lineas = src.split('\n')
print(f'Lineas antes: {len(lineas)}')

# Encontrar rangos a eliminar
# 1. Bloque _build_horaria + _tabla_horaria  (lineas 85-199 aprox)
# 2. tab_horaria = _build_horaria() (linea 675)
# 3. tab_horaria en TABS.children (linea 684)
# 4. TABS.set_title(1, Horaria) (linea 688)

nueva = []
i = 0
skip_until = -1

while i < len(lineas):
    l = lineas[i]

    # Saltar bloque completo # MODULO 1: HORARIA hasta # MODULO 2
    if '# MODULO 1: HORARIA' in l:
        # saltar hasta MODULO 2
        while i < len(lineas) and '# MODULO 2:' not in lineas[i]:
            i += 1
        continue  # no incrementar, el while lo hará

    # Saltar tab_horaria = _build_horaria()
    if re.match(r'^tab_horaria\s*=', l.strip()):
        i += 1; continue

    # Quitar tab_horaria de TABS.children y ajustar titles
    if 'tab_horaria' in l:
        i += 1; continue

    # Ajustar set_title: si era title(1,'Horaria') lo quitamos,
    # y reindexamos los siguientes (2→1, 3→2, 4→3, 5→4, 6→5)
    m = re.match(r"TABS\.set_title\((\d+),\s*'(.+?)'\)", l.strip())
    if m:
        idx = int(m.group(1)); ttl = m.group(2)
        if ttl == '☽ Horaria':
            i += 1; continue  # eliminar
        if idx > 1:  # reindexar: 2→1, 3→2, etc.
            indent = len(l) - len(l.lstrip())
            l = ' '*indent + f"TABS.set_title({idx-1}, '{ttl}')"

    nueva.append(l)
    i += 1

print(f'Lineas después: {len(nueva)}')

# Reconstruir source como lista de strings para Jupyter
new_src = '\n'.join(nueva)
nb['cells'][2]['source'] = [line + '\n' for line in new_src.split('\n')]
# quitar ultimo \n extra
if nb['cells'][2]['source'] and nb['cells'][2]['source'][-1] == '\n':
    nb['cells'][2]['source'][-1] = ''

with open(NB, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('Notebook guardado OK')
print('Verificar: tab_horaria restantes =', new_src.count('tab_horaria'))
print('Verificar: _build_horaria restantes =', new_src.count('_build_horaria'))
