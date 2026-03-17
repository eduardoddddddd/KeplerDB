# =============================================================================
# kepler_interp.py  —  Motor de interpretaciones Kepler para astro_dashboard
# Consulta kepler.db y devuelve textos interpretativos para una carta calculada
# Formato _carta_activa del dashboard:
#   planets      = {nombre: lon_float}   ← longitud directa, NO dict
#   planets_spd  = {nombre: spd_float}
#   cusps        = [lon1..lon12]          ← lista de 12 floats
#   ASC, MC      = float
# Autor: Eduardo + Claude  |  2026-03-17
# =============================================================================
import sqlite3, re

DB_PATH = r"C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db"

# Mapeo nombres dashboard → nombres en la DB
PLANET_MAP = {
    'Sol':'Sol', 'Luna':'Luna', 'Mercurio':'Mercurio', 'Venus':'Venus',
    'Marte':'Marte', 'Jupiter':'Júpiter', 'Saturno':'Saturno',
    'Urano':'Urano', 'Neptuno':'Neptuno', 'Pluton':'Plutón',
    'NodoN':'Nodo Norte', 'ASC':'Ascendente', 'MC':'Medio Cielo',
}

# Mapeo signos → nombre normalizado en DB
SIGN_MAP = {
    'Aries':'Aries','Tauro':'Tauro','Géminis':'Géminis','Geminis':'Géminis',
    'Cáncer':'Cáncer','Cancer':'Cáncer','Leo':'Leo','Virgo':'Virgo',
    'Libra':'Libra','Escorpio':'Escorpio','Sagitario':'Sagitario',
    'Capricornio':'Capricornio','Acuario':'Acuario','Piscis':'Piscis',
}

# Mapeo abreviaturas de aspecto dashboard → nombres DB
ASPECT_MAP = {
    'Conj':'Conjunción','Sext':'Sextil',
    'Cuad':'Cuadratura','Trig':'Trígono','Opoc':'Oposición',
}

SIGN_ESP = ['Aries','Tauro','Géminis','Cáncer','Leo','Virgo',
            'Libra','Escorpio','Sagitario','Capricornio','Acuario','Piscis']

def _conn():
    return sqlite3.connect(DB_PATH)

def _signo(lon):
    """Devuelve nombre de signo para una longitud eclíptica."""
    return SIGN_ESP[int((lon % 360) / 30)]

def _casa(lon, cusps):
    """Devuelve número de casa (1-12) para una longitud y lista de cúspides."""
    for i in range(12):
        s = cusps[i] % 360
        e = cusps[(i+1) % 12] % 360
        l = lon % 360
        if s <= e:
            if s <= l < e: return i+1
        else:
            if l >= s or l < e: return i+1
    return 1


def get_planeta(planeta_dash, signo_str, casa_num):
    """Texto para planeta en signo/casa."""
    p = PLANET_MAP.get(planeta_dash, planeta_dash)
    s = SIGN_MAP.get(signo_str, signo_str)
    conn = _conn(); cur = conn.cursor()
    cur.execute("""
        SELECT cabecera, texto FROM interpretaciones
        WHERE planeta1=? AND signo=?
        AND fichero IN ('PLANETAS.ASC','ASCEN.ASC','SOL.ASC')
        LIMIT 1
    """, (p, s))
    rows = cur.fetchall(); conn.close(); return rows

def get_aspecto(p1_dash, p2_dash, asp_dash):
    """Texto para aspecto entre dos planetas."""
    p1 = PLANET_MAP.get(p1_dash, p1_dash)
    p2 = PLANET_MAP.get(p2_dash, p2_dash)
    asp = ASPECT_MAP.get(asp_dash, asp_dash)
    conn = _conn(); cur = conn.cursor()
    cur.execute("""
        SELECT cabecera, texto FROM interpretaciones
        WHERE aspecto=?
          AND ((planeta1=? AND planeta2=?) OR (planeta1=? AND planeta2=?))
        AND fichero='ASPECTOS.ASC' LIMIT 1
    """, (asp, p1, p2, p2, p1))
    row = cur.fetchone(); conn.close(); return row

def busqueda_libre(query, limite=10):
    """FTS sobre todos los textos."""
    conn = _conn(); cur = conn.cursor()
    cur.execute("""
        SELECT i.fichero, i.cabecera, i.texto
        FROM interpretaciones_fts fts
        JOIN interpretaciones i ON fts.rowid=i.id
        WHERE interpretaciones_fts MATCH ?
        ORDER BY rank LIMIT ?
    """, (query, limite))
    rows = cur.fetchall(); conn.close(); return rows

def _asp_short(angle, orbe=8):
    """Devuelve (abrev, orb) para un ángulo."""
    for deg, name in [(0,'Conj'),(60,'Sext'),(90,'Cuad'),(120,'Trig'),(180,'Opoc')]:
        d = min(abs(angle-deg), abs(angle-(360-deg)))
        if d <= orbe: return name, round(d, 2)
    return None, None


