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

ELEMENTOS = {
    'Fuego': ['Aries','Leo','Sagitario'],
    'Tierra': ['Tauro','Virgo','Capricornio'],
    'Aire':   ['Géminis','Libra','Acuario'],
    'Agua':   ['Cáncer','Escorpio','Piscis'],
}
MODALIDADES = {
    'Cardinal': ['Aries','Cáncer','Libra','Capricornio'],
    'Fijo':     ['Tauro','Leo','Escorpio','Acuario'],
    'Mutable':  ['Géminis','Virgo','Sagitario','Piscis'],
}
ELEM_ICONS  = {'Fuego':'🔥','Tierra':'🌍','Aire':'💨','Agua':'💧'}
MODAL_ICONS = {'Cardinal':'⚡','Fijo':'🔷','Mutable':'🔄'}

# Regencias clásicas (dashboard key → nombre dashboard)
SIGN_RULER_CLASSIC = {
    'Aries':'Marte','Tauro':'Venus','Géminis':'Mercurio','Cáncer':'Luna',
    'Leo':'Sol','Virgo':'Mercurio','Libra':'Venus','Escorpio':'Marte',
    'Sagitario':'Jupiter','Capricornio':'Saturno','Acuario':'Saturno','Piscis':'Jupiter'
}

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
    Textos de planeta en signo (PLANETAS.ASC + SOL.ASC) y en casa (CASAS.ASC).
    """
    p = PLANET_MAP.get(planeta_dash, planeta_dash)
    s = SIGN_MAP.get(signo_str, signo_str)
    conn = _conn(); cur = conn.cursor()
    results = []

    # SOL.ASC — texto adicional solo para el Sol
    if p == 'Sol':
        cur.execute("""SELECT cabecera,texto,'sol' FROM interpretaciones
            WHERE planeta1='Sol' AND signo=? AND fichero='SOL.ASC' LIMIT 1""", (s,))
        r = cur.fetchone()
        if r: results.append(r)

    # Texto por SIGNO (PLANETAS.ASC o ASCEN.ASC)
    if p == 'Ascendente':
        cur.execute("""SELECT cabecera,texto,'signo' FROM interpretaciones
            WHERE planeta1='Ascendente' AND signo=? AND fichero='ASCEN.ASC' LIMIT 1""", (s,))
    else:
        cur.execute("""SELECT cabecera,texto,'signo' FROM interpretaciones
            WHERE planeta1=? AND signo=? AND fichero='PLANETAS.ASC' LIMIT 1""", (p, s))
    r = cur.fetchone()
    if r: results.append(r)

    # Texto por CASA (CASAS.ASC) — solo si el planeta no es ASC
    if p != 'Ascendente':
        cur.execute("""SELECT cabecera,texto,'casa' FROM interpretaciones
            WHERE signo=? AND casa=? AND fichero='CASAS.ASC' LIMIT 1""", (s, casa_num))
        r = cur.fetchone()
        if r: results.append(r)

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

def get_regente(casa_origen, casa_del_regente):
    """
    Texto REGENTES.ASC: regente de casa N ubicado en casa M.
    Cabecera en DB: 'REGENTE DE CASA N EN SIGNO O CASA M' (M = índice natural del signo).
    Consulta por LIKE para tolerar variantes de formato.
    """
    conn = _conn(); cur = conn.cursor()
    cur.execute("""SELECT cabecera, texto FROM interpretaciones
        WHERE fichero='REGENTES.ASC'
        AND cabecera LIKE ? LIMIT 1""",
        (f'REGENTE DE CASA {casa_origen} %CASA {casa_del_regente}',))
    row = cur.fetchone(); conn.close(); return row


def mayorias_planetarias(planets_lon):
    """
    Cuenta planetas por elemento y modalidad.
    Devuelve dict con conteos y lista de planetas por grupo.
    """
    ORDEN = ['Sol','Luna','Mercurio','Venus','Marte','Jupiter',
             'Saturno','Urano','Neptuno','Pluton','NodoN']
    elem_count  = {k: [] for k in ELEMENTOS}
    modal_count = {k: [] for k in MODALIDADES}
    for pname in ORDEN:
        if pname not in planets_lon: continue
        sig = _signo(planets_lon[pname])
        for elem, signs in ELEMENTOS.items():
            if sig in signs: elem_count[elem].append(pname)
        for mod, signs in MODALIDADES.items():
            if sig in signs: modal_count[mod].append(pname)
    return {'elementos': elem_count, 'modalidades': modal_count}


def get_transito(p_trans_dash, p_natal_dash, asp_dash):
    """Tránsito: reutiliza ASPECTOS.ASC."""
    return get_aspecto(p_trans_dash, p_natal_dash, asp_dash)


# Códigos PAREJA.ASC: primera letra = planeta, tercera = B(enigno)/M(aligno)
_PAREJA_CODE = {
    'Sol':'E','Luna':'L','Mercurio':'H','Venus':'V','Marte':'M',
    'Jupiter':'J','Saturno':'S','Urano':'U','Neptuno':'N','Pluton':'P',
    'NodoN':'D','ASC':'A','MC':'C',
}
# Aspecto → B o M
_PAREJA_TIPO = {
    'Conj':'B','Trig':'B','Sext':'B',   # benignos
    'Cuad':'M','Opoc':'M',              # malignos
}
_PAREJA_TIPO_FULL = {
    'Conj':'Conjunción','Trig':'Trígono','Sext':'Sextil',
    'Cuad':'Cuadratura','Opoc':'Oposición',
}


def get_sinastria(p1_dash, p2_dash, asp_dash):
    """
    Texto de sinastría: busca en PAREJA.ASC por cabecera 'Sinastría XYZ'.
    X=código p1, Y=código p2, Z=B|M.
    Intenta ambos órdenes XY e YX (matriz triangular en DB).
    """
    c1 = _PAREJA_CODE.get(p1_dash)
    c2 = _PAREJA_CODE.get(p2_dash)
    t  = _PAREJA_TIPO.get(asp_dash)
    if not c1 or not c2 or not t:
        return None
    conn = _conn(); cur = conn.cursor()
    for key in (f'{c1}{c2}{t}', f'{c2}{c1}{t}'):
        cur.execute("""SELECT cabecera,texto FROM interpretaciones
            WHERE fichero='PAREJA.ASC' AND cabecera=? LIMIT 1""",
            (f'Sinastría {key}',))
        row = cur.fetchone()
        if row:
            conn.close(); return row
    conn.close(); return None


def generar_informe_sinastria(carta1, carta2, orbe=6):
    """
    Genera informe HTML de sinastría entre dos cartas.
    carta1/carta2: misma estructura que carta_activa (nombre, planets, ASC, MC, cusps).
    Busca aspectos p1→p2 con orbe dado y textos en PAREJA.ASC.
    """
    nombre1 = carta1.get('nombre','Persona 1')
    nombre2 = carta2.get('nombre','Persona 2')
    lons1   = carta1.get('planets', {})
    lons2   = carta2.get('planets', {})
    # Añadir ASC y MC de ambas cartas
    if carta1.get('ASC'): lons1 = dict(lons1, ASC=carta1['ASC'])
    if carta1.get('MC'):  lons1 = dict(lons1, MC=carta1['MC'])
    if carta2.get('ASC'): lons2 = dict(lons2, ASC=carta2['ASC'])
    if carta2.get('MC'):  lons2 = dict(lons2, MC=carta2['MC'])

    ORDEN = ['Sol','Luna','Mercurio','Venus','Marte','Jupiter',
             'Saturno','Urano','Neptuno','Pluton','NodoN','ASC','MC']
    ASP_COLS = {'Conj':'#f57f17','Trig':'#2e7d32','Sext':'#1565c0',
                'Cuad':'#c62828','Opoc':'#880e4f'}
    ASP_BGS  = {'Conj':'#fffde7','Trig':'#e8f5e9','Sext':'#e3f2fd',
                'Cuad':'#fce4ec','Opoc':'#fce4ec'}
    ASP_ICONS= {'Conj':'☌','Trig':'△','Sext':'⚹','Cuad':'□','Opoc':'☍'}

    sec = []
    sec.append(f"""<div style="background:#4a148c;color:#fff;padding:14px 18px;
        border-radius:8px;margin-bottom:20px">
      <div style="font-size:18px;font-weight:700">💞 Sinastría Kepler 4</div>
      <div style="font-size:13px;color:#e1bee7;margin-top:4px">
        {nombre1} ↔ {nombre2} · Orbe ±{orbe}°</div>
    </div>""")

    n_con_texto = 0; n_sin_texto = 0
    bloques = []

    for p1 in ORDEN:
        if p1 not in lons1: continue
        lon1 = lons1[p1]
        for p2 in ORDEN:
            if p2 not in lons2: continue
            lon2 = lons2[p2]
            ang  = abs(lon1 - lon2) % 360
            if ang > 180: ang = 360 - ang
            asp_s, orb_val = _asp_short(ang, orbe=orbe)
            if not asp_s: continue
            row = get_sinastria(p1, p2, asp_s)
            col  = ASP_COLS.get(asp_s,'#555')
            bg   = ASP_BGS.get(asp_s,'#f9f9f9')
            icon = ASP_ICONS.get(asp_s,'·')
            af   = _PAREJA_TIPO_FULL.get(asp_s, asp_s)
            if row:
                n_con_texto += 1
            else:
                n_sin_texto += 1
            bloques.append((orb_val, p1, p2, asp_s, af, icon, col, bg, orb_val, row))

    bloques.sort(key=lambda x: (0 if x[9] else 1, x[0]))

    for (_, p1, p2, asp_s, af, icon, col, bg, orb_val, row) in bloques:
        sig1 = _signo(lons1[p1]); sig2 = _signo(lons2[p2])
        txt_bloque = ''
        if row:
            txt_bloque = f"""<div style="font-size:13px;color:#212121;line-height:1.65;
                margin-top:6px;border-top:1px solid rgba(0,0,0,.07);padding-top:6px">{row[1]}</div>"""
        opacity = '' if row else 'opacity:0.6;'
        sec.append(f"""<div style="background:{bg};border-left:4px solid {col};
            padding:9px 14px;margin:4px 0;border-radius:0 6px 6px 0;{opacity}">
          <div style="font-size:12px;font-weight:700;color:{col}">
            <span style="font-size:15px">{icon}</span>
            <span style="color:#1a237e;margin:0 4px">{nombre1}</span>
            <b>{p1}</b> <span style="color:#757575;font-size:11px">({sig1})</span>
            <span style="font-weight:400;margin:0 4px">{af}</span>
            <span style="color:#4a148c;margin:0 4px">{nombre2}</span>
            <b>{p2}</b> <span style="color:#757575;font-size:11px">({sig2})</span>
            <span style="font-size:11px;font-weight:400;color:#9e9e9e;margin-left:6px">orbe {orb_val}°</span>
          </div>{txt_bloque}
        </div>""")

    if not bloques:
        sec.append('<p style="color:#888;font-style:italic">Sin aspectos en el orbe indicado.</p>')

    sec.append(f"""<div style="margin-top:16px;padding:8px 14px;background:#f3e5f5;
        border-radius:6px;font-size:11px;color:#6a1b9a;border:1px solid #ce93d8">
      PAREJA.ASC · {n_con_texto} aspectos con texto · {n_sin_texto} sin texto en DB
    </div>""")
    return '\n'.join(sec)


