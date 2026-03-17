# =============================================================================
# build_kepler_db.py  —  KeplerDB Builder v2
# Kepler 4 (Miguel García)  →  SQLite consultable
# Autor: Eduardo + Claude  |  2026-03-17
# =============================================================================
import sqlite3, os, re

KEPLER_DIR = r"C:\Program Files (x86)\Kepler 4"
DB_PATH    = r"C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db"
ENC        = "cp850"

SIGNOS = {1:"Aries",2:"Tauro",3:"Géminis",4:"Cáncer",5:"Leo",6:"Virgo",
          7:"Libra",8:"Escorpio",9:"Sagitario",10:"Capricornio",11:"Acuario",12:"Piscis"}
PLANETAS = {"SOL":"Sol","LUN":"Luna","MER":"Mercurio","VEN":"Venus",
            "MAR":"Marte","JUP":"Júpiter","SAT":"Saturno",
            "URA":"Urano","NEP":"Neptuno","PLU":"Plutón",
            "ASC":"Ascendente","MC":"Medio Cielo","NOD":"Nodo Norte","LIL":"Lilith"}
ASPECTOS = {"CONJUNCION":"Conjunción","CONJUNCI":"Conjunción","OPOSICION":"Oposición",
            "TRIGONO":"Trígono","CUADRATURA":"Cuadratura","SEXTIL":"Sextil",
            "QUINCUN":"Quincuncio","SESQUI":"Sesquicuadratura","QUINTIL":"Quintil"}

def leer(nombre):
    ruta = os.path.join(KEPLER_DIR, nombre)
    if not os.path.exists(ruta): return None
    return open(ruta,"rb").read().decode(ENC, errors="replace")


def parsear_asc(nombre):
    """Parser formato estándar: bloques separados por línea '#' sola"""
    txt = leer(nombre)
    if not txt: print(f"  [!] No encontrado: {nombre}"); return []
    bloques = []
    partes = re.split(r'(?m)^#\s*$', txt)
    if len(partes) <= 1:
        partes = re.split(r'\n#\n|\r\n#\r\n', txt)
    for i, parte in enumerate(partes):
        parte = parte.strip()
        if not parte: continue
        lineas = parte.split("\n")
        cabecera = lineas[0].strip().rstrip(".")
        texto = " ".join(l.strip() for l in lineas[1:] if l.strip())
        texto = re.sub(r'\s+', ' ', texto).strip()
        if cabecera and texto:
            bloques.append({"indice":i+1,"cabecera":cabecera,"texto":texto,"fichero":nombre})
    return bloques

def parsear_asc_pareja(nombre):
    """Parser formato PAREJA.ASC: bloques separados por ==COD al inicio de línea"""
    txt = leer(nombre)
    if not txt: return []
    bloques = []
    partes = re.split(r'(?m)^==', txt)
    for i, parte in enumerate(partes):
        parte = parte.strip()
        if not parte: continue
        lineas = [l.strip() for l in parte.split("\n") if l.strip()]
        if not lineas: continue
        codigo = lineas[0].strip()   # ej: "EAB"
        texto  = " ".join(lineas[1:])
        texto  = re.sub(r'\s+', ' ', texto).strip()
        # Decodificar el código: 3 letras
        # Posición 1: tipo aspecto (E=Sol-relacionado, L=Luna, M=Marte...)
        # Posición 2: subgrupo planetario
        # Posición 3: B=Beneficioso, M=Maléfico/Tenso
        valencia = "Beneficioso" if codigo.endswith("B") else ("Tenso" if codigo.endswith("M") else "")
        cabecera = f"Sinastría {codigo}" + (f" ({valencia})" if valencia else "")
        if codigo and texto:
            bloques.append({
                "indice": i, "cabecera": cabecera, "texto": texto,
                "fichero": nombre, "codigo_pareja": codigo, "valencia": valencia
            })
    return bloques

def parsear_asc_figuras(nombre):
    """FIGURASD.ASC: documento de congreso, texto libre, guardamos como bloques por párrafo"""
    txt = leer(nombre)
    if not txt: return []
    # Separar por párrafos vacíos dobles
    partes = re.split(r'\n{3,}', txt)
    bloques = []
    for i, parte in enumerate(partes):
        parte = parte.strip()
        if len(parte) < 40: continue  # ignorar líneas cortas/títulos solos
        lineas = [l.strip() for l in parte.split("\n") if l.strip()]
        cabecera = lineas[0][:80]
        texto = " ".join(lineas)
        texto = re.sub(r'\s+', ' ', texto).strip()
        bloques.append({"indice":i+1,"cabecera":cabecera,"texto":texto,"fichero":nombre})
    return bloques


