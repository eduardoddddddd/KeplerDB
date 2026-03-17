# =============================================================================
# kepler_interp.py  —  Motor de interpretaciones Kepler para astro_dashboard
# _carta_activa formato dashboard:
#   planets      = {nombre: lon_float}
#   planets_spd  = {nombre: spd_float}
#   cusps        = [lon1..lon12]
# =============================================================================
import sqlite3, re

DB_PATH = r"C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db"

PLANET_MAP = {
    'Sol':'Sol','Luna':'Luna','Mercurio':'Mercurio','Venus':'Venus',
    'Marte':'Marte','Jupiter':'Júpiter','Saturno':'Saturno',
    'Urano':'Urano','Neptuno':'Neptuno','Pluton':'Plutón',
    'NodoN':'Nodo Norte','ASC':'Ascendente','MC':'Medio Cielo',
}
SIGN_MAP = {
    'Aries':'Aries','Tauro':'Tauro','Géminis':'Géminis','Geminis':'Géminis',
    'Cáncer':'Cáncer','Cancer':'Cáncer','Leo':'Leo','Virgo':'Virgo',
    'Libra':'Libra','Escorpio':'Escorpio','Sagitario':'Sagitario',
    'Capricornio':'Capricornio','Acuario':'Acuario','Piscis':'Piscis',
}
ASPECT_MAP = {
    'Conj':'Conjunción',
    'Sext':'Armónico',   # Trígono y Sextil → mismo bloque "ARMONICO"
    'Trig':'Armónico',
    'Cuad':'Tensión',    # Cuadratura y Oposición → mismo bloque "TENSION"
    'Opoc':'Tensión',
}
SIGN_ESP = ['Aries','Tauro','Géminis','Cáncer','Leo','Virgo',
            'Libra','Escorpio','Sagitario','Capricornio','Acuario','Piscis']

def _conn(): return sqlite3.connect(DB_PATH)

def _signo(lon): return SIGN_ESP[int((lon % 360) / 30)]

def _casa(lon, cusps):
    for i in range(12):
        s = cusps[i]%360; e = cusps[(i+1)%12]%360; l = lon%360
        if s<=e:
            if s<=l<e: return i+1
        else:
            if l>=s or l<e: return i+1
    return 1


def get_planeta(planeta_dash, signo_str, casa_num):
    """
    Devuelve textos para planeta:
    - Por signo: PLANETAS.ASC donde planeta1=P AND signo=S
    - Por casa:  PLANETAS.ASC donde planeta1=P AND casa=C
    (ambos usan PLANETAS.ASC — confirmado en CASAS.RPN)
    """
    p = PLANET_MAP.get(planeta_dash, planeta_dash)
    s = SIGN_MAP.get(signo_str, signo_str)
    conn = _conn(); cur = conn.cursor()
    results = []
    # texto por signo
    cur.execute("""SELECT cabecera,texto,'signo' FROM interpretaciones
        WHERE planeta1=? AND signo=? AND fichero='PLANETAS.ASC' LIMIT 1""", (p, s))
    r = cur.fetchone()
    if r: results.append(r)
    # texto por casa (solo si es diferente del de signo)
    if casa_num != (SIGN_ESP.index(s)+1 if s in SIGN_ESP else -1):
        cur.execute("""SELECT cabecera,texto,'casa' FROM interpretaciones
            WHERE planeta1=? AND casa=? AND fichero='PLANETAS.ASC' LIMIT 1""", (p, casa_num))
        r = cur.fetchone()
        if r: results.append(r)
    # Ascendente usa ASCEN.ASC
    if p == 'Ascendente':
        cur.execute("""SELECT cabecera,texto,'signo' FROM interpretaciones
            WHERE planeta1='Ascendente' AND signo=? AND fichero='ASCEN.ASC' LIMIT 1""", (s,))
        r = cur.fetchone()
        if r: results = [r]
    conn.close()
    return results

def get_aspecto(p1_dash, p2_dash, asp_dash):
    p1=PLANET_MAP.get(p1_dash,p1_dash); p2=PLANET_MAP.get(p2_dash,p2_dash)
    asp=ASPECT_MAP.get(asp_dash,asp_dash)
    conn=_conn(); cur=conn.cursor()
    cur.execute("""SELECT cabecera,texto FROM interpretaciones
        WHERE aspecto=? AND ((planeta1=? AND planeta2=?) OR (planeta1=? AND planeta2=?))
        AND fichero='ASPECTOS.ASC' LIMIT 1""", (asp,p1,p2,p2,p1))
    row=cur.fetchone(); conn.close(); return row

def busqueda_libre(query, limite=10):
    conn=_conn(); cur=conn.cursor()
    cur.execute("""SELECT i.fichero,i.cabecera,i.texto
        FROM interpretaciones_fts fts JOIN interpretaciones i ON fts.rowid=i.id
        WHERE interpretaciones_fts MATCH ? ORDER BY rank LIMIT ?""", (query,limite))
    rows=cur.fetchall(); conn.close(); return rows

def _asp_short(angle, orbe=8):
    for deg,name in [(0,'Conj'),(60,'Sext'),(90,'Cuad'),(120,'Trig'),(180,'Opoc')]:
        d=min(abs(angle-deg),abs(angle-(360-deg)))
        if d<=orbe: return name,round(d,2)
    return None,None


