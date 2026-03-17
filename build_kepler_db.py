# =============================================================================
# build_kepler_db.py v3  —  Reconstrucción correcta por posición
# La asignación de planeta/signo se hace por POSICIÓN en el fichero,
# no por parseo del nombre (que tiene problemas con tildes y substrings)
# =============================================================================
import sqlite3, os, re

KEPLER_DIR = r"C:\Program Files (x86)\Kepler 4"
DB_PATH    = r"C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db"
ENC        = "cp850"

SIGN_ESP = ['Aries','Tauro','Géminis','Cáncer','Leo','Virgo',
            'Libra','Escorpio','Sagitario','Capricornio','Acuario','Piscis']

# Planetas en orden del RPN (posición 1-10)
PLANET_ORDER = ['Sol','Luna','Mercurio','Venus','Marte',
                'Júpiter','Saturno','Urano','Neptuno','Plutón']

# Offsets de planetas en ASPECTOS.ASC (del RPN)
# Cada par tiene 3 bloques: conj(0), armonico(1), tension(2)
# Sol: pares con Luna,Mer,Ven,Mar,Jup,Sat,Ura,Nep,Plu = 9 pares × 3 = 27
# Luna offset=28, Mer=53, Ven=75, Mar=94, Jup=110, Sat=123, Ura=133, Nep=140
ASP_OFFSETS = {
    'Sol':      (0,  ['Luna','Mercurio','Venus','Marte','Júpiter','Saturno','Urano','Neptuno','Plutón']),
    'Luna':     (28, ['Mercurio','Venus','Marte','Júpiter','Saturno','Urano','Neptuno','Plutón']),
    'Mercurio': (53, ['Venus','Marte','Júpiter','Saturno','Urano','Neptuno','Plutón']),
    'Venus':    (75, ['Marte','Júpiter','Saturno','Urano','Neptuno','Plutón']),
    'Marte':    (94, ['Júpiter','Saturno','Urano','Neptuno','Plutón']),
    'Júpiter':  (110,['Saturno','Urano','Neptuno','Plutón']),
    'Saturno':  (123,['Urano','Neptuno','Plutón']),
    'Urano':    (133,['Neptuno','Plutón']),
    'Neptuno':  (140,['Plutón']),
}
# Tipos de aspecto por offset dentro del par (0=conj, 1=armonico, 2=tension)
ASP_TYPES = {0:'Conjunción', 1:'Armónico', 2:'Tensión'}

def leer(nombre):
    ruta = os.path.join(KEPLER_DIR, nombre)
    if not os.path.exists(ruta): return None
    return open(ruta,'rb').read().decode(ENC, errors='replace')


def split_bloques(txt):
    """Divide el fichero por separadores # y devuelve lista de (cabecera, texto)."""
    partes = re.split(r'(?m)^#\s*$', txt)
    bloques = []
    for parte in partes:
        parte = parte.strip()
        if not parte: continue
        lineas = parte.split('\n')
        cab = lineas[0].strip().rstrip('.')
        texto = ' '.join(l.strip() for l in lineas[1:] if l.strip())
        texto = re.sub(r'\s+', ' ', texto).strip()
        if cab and texto:
            bloques.append((cab, texto))
    return bloques

def parse_planetas_asc():
    """
    PLANETAS.ASC: 120 bloques, 10 planetas × 12 signos.
    Asigna planeta y signo por POSICIÓN, no por nombre.
    También asigna casa = signo_num (misma posición usada para casas en CASAS.RPN).
    """
    txt = leer('PLANETAS.ASC')
    if not txt: return []
    bloques = split_bloques(txt)
    print(f'  PLANETAS.ASC: {len(bloques)} bloques')
    rows = []
    for i, (cab, texto) in enumerate(bloques):
        pos = i + 1          # posición 1-120
        planeta_idx = (pos - 1) // 12   # 0=Sol, 1=Luna, ..., 9=Plutón
        signo_idx   = (pos - 1) % 12    # 0=Aries, ..., 11=Piscis
        if planeta_idx >= len(PLANET_ORDER): continue
        planeta = PLANET_ORDER[planeta_idx]
        signo   = SIGN_ESP[signo_idx]
        casa    = signo_idx + 1          # casa 1-12 (misma posición)
        rows.append({
            'fichero':'PLANETAS.ASC', 'indice':pos,
            'cabecera':cab, 'texto':texto,
            'planeta1':planeta, 'planeta2':None,
            'signo':signo, 'casa':casa, 'aspecto':None,
        })
    return rows

