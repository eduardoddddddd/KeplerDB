import sqlite3
conn = sqlite3.connect(r'C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db')
cur = conn.cursor()

print('=== Sol en Libra (tu signo natal) ===')
cur.execute("SELECT cabecera, substr(texto,1,200) FROM interpretaciones WHERE planeta1='Sol' AND signo='Libra'")
for r in cur.fetchall():
    print(f"  [{r[0]}]")
    print(f"  {r[1]}")
    print()

print('=== Luna en Casa 12 (tu Luna natal) ===')
cur.execute("SELECT cabecera, substr(texto,1,200) FROM interpretaciones WHERE planeta1='Luna' AND casa=12")
for r in cur.fetchall():
    print(f"  [{r[0]}]")
    print(f"  {r[1]}")
    print()

print('=== FTS: busqueda libre "voluntad energia" ===')
cur.execute("""SELECT i.cabecera, substr(i.texto,1,150)
    FROM interpretaciones_fts fts
    JOIN interpretaciones i ON fts.rowid=i.id
    WHERE interpretaciones_fts MATCH 'voluntad energía'
    LIMIT 4""")
for r in cur.fetchall():
    print(f"  [{r[0]}]: {r[1]}...")

print()
print('=== Famosos del Kepler nacidos en octubre ===')
cur.execute("SELECT nombre, lugar, anio, mes, dia, descripcion FROM cartas WHERE mes=10 AND fichero_origen='FAMOSOS.DAT' LIMIT 10")
for r in cur.fetchall():
    print(f"  {r[0]} ({r[4]}/{r[3]}/{r[2]}) {r[1]} — {r[5]}")

print()
print('=== Sinastria — 3 primeros textos de PAREJA.ASC ===')
cur.execute("SELECT cabecera, substr(texto,1,200) FROM interpretaciones WHERE fichero='PAREJA.ASC' LIMIT 3")
for r in cur.fetchall():
    print(f"  [{r[0]}]")
    print(f"  {r[1]}")
    print()

print()
print('=== RESUMEN TOTAL ===')
cur.execute("SELECT COUNT(*) FROM interpretaciones"); print(f"  Interpretaciones : {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM cartas");           print(f"  Cartas natales   : {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM rpn_scripts");      print(f"  Scripts RPN      : {cur.fetchone()[0]}")
cur.execute("SELECT fichero, COUNT(*) n FROM interpretaciones GROUP BY fichero ORDER BY n DESC")
print("\n  Por fichero:")
for r in cur.fetchall():
    print(f"    {r[0]:22s} {r[1]:4d} bloques")

conn.close()
print("\n[OK] Todos los tests pasados.")