def inferir(cab):
    c = cab.upper()
    m = {"planeta1":None,"planeta2":None,"signo":None,"casa":None,"aspecto":None}
    for cod,nom in PLANETAS.items():
        if c.startswith(cod) or f" {cod} " in c: m["planeta1"]=nom; break
    for cod,nom in ASPECTOS.items():
        if cod in c:
            m["aspecto"]=nom
            idx = c.find(cod)+len(cod)
            for cod2,nom2 in PLANETAS.items():
                if c[idx:].strip().startswith(cod2): m["planeta2"]=nom2; break
            break
    for num,sig in SIGNOS.items():
        if sig.upper() in c or sig[:3].upper() in c: m["signo"]=sig; break
    mc = re.search(r'CASA\s+(\d+)', c)
    if mc: m["casa"]=int(mc.group(1))
    return m

def parsear_dat(nombre):
    txt = leer(nombre)
    if not txt: return []
    cartas = []
    for linea in txt.replace("\r\n","\n").split("\n"):
        linea = linea.strip()
        if not linea or not linea.startswith("\\"): continue
        c = {"fichero_origen":nombre}
        partes = re.split(r'\\([A-Z])>', linea)
        i = 1
        while i < len(partes)-1:
            k, v = partes[i], partes[i+1].strip(); i+=2
            if k=="S":
                mm = re.match(r'(\d{4})-\s*(\d+)-\s*(\d+)\s+(\d+):\s*(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)',v)
                if mm:
                    c["anio"]=int(mm.group(1)); c["mes"]=int(mm.group(2)); c["dia"]=int(mm.group(3))
                    c["hora"]=int(mm.group(4)); c["min"]=int(mm.group(5))
                    c["gmt"]=float(mm.group(6)); c["lat"]=float(mm.group(7)); c["lon"]=float(mm.group(8))
            elif k=="N": c["nombre"]=v
            elif k=="L": c["lugar"]=v
            elif k=="D":
                c["tags"]=",".join(re.findall(r':([A-Z]):', v))
                c["descripcion"]=re.sub(r'(:[A-Z]:)+','',v).strip().lstrip(":")
            elif k=="A": c["fecha_sesion"]=v
        if "nombre" in c: cartas.append(c)
    return cartas


def crear_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS interpretaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fichero TEXT NOT NULL, indice INTEGER NOT NULL,
        cabecera TEXT NOT NULL, texto TEXT NOT NULL,
        planeta1 TEXT, planeta2 TEXT, signo TEXT, casa INTEGER, aspecto TEXT,
        codigo_pareja TEXT, valencia TEXT, palabras_clave TEXT
    );
    CREATE TABLE IF NOT EXISTS cartas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fichero_origen TEXT, nombre TEXT, lugar TEXT,
        anio INTEGER, mes INTEGER, dia INTEGER,
        hora INTEGER, min INTEGER, gmt REAL, lat REAL, lon REAL,
        tags TEXT, descripcion TEXT
    );
    CREATE TABLE IF NOT EXISTS rpn_scripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fichero TEXT NOT NULL, contenido TEXT NOT NULL, descripcion TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_p1  ON interpretaciones(planeta1);
    CREATE INDEX IF NOT EXISTS idx_p2  ON interpretaciones(planeta2);
    CREATE INDEX IF NOT EXISTS idx_sig ON interpretaciones(signo);
    CREATE INDEX IF NOT EXISTS idx_cas ON interpretaciones(casa);
    CREATE INDEX IF NOT EXISTS idx_asp ON interpretaciones(aspecto);
    CREATE INDEX IF NOT EXISTS idx_fic ON interpretaciones(fichero);
    CREATE INDEX IF NOT EXISTS idx_val ON interpretaciones(valencia);
    CREATE INDEX IF NOT EXISTS idx_cnm ON cartas(nombre);
    CREATE INDEX IF NOT EXISTS idx_cyr ON cartas(anio,mes,dia);
    """)
    conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS interpretaciones_fts USING fts5(
        cabecera, texto, planeta1, signo, aspecto,
        content='interpretaciones', content_rowid='id')""")
    conn.commit()
    print("  [OK] Esquema creado.")

FICHEROS_ASC = [
    ("PLANETAS.ASC","std","Planetas en signo/casa"),
    ("ASCEN.ASC",   "std","Ascendente en signo"),
    ("CASAS.ASC",   "std","Planetas en casas extendido"),
    ("REGENTES.ASC","std","Regentes de casas"),
    ("ASPECTOS.ASC","std","Aspectos entre planetas"),
    ("PAREJA.ASC",  "par","Sinastría y pareja"),
    ("FIGURASD.ASC","fig","Figuras geométricas / Estructuras Celestes"),
    ("SOL.ASC",     "std","Sol - complementario"),
]