def generar_informe_completo(carta_activa):
    """
    Genera informe HTML completo desde _carta_activa del dashboard.
    carta_activa['planets'] = {nombre: lon_float}   ← formato real del dashboard
    carta_activa['cusps']   = [lon1..lon12]
    """
    # --- extraer datos del formato real del dashboard ---
    planets_lon = carta_activa.get('planets', {})   # {nombre: float}
    cusps       = carta_activa.get('cusps', [i*30 for i in range(12)])
    nombre      = carta_activa.get('nombre', 'Carta')
    fecha       = carta_activa.get('fecha_str', '')
    sistema     = carta_activa.get('sistema', '')

    secciones = []

    # ── CABECERA ────────────────────────────────────────────────────────────
    secciones.append(f"""
    <div style="background:#1a2a3a;color:#e8d8b0;padding:14px 18px;
                border-radius:8px;margin-bottom:16px">
      <h2 style="margin:0;font-size:18px">📖 Interpretaciones Kepler 4 — {nombre}</h2>
      <div style="font-size:12px;color:#a0b8c8;margin-top:4px">
        {fecha} &nbsp;·&nbsp; Casas: {sistema}
        &nbsp;·&nbsp; Fuente: Kepler 4 de Miguel García
      </div>
    </div>""")

    # ── PLANETAS EN SIGNO/CASA ───────────────────────────────────────────────
    secciones.append("""<h3 style="color:#4488cc;border-bottom:1px solid #334;
        padding-bottom:4px">🪐 Planetas en Signo y Casa</h3>""")

    ORDEN = ['Sol','Luna','Mercurio','Venus','Marte','Jupiter',
             'Saturno','Urano','Neptuno','Pluton','NodoN']
    ASP_CLR = {'Conj':'#bb8800','Trig':'#226622','Sext':'#224488',
               'Cuad':'#882200','Opoc':'#880022'}

    n_planetas = 0
    for pname in ORDEN:
        if pname not in planets_lon:
            continue
        lon  = planets_lon[pname]          # ← float directo
        sig  = _signo(lon)
        casa = _casa(lon, cusps)
        deg  = int(lon % 30)
        minn = int((lon % 30 % 1) * 60)

        rows = get_planeta(pname, sig, casa)
        if not rows:
            continue

        secciones.append(f"""
        <div style="margin:12px 0 4px;font-weight:700;color:#88aadd;font-size:14px">
          {pname} en {sig} · Casa {casa}
          <span style="font-size:11px;color:#556;font-weight:normal">
            &nbsp;({deg}°{sig[:3]}{minn:02d}')
          </span>
        </div>""")

        for cab, texto in rows:
            secciones.append(f"""
        <div style="background:#1e2a1e;border-left:3px solid #446644;
                    padding:8px 12px;margin:3px 0;border-radius:0 6px 6px 0">
          <div style="font-size:11px;color:#6a8a6a;margin-bottom:3px">{cab}</div>
          <div style="font-size:13px;color:#c8dcc8;line-height:1.55">{texto}</div>
        </div>""")
            n_planetas += 1

    # ── ASPECTOS ────────────────────────────────────────────────────────────
    secciones.append("""<h3 style="color:#cc8844;border-bottom:1px solid #334;
        padding-bottom:4px;margin-top:20px">⚡ Aspectos</h3>""")

    planet_list = [(n, planets_lon[n]) for n in ORDEN if n in planets_lon]
    n_aspectos = 0

    for i in range(len(planet_list)):
        for j in range(i+1, len(planet_list)):
            n1, lon1 = planet_list[i]
            n2, lon2 = planet_list[j]
            ang = abs(lon1 - lon2) % 360
            if ang > 180: ang = 360 - ang
            asp_short, orb = _asp_short(ang)
            if not asp_short: continue
            row = get_aspecto(n1, n2, asp_short)
            if not row: continue
            cab, texto = row
            asp_full = {'Conj':'Conjunción','Sext':'Sextil','Cuad':'Cuadratura',
                        'Trig':'Trígono','Opoc':'Oposición'}.get(asp_short, asp_short)
            col = ASP_CLR.get(asp_short, '#555')
            secciones.append(f"""
        <div style="background:#1e1e2a;border-left:3px solid {col};
                    padding:8px 12px;margin:3px 0;border-radius:0 6px 6px 0">
          <div style="font-size:11px;color:#7a7aaa;margin-bottom:3px">
            {n1} <b style="color:{col}">{asp_full}</b> {n2}
            <span style="color:#445">&nbsp;(orbe {orb}°)</span>
          </div>
          <div style="font-size:13px;color:#c8c8dc;line-height:1.55">{texto}</div>
        </div>""")
            n_aspectos += 1

    if n_aspectos == 0:
        secciones.append('<div style="color:#666;font-style:italic;padding:8px">'
                         'No se encontraron aspectos con texto en la DB.</div>')

    # ── PIE ─────────────────────────────────────────────────────────────────
    secciones.append(f"""
    <div style="margin-top:16px;padding:8px 12px;background:#111;
                border-radius:6px;font-size:11px;color:#445">
      kepler.db · {n_planetas} textos de planetas · {n_aspectos} aspectos interpretados
    </div>""")

    return '\n'.join(secciones)