def generar_informe_completo(carta_activa):
    """Genera informe HTML fondo BLANCO con textos de signo + casa + aspectos."""
    planets_lon = carta_activa.get('planets', {})
    cusps   = carta_activa.get('cusps', [i*30 for i in range(12)])
    nombre  = carta_activa.get('nombre', 'Carta')
    fecha   = carta_activa.get('fecha_str', '')
    sistema = carta_activa.get('sistema', '')

    ORDEN = ['Sol','Luna','Mercurio','Venus','Marte','Jupiter',
             'Saturno','Urano','Neptuno','Pluton','NodoN']
    ASP_COLS = {'Conj':'#f57f17','Trig':'#2e7d32','Sext':'#1565c0',
                'Cuad':'#c62828','Opoc':'#880e4f'}
    ASP_BGS  = {'Conj':'#fffde7','Trig':'#e8f5e9','Sext':'#e3f2fd',
                'Cuad':'#fce4ec','Opoc':'#fce4ec'}
    ASP_FULL = {'Conj':'Conjunción','Sext':'Sextil','Cuad':'Cuadratura',
                'Trig':'Trígono','Opoc':'Oposición'}

    sec = []

    # CABECERA
    sec.append(f"""<div style="background:#283593;color:#fff;padding:14px 18px;
        border-radius:8px;margin-bottom:20px">
      <div style="font-size:18px;font-weight:700">📖 Interpretaciones Kepler 4 — {nombre}</div>
      <div style="font-size:12px;color:#c5cae9;margin-top:4px">{fecha} · Casas: {sistema} · Miguel García</div>
    </div>""")

    # SECCION PLANETAS EN SIGNO
    sec.append("""<h3 style="color:#1565c0;border-bottom:2px solid #1565c0;
        padding-bottom:6px;margin:0 0 12px">🪐 Planetas en Signo</h3>""")

    n_bloques = 0
    for pname in ORDEN:
        if pname not in planets_lon: continue
        lon  = planets_lon[pname]
        sig  = _signo(lon)
        casa = _casa(lon, cusps)
        deg  = int(lon % 30)
        minn = int((lon % 30 % 1) * 60)
        rows = get_planeta(pname, sig, casa)
        if not rows: continue

        sec.append(f"""<div style="margin:16px 0 6px">
          <b style="color:#1a237e;font-size:14px">{pname}</b>
          <span style="color:#424242;font-size:13px"> en {sig} · Casa {casa}</span>
          <span style="color:#9e9e9e;font-size:11px"> ({deg}°{sig[:3]}{minn:02d}')</span>
        </div>""")

        for cab, texto, tipo in rows:
            if tipo == 'signo':
                sec.append(f"""<div style="background:#e3f2fd;border-left:4px solid #1976d2;
                    padding:10px 14px;margin:3px 0 3px 16px;border-radius:0 6px 6px 0">
                  <div style="font-size:10px;color:#1565c0;font-weight:700;margin-bottom:4px;
                      text-transform:uppercase">{cab}</div>
                  <div style="font-size:13px;color:#212121;line-height:1.65">{texto}</div>
                </div>""")
            else:
                sec.append(f"""<div style="background:#f1f8e9;border-left:4px solid #558b2f;
                    padding:10px 14px;margin:3px 0 3px 16px;border-radius:0 6px 6px 0">
                  <div style="font-size:10px;color:#558b2f;font-weight:700;margin-bottom:4px;
                      text-transform:uppercase">{cab}</div>
                  <div style="font-size:13px;color:#212121;line-height:1.65">{texto}</div>
                </div>""")
            n_bloques += 1

    # SECCION ASPECTOS
    sec.append("""<h3 style="color:#6a1b9a;border-bottom:2px solid #6a1b9a;
        padding-bottom:6px;margin:24px 0 12px">⚡ Aspectos entre Planetas</h3>""")

    planet_list = [(n, planets_lon[n]) for n in ORDEN if n in planets_lon]
    n_asp = 0
    for i in range(len(planet_list)):
        for j in range(i+1, len(planet_list)):
            n1,lon1 = planet_list[i]; n2,lon2 = planet_list[j]
            ang = abs(lon1-lon2)%360
            if ang>180: ang=360-ang
            asp_s,orb = _asp_short(ang)
            if not asp_s: continue
            row = get_aspecto(n1, n2, asp_s)
            if not row: continue
            cab,texto = row
            col = ASP_COLS.get(asp_s,'#555')
            bg  = ASP_BGS.get(asp_s,'#f9f9f9')
            af  = ASP_FULL.get(asp_s, asp_s)
            sec.append(f"""<div style="background:{bg};border-left:4px solid {col};
                padding:10px 14px;margin:4px 0;border-radius:0 6px 6px 0">
              <div style="font-size:11px;color:{col};font-weight:700;margin-bottom:4px">
                {n1} — {af} — {n2}
                <span style="color:#9e9e9e;font-weight:400"> (orbe {orb}°)</span>
              </div>
              <div style="font-size:13px;color:#212121;line-height:1.65">{texto}</div>
            </div>""")
            n_asp += 1

    if n_asp == 0:
        sec.append('<p style="color:#888;font-style:italic">Sin aspectos con texto en DB.</p>')

    # PIE
    sec.append(f"""<div style="margin-top:20px;padding:8px 14px;background:#f5f5f5;
        border-radius:6px;font-size:11px;color:#757575;border:1px solid #e0e0e0">
      kepler.db · {n_bloques} interpretaciones de planetas · {n_asp} aspectos
    </div>""")

    return '\n'.join(sec)