FICHEROS_DAT = [
    "FAMOSOS.DAT","CARTAS1.DAT","CART.DAT","CMURDE.DAT","MURDE.DAT","MU.DAT",
    "FUTBOL.DAT","POLITIC.DAT","SALUD.DAT","ELCCION.DAT","CONCILIO.DAT","RIPS.DAT",
    "HORARIAS.DAT","TERREMOT.DAT","MONROE.DAT","FELIPE.DAT","MUNDIAL.DAT","MGF.DAT",
    "ESTUDI.DAT","ESTUDIO3.DAT","CESQUIZO.DAT","MEDESP.DAT","MEDFRA.DAT","CURFRA.DAT",
]
FICHEROS_RPN = [
    ("PLANETAS.RPN","Planetas signo/casa"),("CASAS.RPN","Casas"),
    ("ASPECTOS.RPN","Aspectos"),("R_SOLAR.RPN","Revolución Solar"),
    ("T_INDIVI.RPN","Tránsitos individuales"),("T_PAREJA.RPN","Tránsitos pareja"),
    ("S_PAREJA.RPN","Sinastría"),("RADICAL.RPN","Carta radical"),
    ("ESTRUC1.RPN","Estructuras 1"),("ESTRUC2.RPN","Estructuras 2"),
    ("ESTRUC3.RPN","Estructuras 3"),("ARMOGRAM.RPN","Armogramas"),
    ("ARMOPLNT.RPN","Armónicos planetas"),("ARMOLUNA.RPN","Lunaciones armónicas"),
    ("ARMOSOL.RPN","Armónicos solares"),("GENERO.RPN","Género"),
    ("ESTADO.RPN","Estado"),("SENDEROS.RPN","Senderos"),
    ("SEFIRAS.RPN","Séfiras"),("JONES.RPN","Figuras Jones"),
    ("BLOQUEOS.RPN","Bloqueos"),("MAYORIAS.RPN","Mayorías"),
]

def poblar_interpretaciones(conn):
    cur = conn.cursor(); total = 0
    for fichero, tipo, desc in FICHEROS_ASC:
        if tipo=="std":   bloques = parsear_asc(fichero)
        elif tipo=="par": bloques = parsear_asc_pareja(fichero)
        else:             bloques = parsear_asc_figuras(fichero)
        print(f"  {fichero}: {len(bloques)} bloques [{tipo}]")
        for b in bloques:
            meta = inferir(b["cabecera"])
            pal  = " ".join(b["texto"].split()[:12])
            cur.execute("""INSERT INTO interpretaciones
                (fichero,indice,cabecera,texto,planeta1,planeta2,signo,casa,aspecto,
                 codigo_pareja,valencia,palabras_clave)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (b["fichero"],b["indice"],b["cabecera"],b["texto"],
                 meta["planeta1"],meta["planeta2"],meta["signo"],meta["casa"],meta["aspecto"],
                 b.get("codigo_pareja"),b.get("valencia"),pal))
            total += 1
    conn.commit()
    cur.execute("""INSERT INTO interpretaciones_fts(rowid,cabecera,texto,planeta1,signo,aspecto)
        SELECT id,cabecera,texto,COALESCE(planeta1,''),COALESCE(signo,''),COALESCE(aspecto,'')
        FROM interpretaciones""")
    conn.commit()
    print(f"  [OK] Interpretaciones: {total}"); return total

def poblar_cartas(conn):
    cur = conn.cursor(); total = 0
    for f in FICHEROS_DAT:
        ruta = os.path.join(KEPLER_DIR, f)
        if not os.path.exists(ruta) or os.path.getsize(ruta)==0: continue
        cartas = parsear_dat(f)
        print(f"  {f}: {len(cartas)} cartas")
        for c in cartas:
            cur.execute("""INSERT INTO cartas
                (fichero_origen,nombre,lugar,anio,mes,dia,hora,min,gmt,lat,lon,tags,descripcion)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (c.get("fichero_origen"),c.get("nombre"),c.get("lugar"),
                 c.get("anio"),c.get("mes"),c.get("dia"),
                 c.get("hora"),c.get("min"),c.get("gmt"),
                 c.get("lat"),c.get("lon"),c.get("tags"),c.get("descripcion")))
            total += 1
    conn.commit(); print(f"  [OK] Cartas: {total}"); return total

def poblar_rpn(conn):
    cur = conn.cursor(); total = 0
    for f, desc in FICHEROS_RPN:
        txt = leer(f)
        if txt:
            cur.execute("INSERT INTO rpn_scripts(fichero,contenido,descripcion) VALUES(?,?,?)",(f,txt,desc))
            total += 1
    conn.commit(); print(f"  [OK] RPN: {total}"); return total


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("="*55)
    print("KeplerDB Builder v2 — Kepler 4 de Miguel García")
    print("="*55)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("  DB anterior eliminada.")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    print("\n[1] Creando esquema...")
    crear_db(conn)

    print("\n[2] Textos interpretativos (.ASC)...")
    n1 = poblar_interpretaciones(conn)

    print("\n[3] Cartas natales (.DAT)...")
    n2 = poblar_cartas(conn)

    print("\n[4] Scripts RPN...")
    n3 = poblar_rpn(conn)

    conn.close()
    kb = os.path.getsize(DB_PATH) // 1024
    print(f"""
{'='*55}
COMPLETADO
  Interpretaciones : {n1}
  Cartas natales   : {n2}
  Scripts RPN      : {n3}
  Tamaño DB        : {kb} KB
  Ruta             : {DB_PATH}
{'='*55}
""")

if __name__ == "__main__":
    main()
