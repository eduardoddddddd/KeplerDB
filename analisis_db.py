import sqlite3
conn = sqlite3.connect(r'C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db')
cur = conn.cursor()
print('=== ASPECTOS primeros 10 asignados ===')
cur.execute("""SELECT indice,planeta1,planeta2,aspecto,cabecera
    FROM interpretaciones WHERE fichero='ASPECTOS.ASC' AND planeta1 IS NOT NULL
    ORDER BY indice LIMIT 10""")
for r in cur.fetchall():
    print(f'  [{r[0]:3d}] {str(r[1]):<12} {str(r[2]):<12} {str(r[3]):<14}  {r[4]}')
print()
print('=== Sol-Luna los 3 tipos ===')
cur.execute("""SELECT aspecto,cabecera FROM interpretaciones
    WHERE fichero='ASPECTOS.ASC' AND planeta1='Sol' AND planeta2='Luna'""")
for r in cur.fetchall(): print(f'  {str(r[0]):<14} {r[1]}')
print()
print('=== Sol-Saturno ===')
cur.execute("""SELECT aspecto,cabecera FROM interpretaciones
    WHERE fichero='ASPECTOS.ASC' AND planeta1='Sol' AND planeta2='Saturno'""")
for r in cur.fetchall(): print(f'  {str(r[0]):<14} {r[1]}')
conn.close()
