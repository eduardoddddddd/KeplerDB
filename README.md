# KeplerDB 🔭

Aplicación web local que reproduce las interpretaciones astrológicas del programa **Kepler 4** (Miguel García, 1985) sobre cálculos astronómicos precisos con **pyswisseph** (Swiss Ephemeris).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 · Flask |
| Astronomía | pyswisseph (Swiss Ephemeris) |
| Base de datos | SQLite (`kepler.db`) · 597 textos originales |
| Frontend | HTML/CSS/JS vanilla (sin dependencias) |
| Gráficos | matplotlib (rueda zodiacal) |

## Arranque

```bash
py -X utf8 app\app.py
# → http://localhost:5000
```

## Estructura del proyecto

```
KeplerDB/
├── app/
│   ├── app.py              # Servidor Flask + endpoints
│   └── templates/
│       └── index.html      # UI completa (single-page)
├── kepler_interp.py        # Motor de interpretaciones (consulta kepler.db)
├── kepler.db               # Base de datos SQLite con textos Kepler 4
└── README.md
```

## Base de datos — kepler.db

597 textos extraídos del Kepler 4 original, distribuidos en 6 ficheros:

| Fichero | Registros | Contenido |
|---|---|---|
| `PLANETAS.ASC` | 120 | 10 planetas × 12 signos/casas |
| `REGENTES.ASC` | 144 | Regente de casa N en casa M (12×12) |
| `ASPECTOS.ASC` | 136 | Aspectos entre planetas (Conj/Armónico/Tensión) |
| `ASCEN.ASC` | 12 | Ascendente en cada signo |
| `SOL.ASC` | 12 | Sol en cada signo (textos extendidos) |
| `PAREJA.ASC` | 173 | Sinastría: aspectos entre planetas de dos cartas |

### Codificación PAREJA.ASC

Clave: `XYZ` donde X=planeta1, Y=planeta2, Z=B(enigno)/M(aligno)

| Código | Planeta |
|---|---|
| E | Sol | L | Luna | H | Mercurio | V | Venus | M | Marte |
| J | Júpiter | S | Saturno | U | Urano | N | Neptuno | P | Plutón |
| A | ASC | C | MC | D | Nodo Norte |

B = Conjunción/Trígono/Sextil · M = Cuadratura/Oposición

## Funcionalidades

### 1. Carta Natal
- Cálculo con pyswisseph: 10 planetas + Nodo Norte verdadero
- Sistemas de casas: Placidus, Koch, Regiomontanus, Whole Sign, Equal, Campanus
- Rueda zodiacal (matplotlib, fondo blanco, colores pastel por elemento)
- Tabla de posiciones con grado/signo/casa/retrogradación
- Tabla de aspectos con orbe
- Guardar/cargar/borrar cartas (JSON en `~/astro_cartas/`)

### 2. Informe Kepler (tab 📖)
Secciones en orden:

1. **🌅 Ascendente** — texto ASCEN.ASC para el signo ascendente
2. **⚖️ Mayorías Planetarias** — conteo por elemento (Fuego/Tierra/Aire/Agua) y modalidad (Cardinal/Fijo/Mutable) con tarjetas de color
3. **🪐 Planetas en Signo** — para cada planeta:
   - ☉ Texto SOL.ASC (solo Sol, más descriptivo)
   - 📍 Texto por signo (PLANETAS.ASC)
   - 🏠 Texto por casa si difiere del signo
4. **⚡ Aspectos** — textos ASPECTOS.ASC para cada aspecto activo (orbe 8°)
5. **🏛️ Regentes de Casas** — para cada casa: regente clásico, su posición y texto REGENTES.ASC

### 3. Tránsitos (tab 🌍)
- Selector de fecha (rellena automáticamente con hoy)
- Calcula planetas transitantes con pyswisseph para esa fecha
- Orbes diferenciados: Luna 1°, Sol/inferiores 2°, superiores (Jup-Plu) 3°
- Detecta retrogradación (muestra ℞)
- Textos de ASPECTOS.ASC (mismos que natal — Kepler 4 no distinguía)
- Ordenados: primero los que tienen texto, luego por orbe creciente
- Aspectos sin texto se muestran atenuados (sin texto en DB)

### 4. Sinastría (tab 💞)
- Formulario independiente para 2 personas (con botón "Cargar carta natal → P1")
- Orbe configurable (por defecto 6°)
- Busca aspectos entre todos los planetas de P1 y P2 (incluye ASC y MC)
- Textos de PAREJA.ASC — busca en ambos órdenes (XY e YX)
- Iconos astrológicos: ☌ △ ⚹ □ ☍
- Ordenados: con texto primero, luego por orbe

## Motor de interpretaciones — kepler_interp.py

Funciones principales:

```python
get_planeta(planeta, signo, casa)      # Textos PLANETAS.ASC + SOL.ASC
get_aspecto(p1, p2, asp)               # Texto ASPECTOS.ASC
get_transito(p_trans, p_natal, asp)    # Alias de get_aspecto para tránsitos
get_regente(casa_origen, casa_regente) # Texto REGENTES.ASC
get_sinastria(p1, p2, asp)             # Texto PAREJA.ASC
mayorias_planetarias(planets_lon)      # Conteo por elemento y modalidad
generar_informe_completo(carta)        # HTML completo del informe natal
generar_informe_sinastria(c1, c2)      # HTML completo de sinastría
```

### Nombres de planetas (dashboard → DB)

```python
PLANET_MAP = {
    'Sol':'Sol', 'Luna':'Luna', 'Mercurio':'Mercurio', 'Venus':'Venus',
    'Marte':'Marte', 'Jupiter':'Júpiter', 'Saturno':'Saturno',
    'Urano':'Urano', 'Neptuno':'Neptuno', 'Pluton':'Plutón',
    'NodoN':'Nodo Norte', 'ASC':'Ascendente', 'MC':'Medio Cielo',
}
```

## Endpoints Flask

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/calcular` | Carta natal completa (planetas, casas, aspectos, rueda, informe Kepler) |
| POST | `/transitos` | Tránsitos de una fecha sobre carta natal |
| POST | `/sinastria` | Sinastría entre dos cartas |
| POST | `/cartas/guardar` | Guardar carta como JSON |
| GET | `/cartas/listar` | Listar cartas guardadas |
| GET | `/cartas/cargar/<nombre>` | Cargar carta guardada |
| DELETE | `/cartas/borrar/<nombre>` | Borrar carta guardada |

## Regencias clásicas usadas para Regentes

Marte→Aries/Escorpio · Venus→Tauro/Libra · Mercurio→Géminis/Virgo  
Luna→Cáncer · Sol→Leo · Júpiter→Sagitario/Piscis · Saturno→Capricornio/Acuario

## Notas técnicas

- Ejecutar siempre con `py -X utf8` para evitar problemas de encoding en Windows
- Flask en modo `debug=False` — matar proceso antes de relanzar (no recarga automático)
- `importlib.reload(ki)` en cada request para desarrollo sin reinicio
- Cartas guardadas en `%USERPROFILE%\astro_cartas\` como JSON
- DB en ruta absoluta: `C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db`

## Roadmap pendiente

- [ ] Tab Famosos/Eventos — búsqueda en tabla `cartas` (8502 registros)
- [ ] Retorno Solar
- [ ] Firdaria / Profecciones anuales
- [ ] Exportar informe a PDF