def parse_ascen_asc():
    """ASCEN.ASC: 12 bloques, Ascendente en cada signo."""
    txt = leer('ASCEN.ASC')
    if not txt: return []
    bloques = split_bloques(txt)
    print(f'  ASCEN.ASC: {len(bloques)} bloques')
    rows = []
    for i, (cab, texto) in enumerate(bloques):
        signo = SIGN_ESP[i % 12]
        rows.append({
            'fichero':'ASCEN.ASC', 'indice':i+1,
            'cabecera':cab, 'texto':texto,
            'planeta1':'Ascendente', 'planeta2':None,
            'signo':signo, 'casa':i+1, 'aspecto':None,
        })
    return rows

def parse_sol_asc():
    """SOL.ASC: 12 bloques adicionales del Sol."""
    txt = leer('SOL.ASC')
    if not txt: return []
    bloques = split_bloques(txt)
    print(f'  SOL.ASC: {len(bloques)} bloques')
    rows = []
    for i, (cab, texto) in enumerate(bloques):
        signo = SIGN_ESP[i % 12]
        rows.append({
            'fichero':'SOL.ASC', 'indice':i+1,
            'cabecera':cab, 'texto':texto,
            'planeta1':'Sol', 'planeta2':None,
            'signo':signo, 'casa':i+1, 'aspecto':None,
        })
    return rows


def parse_aspectos_asc():
    """
    ASPECTOS.ASC: 3 bloques por par (conj / armonico / tension).
    Asignación por posición usando los offsets del RPN.
    """
    txt = leer('ASPECTOS.ASC')
    if not txt: return []
    bloques = split_bloques(txt)
    print(f'  ASPECTOS.ASC: {len(bloques)} bloques')

    # Construir mapa posicion → (planeta1, planeta2, tipo_aspecto)
    asp_map = {}
    # El bloque 1 es el header ST4 — los aspectos reales empiezan en bloque 2
    # Los offsets del RPN son 0-based desde el primer aspecto real (bloque 2)
    # Por tanto en la lista de bloques (1-based): posicion = offset + j*3 + 2
    for p1_name, (offset, partners) in ASP_OFFSETS.items():
        for j, p2_name in enumerate(partners):
            base = offset + j * 3 + 2  # +2: bloque 1=header, bloques reales desde 2
            asp_map[base]     = (p1_name, p2_name, 'Conjunción')
            asp_map[base + 1] = (p1_name, p2_name, 'Armónico')
            asp_map[base + 2] = (p1_name, p2_name, 'Tensión')

    rows = []
    for i, (cab, texto) in enumerate(bloques):
        pos = i + 1
        info = asp_map.get(pos)
        if info:
            p1, p2, asp = info
        else:
            p1 = p2 = asp = None
        rows.append({
            'fichero':'ASPECTOS.ASC', 'indice':pos,
            'cabecera':cab, 'texto':texto,
            'planeta1':p1, 'planeta2':p2,
            'signo':None, 'casa':None, 'aspecto':asp,
        })
    return rows

def parse_regentes_asc():
    """REGENTES.ASC: texto para regente de casa en signo/casa."""
    txt = leer('REGENTES.ASC')
    if not txt: return []
    bloques = split_bloques(txt)
    print(f'  REGENTES.ASC: {len(bloques)} bloques')
    rows = []
    for i, (cab, texto) in enumerate(bloques):
        rows.append({
            'fichero':'REGENTES.ASC', 'indice':i+1,
            'cabecera':cab, 'texto':texto,
            'planeta1':None, 'planeta2':None,
            'signo':None, 'casa':None, 'aspecto':None,
        })
    return rows

