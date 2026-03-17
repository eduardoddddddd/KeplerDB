# =============================================================================
# app.py  —  KeplerDB Web App
# Flask app standalone: calcula carta natal + interpretaciones Kepler
# Ejecutar: py -X utf8 app.py  →  abre http://localhost:5000
# =============================================================================
import sys, os, io, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify
import swisseph as swe
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import kepler_interp as ki

swe.set_ephe_path(None)
app = Flask(__name__)

SIGN_ESP = ['Aries','Tauro','Géminis','Cáncer','Leo','Virgo',
            'Libra','Escorpio','Sagitario','Capricornio','Acuario','Piscis']
SIGN_GLYPHS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
PLANET_GLYPHS = {
    'Sol':'☉','Luna':'☽','Mercurio':'☿','Venus':'♀','Marte':'♂',
    'Jupiter':'♃','Saturno':'♄','Urano':'⛢','Neptuno':'♆','Pluton':'♇','NodoN':'☊'
}
PCOLS = {
    'Sol':'#FFD700','Luna':'#AAAAFF','Mercurio':'#FFAA44','Venus':'#88EE88',
    'Marte':'#FF5555','Jupiter':'#CC88FF','Saturno':'#88CCFF',
    'Urano':'#44DDCC','Neptuno':'#8888FF','Pluton':'#FF88AA','NodoN':'#FFAA00'
}
SISTEMAS = {'Placidus':b'P','Koch':b'K','Whole Sign':b'W',
            'Equal':b'E','Campanus':b'C','Regiomontanus':b'R'}
PLANET_IDS = {
    'Sol':swe.SUN,'Luna':swe.MOON,'Mercurio':swe.MERCURY,
    'Venus':swe.VENUS,'Marte':swe.MARS,'Jupiter':swe.JUPITER,
    'Saturno':swe.SATURN,'Urano':swe.URANUS,'Neptuno':swe.NEPTUNE,'Pluton':swe.PLUTO
}

def deg_to_sign(deg):
    deg = deg % 360
    s = int(deg/30); d = deg%30; m = int((d%1)*60)
    return SIGN_ESP[s], int(d), m, s

def which_house(lon, cusps):
    for i in range(12):
        s = cusps[i]%360; e = cusps[(i+1)%12]%360; l = lon%360
        if s<=e:
            if s<=l<e: return i+1
        else:
            if l>=s or l<e: return i+1
    return 1

def asp_short(angle, orbe=8):
    for deg,name in [(0,'Conj'),(60,'Sext'),(90,'Cuad'),(120,'Trig'),(180,'Opoc')]:
        d = min(abs(angle-deg), abs(angle-(360-deg)))
        if d<=orbe: return name, round(d,2)
    return None, None

def calcular_carta(Y,M,D,h,m,off,lat,lon_geo,sistema='Regiomontanus'):
    H_utc = h + off + m/60.0   # off=-1 para UTC+1 (España invierno)
    JD = swe.julday(Y,M,D,H_utc)
    sis_b = SISTEMAS.get(sistema, b'R')
    cusps, ascmc = swe.houses(JD, lat, lon_geo, sis_b)
    ASC, MC = ascmc[0], ascmc[1]
    planets_raw = {}
    for name, pid in PLANET_IDS.items():
        res = swe.calc_ut(JD, pid)
        planets_raw[name] = {'lon': res[0][0], 'spd': res[0][3]}
    nn = swe.calc_ut(JD, swe.TRUE_NODE)
    planets_raw['NodoN'] = {'lon': nn[0][0], 'spd': nn[0][3]}
    return {
        'JD': JD, 'ASC': ASC, 'MC': MC,
        'cusps': list(cusps),
        'planets': {k:v['lon'] for k,v in planets_raw.items()},
        'planets_spd': {k:v['spd'] for k,v in planets_raw.items()},
        'sistema': sistema,
    }

def rueda_png(carta, nombre='', fecha=''):
    """Genera rueda zodiacal como PNG base64."""
    planets = carta['planets']
    cusps   = carta['cusps']
    ASC     = carta['ASC']
    fig, ax = plt.subplots(1,1, figsize=(8,8),
                           subplot_kw={'projection':'polar'}, facecolor='#ffffff')
    ax.set_facecolor('#f8f9fa')
    lp = lambda lon: np.radians(180.0+(lon-ASC)%360) % (2*np.pi)

    R_OUT=1.0; R_ZO=0.92; R_ZI=0.78; R_HO=0.76; R_HI=0.56; R_PL=0.72

    # Fondo signos
    ELEM_COLS=['#fff0f0','#f0fff0','#f0f0ff','#f5f0ff']
    for i in range(12):
        t1 = lp(i*30); t2 = lp((i+1)*30)
        if t2 < t1: t1, t2 = t2, t1
        if t2-t1 > np.pi: t1 += 2*np.pi
        tv = np.linspace(t1, t2, 40) % (2*np.pi)
        col = ELEM_COLS[i%4]
        ax.fill_between(tv, R_ZI, R_ZO, color=col, alpha=0.7)
        ax.fill_between(tv, R_ZI, R_ZO, color='none',
                        edgecolor='#334466', linewidth=0.5)
        mid = np.radians(180.0+((i+0.5)*30-ASC)%360) % (2*np.pi)
        ax.text(mid, (R_ZI+R_ZO)/2, SIGN_GLYPHS[i],
                ha='center', va='center', fontsize=11,
                color='#3949ab', fontweight='bold')

    # Casas
    for i, c in enumerate(cusps):
        th = lp(c)
        lw = 1.6 if i in (0,3,6,9) else 0.7
        col = '#6688aa' if i in (0,3,6,9) else '#334455'
        ax.plot([th,th],[R_HI,R_ZI], color=col, lw=lw, zorder=5)
        ax.text(th, R_HI-0.04, str(i+1), ha='center', va='center',
                fontsize=7, color='#424242')

    ax.fill_between(np.linspace(0,2*np.pi,360), R_HI, R_HI, color='none',
                    edgecolor='#334466', linewidth=0.5)

    # Planetas
    ORDEN = ['Sol','Luna','Mercurio','Venus','Marte','Jupiter',
             'Saturno','Urano','Neptuno','Pluton','NodoN']
    for pname in ORDEN:
        if pname not in planets: continue
        lon = planets[pname]
        th = lp(lon)
        col = PCOLS.get(pname, '#ffffff')
        glyph = PLANET_GLYPHS.get(pname, pname[:2])
        ax.text(th, R_PL, glyph, ha='center', va='center',
                fontsize=13, color=col, fontweight='bold', zorder=9)
        ax.plot([th,th],[R_PL+0.09, R_ZI-0.01],
                color=col, lw=0.5, alpha=0.4, zorder=3)

    ax.text(0, 0, '☽', ha='center', va='center',
            fontsize=18, color='#3949ab', zorder=10)
    titulo = f'{nombre}  {fecha}' if nombre else fecha
    if titulo:
        ax.set_title(titulo, color='#424242', fontsize=9, pad=6)
    ax.set_rticks([]); ax.set_xticks([])
    ax.spines['polar'].set_visible(False)
    ax.set_ylim(0, 1.01)
    plt.tight_layout(pad=0.2)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=140,
                facecolor='#ffffff', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