def get_planeta_rev(planeta_dash, casa_natal):
    """Texto de planeta de RS en casa natal (PLANETAS.REV)."""
    p = PLANET_MAP.get(planeta_dash, planeta_dash)
    conn = _conn(); cur = conn.cursor()
    cur.execute("""SELECT cabecera,texto FROM interpretaciones
        WHERE fichero='PLANETAS.REV' AND planeta1=? AND casa=? LIMIT 1""",
        (p, casa_natal))
    row = cur.fetchone(); conn.close(); return row

def get_casa_rev(punto_dash, casa_natal):
    """Texto de punto de RS en casa natal (CASAS.REV)."""
    p = PLANET_MAP.get(punto_dash, punto_dash)
    conn = _conn(); cur = conn.cursor()
    cur.execute("""SELECT cabecera,texto FROM interpretaciones
        WHERE fichero='CASAS.REV' AND planeta1=? AND casa=? LIMIT 1""",
        (p, casa_natal))
    row = cur.fetchone(); conn.close(); return row

def get_regente_rev(casa_natal, casa_rs):
    """Texto de regente de casa natal en casa de RS (REGENTES.REV)."""
    conn = _conn(); cur = conn.cursor()
    cur.execute("""SELECT cabecera,texto FROM interpretaciones
        WHERE fichero='REGENTES.REV' AND casa=? AND cabecera LIKE ? LIMIT 1""",
        (casa_natal, f'Regente casa natal {casa_natal} en casa RS {casa_rs}'))
    row = cur.fetchone(); conn.close(); return row