def parse_pareja_asc():
    """PAREJA.ASC: formato ==COD."""
    txt = leer('PAREJA.ASC')
    if not txt: return []
    partes = re.split(r'(?m)^==', txt)
    rows = []
    for i, parte in enumerate(partes):
        parte = parte.strip()
        if not parte: continue
        lineas = [l.strip() for l in parte.split('\n') if l.strip()]
        if not lineas: continue
        codigo = lineas[0].strip()
        texto = ' '.join(lineas[1:])
        texto = re.sub(r'\s+', ' ', texto).strip()
        if not texto: continue
        valencia = 'Beneficioso' if codigo.endswith('B') else ('Tenso' if codigo.endswith('M') else '')
        rows.append({
            'fichero':'PAREJA.ASC', 'indice':i,
            'cabecera':f'Sinastría {codigo}',
            'texto':texto,
            'planeta1':None, 'planeta2':None,
            'signo':None, 'casa':None,
            'aspecto':None, 'codigo_pareja':codigo, 'valencia':valencia,
        })
    return rows


def parse_dat(nombre):
    txt = leer(nombre)
    if not txt: return []
    cartas = []
    for linea in txt.replace('\r\n','\n').split('\n'):
        linea = linea.strip()
        if not linea or not linea.startswith('\\'): continue
        c = {'fichero_origen':nombre}
        partes = re.split(r'\\([A-Z])>', linea)
        i = 1
        while i < len(partes)-1:
            k, v = partes[i], partes[i+1].strip(); i+=2
            if k=='S':
                mm = re.match(r'(\d{4})-\s*(\d+)-\s*(\d+)\s+(\d+):\s*(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)',v)
                if mm:
                    c['anio']=int(mm.group(1)); c['mes']=int(mm.group(2)); c['dia']=int(mm.group(3))
                    c['hora']=int(mm.group(4)); c['min']=int(mm.group(5))
                    c['gmt']=float(mm.group(6)); c['lat']=float(mm.group(7)); c['lon']=float(mm.group(8))
            elif k=='N': c['nombre']=v
            elif k=='L': c['lugar']=v
            elif k=='D':
                c['tags']=','.join(re.findall(r':([A-Z]):', v))
                c['descripcion']=re.sub(r'(:[A-Z]:)+','',v).strip().lstrip(':')
        if 'nombre' in c: cartas.append(c)
    return cartas

FICHEROS_DAT = [
    'FAMOSOS.DAT','CARTAS1.DAT','CART.DAT','CMURDE.DAT','MURDE.DAT','MU.DAT',
    'FUTBOL.DAT','POLITIC.DAT','SALUD.DAT','ELCCION.DAT','CONCILIO.DAT','RIPS.DAT',
    'HORARIAS.DAT','TERREMOT.DAT','MONROE.DAT','FELIPE.DAT','MUNDIAL.DAT','MGF.DAT',
    'ESTUDI.DAT','ESTUDIO3.DAT','CESQUIZO.DAT','MEDESP.DAT','MEDFRA.DAT','CURFRA.DAT',
]
FICHEROS_RPN = [
    ('PLANETAS.RPN','Planetas signo/casa'),('CASAS.RPN','Casas'),
    ('ASPECTOS.RPN','Aspectos'),('R_SOLAR.RPN','Revolución Solar'),
    ('T_INDIVI.RPN','Tránsitos'),('T_PAREJA.RPN','Tránsitos pareja'),
    ('S_PAREJA.RPN','Sinastría'),('RADICAL.RPN','Radical'),
    ('ESTRUC1.RPN','Estructuras 1'),('ESTRUC2.RPN','Estructuras 2'),
    ('ESTRUC3.RPN','Estructuras 3'),('ARMOGRAM.RPN','Armogramas'),
    ('ARMOPLNT.RPN','Armónicos planetas'),('ARMOLUNA.RPN','Lunaciones'),
    ('ARMOSOL.RPN','Armónicos solares'),('GENERO.RPN','Género'),
    ('ESTADO.RPN','Estado'),('SENDEROS.RPN','Senderos'),
    ('SEFIRAS.RPN','Séfiras'),('JONES.RPN','Jones'),
    ('BLOQUEOS.RPN','Bloqueos'),('MAYORIAS.RPN','Mayorías'),
]