@app.route('/')
def index():
    return render_template('index.html', sistemas=list(SISTEMAS.keys()))

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        d = request.json
        Y,M,D   = int(d['anio']), int(d['mes']), int(d['dia'])
        h,m,off = int(d['hora']), int(d['min']), float(d['offset'])
        lat      = float(d['lat'])
        lon_geo  = float(d['lon'])
        nombre   = d.get('nombre','Sin nombre')
        sistema  = d.get('sistema','Regiomontanus')

        carta = calcular_carta(Y,M,D,h,m,off,lat,lon_geo,sistema)
        fecha_str = f'{D:02d}/{M:02d}/{Y} {h:02d}:{m:02d}h'

        # Tabla de posiciones
        tabla = []
        ORDEN = ['Sol','Luna','Mercurio','Venus','Marte','Jupiter',
                 'Saturno','Urano','Neptuno','Pluton','NodoN']
        ASP_FULL = {'Conj':'Conjunción','Sext':'Sextil',
                    'Cuad':'Cuadratura','Trig':'Trígono','Opoc':'Oposición'}
        for pname in ORDEN:
            if pname not in carta['planets']: continue
            lon = carta['planets'][pname]
            sig, deg, minn, _ = deg_to_sign(lon)
            casa = which_house(lon, carta['cusps'])
            spd  = carta['planets_spd'].get(pname, 0)
            retro = ' ℞' if spd < 0 else ''
            tabla.append({
                'planeta': pname,
                'glyph':   PLANET_GLYPHS.get(pname,''),
                'pos':     f"{deg}°{sig[:3]}{minn:02d}'",
                'signo':   sig,
                'casa':    casa,
                'retro':   retro,
                'color':   PCOLS.get(pname,'#fff'),
            })

        # ASC y MC
        asc_sig, asc_d, asc_m, _ = deg_to_sign(carta['ASC'])
        mc_sig,  mc_d,  mc_m,  _ = deg_to_sign(carta['MC'])

        # Aspectos
        aspectos = []
        planet_lons = [(n, carta['planets'][n]) for n in ORDEN if n in carta['planets']]
        ASP_CLR = {'Conj':'#bb8800','Trig':'#226622','Sext':'#224488',
                   'Cuad':'#882200','Opoc':'#880022'}
        for i in range(len(planet_lons)):
            for j in range(i+1, len(planet_lons)):
                n1,lon1 = planet_lons[i]; n2,lon2 = planet_lons[j]
                ang = abs(lon1-lon2)%360
                if ang>180: ang=360-ang
                asp, orb = asp_short(ang)
                if asp:
                    aspectos.append({
                        'p1':n1,'p2':n2,
                        'asp': ASP_FULL.get(asp,asp),
                        'orb': orb,
                        'col': ASP_CLR.get(asp,'#555'),
                    })

        # Rueda
        rueda_b64 = rueda_png(carta, nombre, fecha_str)

        # Interpretaciones Kepler
        carta_ki = {
            'nombre': nombre, 'fecha_str': fecha_str,
            'sistema': sistema,
            'ASC': carta['ASC'], 'MC': carta['MC'],
            'cusps': carta['cusps'],
            'planets': carta['planets'],
            'planets_spd': carta['planets_spd'],
        }
        import importlib; importlib.reload(ki)
        kepler_html = ki.generar_informe_completo(carta_ki)

        return jsonify({
            'ok': True,
            'tabla': tabla,
            'asc': f"{asc_d}°{asc_sig[:3]}{asc_m:02d}'",
            'mc':  f"{mc_d}°{mc_sig[:3]}{mc_m:02d}'",
            'aspectos': aspectos,
            'rueda': rueda_b64,
            'kepler': kepler_html,
            'nombre': nombre,
            'fecha': fecha_str,
        })
    except Exception as e:
        import traceback
        return jsonify({'ok': False, 'error': traceback.format_exc()})

if __name__ == '__main__':
    import webbrowser, threading
    threading.Timer(1.2, lambda: webbrowser.open('http://localhost:5000')).start()
    print('KeplerDB App → http://localhost:5000')
    app.run(debug=False, port=5000)
