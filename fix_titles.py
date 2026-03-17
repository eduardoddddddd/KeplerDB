import re

NB = r'C:\Users\Edu\Downloads\astro_dashboard_v2.ipynb'
with open(NB, encoding='utf-8') as f:
    raw = f.read()

print(f'Horaria antes: {raw.count("Horaria")}')

# 1. Eliminar fila de Horaria en la tabla markdown de la celda 0
# Patron: "| ☽ Horaria | ... |\n",
raw = re.sub(r'\s*"\\| [\u263d☽\\\\u263d]+ Horaria \\|[^"]*",\n', '\n', raw)

# 2. Eliminar línea set_title Horaria en source de celda 2
# En JSON aparece como: "TABS.set_title(1, '\\u263d Horaria')\\n",
raw = re.sub(r'\s*"TABS\\.set_title\\(1, \'\\\\u263d Horaria\'\\)\\\\n",\n', '\n', raw)

print(f'Horaria después: {raw.count("Horaria")}')

# Mostrar lo que queda si aún hay
for m in re.finditer(r'.{60}Horaria.{60}', raw):
    print('Restante:', repr(m.group()))

with open(NB, 'w', encoding='utf-8') as f:
    f.write(raw)
print('Guardado OK')