def crear_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS interpretaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fichero TEXT NOT NULL, indice INTEGER NOT NULL,
        cabecera TEXT NOT NULL, texto TEXT NOT NULL,
        planeta1 TEXT, planeta2 TEXT, signo TEXT, casa INTEGER,
        aspecto TEXT, codigo_pareja TEXT, valencia TEXT
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
        fichero TEXT, contenido TEXT, descripcion TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_p1  ON interpretaciones(planeta1);
    CREATE INDEX IF NOT EXISTS idx_p2  ON interpretaciones(planeta2);
    CREATE INDEX IF NOT EXISTS idx_sig ON interpretaciones(signo);
    CREATE INDEX IF NOT EXISTS idx_cas ON interpretaciones(casa);
    CREATE INDEX IF NOT EXISTS idx_asp ON interpretaciones(aspecto);
    CREATE INDEX IF NOT EXISTS idx_fic ON interpretaciones(fichero);
    CREATE INDEX IF NOT EXISTS idx_cnm ON cartas(nombre);
    """)
    conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS interpretaciones_fts USING fts5(
        cabecera, texto, planeta1, signo, aspecto,
        content='interpretaciones', content_rowid='id')""")
    conn.commit()

def insertar(conn, rows):
    cur = conn.cursor()
    for r in rows:
        cur.execute("""INSERT INTO interpretaciones
            (fichero,indice,cabecera,texto,planeta1,planeta2,signo,casa,aspecto,codigo_pareja,valencia)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (r['fichero'],r['indice'],r['cabecera'],r['texto'],
             r.get('planeta1'),r.get('planeta2'),r.get('signo'),r.get('casa'),
             r.get('aspecto'),r.get('codigo_pareja'),r.get('valencia')))
    conn.commit()

def main():
    print('='*55)
    print('KeplerDB Builder v3 — indexación por posición')
    print('='*55)
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')

    print('\n[1] Esquema...'); crear_db(conn)

    print('\n[2] Interpretaciones...')
    all_rows = []
    all_rows += parse_planetas_asc()
    all_rows += parse_ascen_asc()
    all_rows += parse_sol_asc()
    all_rows += parse_aspectos_asc()
    all_rows += parse_regentes_asc()
    all_rows += parse_pareja_asc()
    insertar(conn, all_rows)

    # FTS
    cur = conn.cursor()
    cur.execute("""INSERT INTO interpretaciones_fts(rowid,cabecera,texto,planeta1,signo,aspecto)
        SELECT id,cabecera,texto,COALESCE(planeta1,''),COALESCE(signo,''),COALESCE(aspecto,'')
        FROM interpretaciones""")
    conn.commit()
    print(f'  Total interpretaciones: {len(all_rows)}')

    print('\n[3] Cartas natales...')
    total_c = 0
    cur = conn.cursor()
    for f in FICHEROS_DAT:
        ruta = os.path.join(KEPLER_DIR, f)
        if not os.path.exists(ruta) or os.path.getsize(ruta)==0: continue
        cartas = parse_dat(f)
        for c in cartas:
            cur.execute("""INSERT INTO cartas
                (fichero_origen,nombre,lugar,anio,mes,dia,hora,min,gmt,lat,lon,tags,descripcion)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (c.get('fichero_origen'),c.get('nombre'),c.get('lugar'),
                 c.get('anio'),c.get('mes'),c.get('dia'),
                 c.get('hora'),c.get('min'),c.get('gmt'),
                 c.get('lat'),c.get('lon'),c.get('tags'),c.get('descripcion')))
            total_c += 1
    conn.commit()
    print(f'  Total cartas: {total_c}')

    print('\n[4] Scripts RPN...')
    total_r = 0
    for f, desc in FICHEROS_RPN:
        txt = leer(f)
        if txt:
            cur.execute('INSERT INTO rpn_scripts(fichero,contenido,descripcion) VALUES(?,?,?)',(f,txt,desc))
            total_r += 1
    conn.commit()

    conn.close()
    kb = os.path.getsize(DB_PATH)//1024
    print(f'\n{"="*55}\nCOMPLETADO\n  Interpretaciones: {len(all_rows)}\n  Cartas: {total_c}\n  RPN: {total_r}\n  DB: {kb} KB\n{"="*55}')

if __name__=='__main__':
    main()