def generar_informe_rs(carta_natal, carta_rs):
    """
    Informe HTML de Revolución Solar.
    carta_natal: carta base (ASC, MC, cusps, planets)
    carta_rs: carta calculada para el año (ASC, MC, cusps, planets)
    """
    nombre  = carta_natal.get('nombre', 'Carta')
    anio_rs = carta_rs.get('anio_rs', '')
    cusps_n = carta_natal.get('cusps', [i*30 for i in range(12)])
    cusps_r = carta_rs.get('cusps', [i*30 for i in range(12)])
    planets_rs = carta_rs.get('planets', {})

    ORDEN = ['Sol','Luna','Mercurio','Venus','Marte','Jupiter',
             'Saturno','Urano','Neptuno','Pluton']
    sec = []
    sec.append(f"""<div style="background:#1b5e20;color:#fff;padding:14px 18px;
        border-radius:8px;margin-bottom:20px">
      <div style="font-size:18px;font-weight:700">☀️ Revolución Solar {anio_rs} — {nombre}</div>
      <div style="font-size:12px;color:#c8e6c9;margin-top:4px">
        Planetas RS en casas natales · Textos Kepler 4</div>
    </div>""")

    # Planetas de RS en casa natal
    sec.append("""<h3 style="color:#1b5e20;border-bottom:2px solid #1b5e20;
        padding-bottom:6px;margin:0 0 12px">🪐 Planetas RS en Casa Natal</h3>""")

    n_tex = 0
    for pname in ORDEN:
        if pname not in planets_rs: continue
        lon_rs = planets_rs[pname]
        casa_n = _casa(lon_rs, cusps_n)
        sig_rs = _signo(lon_rs)
        deg    = int(lon_rs % 30); minn = int((lon_rs % 30 % 1)*60)
        row = get_planeta_rev(pname, casa_n)
        if not row: continue
        sec.append(f"""<div style="margin:14px 0 4px">
          <b style="color:#1a237e">{pname}</b>
          <span style="color:#424242;font-size:13px"> RS en {sig_rs} · Casa natal {casa_n}</span>
          <span style="color:#9e9e9e;font-size:11px"> ({deg}°{sig_rs[:3]}{minn:02d}')</span>
        </div>
        <div style="background:#e8f5e9;border-left:4px solid #388e3c;padding:10px 14px;
            margin:2px 0 2px 16px;border-radius:0 6px 6px 0">
          <div style="font-size:10px;color:#1b5e20;font-weight:700;margin-bottom:4px;
              text-transform:uppercase">{row[0]}</div>
          <div style="font-size:13px;color:#212121;line-height:1.65">{row[1]}</div>
        </div>""")
        n_tex += 1

    # ASC de RS en casa natal
    sec.append("""<h3 style="color:#4a148c;border-bottom:2px solid #4a148c;
        padding-bottom:6px;margin:20px 0 12px">🌅 Puntos RS en Casa Natal</h3>""")

    for punto_dash, punto_key in [('ASC','ASC'),('MC','MC')]:
        lon_p = carta_rs.get(punto_key)
        if lon_p is None: continue
        casa_n = _casa(lon_p, cusps_n)
        sig_p  = _signo(lon_p)
        row = get_casa_rev(punto_dash, casa_n)
        label = 'Ascendente RS' if punto_dash == 'ASC' else 'Medio Cielo RS'
        if not row: continue
        sec.append(f"""<div style="margin:10px 0 4px">
          <b style="color:#4a148c">{label}</b>
          <span style="color:#424242;font-size:13px"> en {sig_p} · Casa natal {casa_n}</span>
        </div>
        <div style="background:#f3e5f5;border-left:4px solid #7b1fa2;padding:10px 14px;
            margin:2px 0 2px 16px;border-radius:0 6px 6px 0">
          <div style="font-size:10px;color:#4a148c;font-weight:700;margin-bottom:4px;
              text-transform:uppercase">{row[0]}</div>
          <div style="font-size:13px;color:#212121;line-height:1.65">{row[1]}</div>
        </div>""")
        n_tex += 1

    # Regentes de casas natales en casas de RS
    sec.append("""<h3 style="color:#e65100;border-bottom:2px solid #e65100;
        padding-bottom:6px;margin:20px 0 12px">🏛️ Regentes Natales en Casas RS</h3>""")

    for casa_n in range(1, 13):
        cusp_sig = _signo(cusps_n[casa_n-1])
        ruler_dash = SIGN_RULER_CLASSIC.get(cusp_sig)
        if not ruler_dash or ruler_dash not in planets_rs: continue
        lon_ruler_rs = planets_rs[ruler_dash]
        casa_rs_num  = _casa(lon_ruler_rs, cusps_r)
        row = get_regente_rev(casa_n, casa_rs_num)
        if not row: continue
        sec.append(f"""<div style="background:#fff3e0;border-left:4px solid #e65100;
            padding:9px 14px;margin:4px 0;border-radius:0 6px 6px 0">
          <div style="font-size:11px;font-weight:700;color:#e65100;margin-bottom:4px">
            Casa natal {casa_n} ({cusp_sig}) → regente {ruler_dash} en casa RS {casa_rs_num}
          </div>
          <div style="font-size:13px;color:#212121;line-height:1.65">{row[1]}</div>
        </div>""")
        n_tex += 1

    sec.append(f"""<div style="margin-top:16px;padding:8px 14px;background:#f1f8e9;
        border-radius:6px;font-size:11px;color:#33691e;border:1px solid #aed581">
      PLANETAS.REV + CASAS.REV + REGENTES.REV · {n_tex} interpretaciones
    </div>""")
    return '\n'.join(sec)


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

    # ── SECCIÓN ASC ──────────────────────────────────────────────────────────
    ASC_lon = carta_activa.get('ASC')
    if ASC_lon is not None:
        asc_sig  = _signo(ASC_lon)
        asc_deg  = int(ASC_lon % 30)
        asc_min  = int((ASC_lon % 30 % 1) * 60)
        rows_asc = get_planeta('ASC', asc_sig, 1)
        if rows_asc:
            sec.append(f"""<h3 style="color:#6d4c41;border-bottom:2px solid #6d4c41;
                padding-bottom:6px;margin:0 0 12px">🌅 Ascendente en {asc_sig}</h3>""")
            for cab, texto, _ in rows_asc:
                sec.append(f"""<div style="background:#fbe9e7;border-left:4px solid #bf360c;
                        padding:10px 14px;margin:3px 0;border-radius:0 6px 6px 0">
                      <div style="font-size:10px;color:#bf360c;font-weight:700;margin-bottom:4px;
                          text-transform:uppercase;letter-spacing:.04em">{cab}
                        <span style="color:#9e9e9e;font-weight:400">
                          ({asc_deg}°{asc_sig[:3]}{asc_min:02d}')</span></div>
                      <div style="font-size:13px;color:#212121;line-height:1.65">{texto}</div>
                    </div>""")

    # ── SECCIÓN MAYORÍAS PLANETARIAS ─────────────────────────────────────────
    mayor = mayorias_planetarias(planets_lon)
    ELEM_BGS  = {'Fuego':'#fff3e0','Tierra':'#f1f8e9','Aire':'#e3f2fd','Agua':'#ede7f6'}
    ELEM_BORD = {'Fuego':'#e65100','Tierra':'#33691e','Aire':'#0d47a1','Agua':'#4a148c'}
    MODAL_BGS  = {'Cardinal':'#fff8e1','Fijo':'#fce4ec','Mutable':'#e8f5e9'}
    MODAL_BORD = {'Cardinal':'#f9a825','Fijo':'#c62828','Mutable':'#2e7d32'}
    sec.append("""<h3 style="color:#37474f;border-bottom:2px solid #37474f;
        padding-bottom:6px;margin:20px 0 12px">⚖️ Mayorías Planetarias</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px">""")
    for elem, planetas in mayor['elementos'].items():
        n = len(planetas)
        bg = ELEM_BGS[elem]; bord = ELEM_BORD[elem]
        ic = ELEM_ICONS[elem]
        pl_str = ', '.join(planetas) if planetas else '—'
        sec.append(f"""<div style="flex:1;min-width:130px;background:{bg};border:1px solid {bord};
            border-radius:8px;padding:8px 12px">
          <div style="font-size:12px;font-weight:700;color:{bord}">{ic} {elem} <span
            style="background:{bord};color:#fff;border-radius:9px;padding:1px 7px;font-size:11px">{n}</span></div>
          <div style="font-size:11px;color:#424242;margin-top:4px">{pl_str}</div>
        </div>""")
    sec.append('</div><div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px">')
    for mod, planetas in mayor['modalidades'].items():
        n = len(planetas)
        bg = MODAL_BGS[mod]; bord = MODAL_BORD[mod]
        ic = MODAL_ICONS[mod]
        pl_str = ', '.join(planetas) if planetas else '—'
        sec.append(f"""<div style="flex:1;min-width:130px;background:{bg};border:1px solid {bord};
            border-radius:8px;padding:8px 12px">
          <div style="font-size:12px;font-weight:700;color:{bord}">{ic} {mod} <span
            style="background:{bord};color:#fff;border-radius:9px;padding:1px 7px;font-size:11px">{n}</span></div>
          <div style="font-size:11px;color:#424242;margin-top:4px">{pl_str}</div>
        </div>""")
    sec.append('</div>')

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
            if tipo == 'sol':
                label = f'☉ SOL.ASC — {cab}'
                bg_col = '#fffde7'; borde = '#f9a825'; txt_col = '#e65100'
            elif tipo == 'signo':
                label = f'📍 En signo — {cab}'
                bg_col = '#e3f2fd'; borde = '#1976d2'; txt_col = '#1565c0'
            else:  # casa — CASAS.ASC
                label = f'🏠 En casa {casa} — {cab}'
                bg_col = '#e8f5e9'; borde = '#388e3c'; txt_col = '#1b5e20'
            sec.append(f"""<div style="background:{bg_col};border-left:4px solid {borde};
                    padding:10px 14px;margin:3px 0 3px 16px;border-radius:0 6px 6px 0">
                  <div style="font-size:10px;color:{txt_col};font-weight:700;margin-bottom:4px;
                      text-transform:uppercase;letter-spacing:.04em">{label}</div>
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

    # ── SECCIÓN REGENTES DE CASAS ─────────────────────────────────────────────
    sec.append("""<h3 style="color:#1b5e20;border-bottom:2px solid #1b5e20;
        padding-bottom:6px;margin:24px 0 12px">🏛️ Regentes de Casas</h3>""")
    n_reg = 0
    for casa_n in range(1, 13):
        cusp_lon = cusps[casa_n - 1]
        cusp_sig = _signo(cusp_lon)
        ruler_dash = SIGN_RULER_CLASSIC.get(cusp_sig)
        if not ruler_dash or ruler_dash not in planets_lon: continue
        ruler_lon  = planets_lon[ruler_dash]
        casa_ruler = _casa(ruler_lon, cusps)
        row = get_regente(casa_n, casa_ruler)
        if not row: continue
        cab, texto = row
        ruler_sig = _signo(ruler_lon)
        sec.append(f"""<div style="background:#f1f8e9;border-left:4px solid #2e7d32;
            padding:10px 14px;margin:4px 0;border-radius:0 6px 6px 0">
          <div style="font-size:11px;color:#1b5e20;font-weight:700;margin-bottom:4px">
            Casa {casa_n} ({cusp_sig}) → regente {ruler_dash} en {ruler_sig} · Casa {casa_ruler}
            <span style="color:#9e9e9e;font-weight:400"> — {cab}</span>
          </div>
          <div style="font-size:13px;color:#212121;line-height:1.65">{texto}</div>
        </div>""")
        n_reg += 1

    if n_reg == 0:
        sec.append('<p style="color:#888;font-style:italic">Sin textos de regentes en DB.</p>')

    # PIE
    sec.append(f"""<div style="margin-top:20px;padding:8px 14px;background:#f5f5f5;
        border-radius:6px;font-size:11px;color:#757575;border:1px solid #e0e0e0">
      kepler.db · {n_bloques} interpretaciones de planetas · {n_asp} aspectos · {n_reg} regentes
    </div>""")

    return '\n'.join(sec)
