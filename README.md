# KeplerDB 🔭

Aplicación web local que reproduce las interpretaciones astrológicas del programa **Kepler 4** (Miguel García, 1985) sobre cálculos astronómicos precisos con **pyswisseph** (Swiss Ephemeris).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 · Flask |
| Astronomía | pyswisseph (Swiss Ephemeris) |
| Base de datos | SQLite (`kepler.db`) · 597 textos originales + 8502 cartas históricas |
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
├── kepler.db               # SQLite: textos Kepler 4 + 8502 cartas históricas
└── README.md
```

## Base de datos — kepler.db

### Textos de interpretación (597 registros)

| Fichero | Registros | Contenido |
|---|---|---|
| `PLANETAS.ASC` | 120 | 10 planetas × 12 signos/casas |
| `REGENTES.ASC` | 144 | Regente de casa N en casa M (12×12) |
| `ASPECTOS.ASC` | 136 | Aspectos entre planetas (Conj/Armónico/Tensión) |
| `ASCEN.ASC` | 12 | Ascendente en cada signo |
| `SOL.ASC` | 12 | Sol en cada signo (textos extendidos) |
| `PAREJA.ASC` | 173 | Sinastría: aspectos entre planetas de dos cartas |

### Cartas históricas (tabla `cartas`, 8502 registros)

Campos: `id, fichero_origen, nombre, lugar, anio, mes, dia, hora, min, gmt, lat, lon, tags, descripcion`

Personajes históricos, artistas, políticos, eventos. Buscable por nombre y descripción.

### Codificación PAREJA.ASC

Clave: `XYZ` donde X=planeta1, Y=planeta2, Z=B(enigno)/M(aligno)

| Código | Planeta | Código | Planeta |
|---|---|---|---|
| E | Sol | J | Júpiter |
| L | Luna | S | Saturno |
| H | Mercurio | U | Urano |
| V | Venus | N | Neptuno |
| M | Marte | P | Plutón |
| A | ASC | C | MC | D | Nodo Norte |

`B` = Conjunción / Trígono / Sextil · `M` = Cuadratura / Oposición

## Sidebar

### Cartas guardadas
Cartas calculadas y guardadas por el usuario como JSON en `%USERPROFILE%\astro_cartas\`.
- Guardar, cargar, borrar
- Disponibles en los selectores de sinastría

### ⭐ Famosos y Eventos
Búsqueda en tiempo real (debounce 300ms) sobre las 8502 cartas históricas.
- Busca por nombre o descripción (mínimo 2 caracteres)
- Máximo 20 resultados por búsqueda
- Click en resultado → rellena el formulario y calcula la carta automáticamente
- También disponible en el panel de Sinastría para P1 y P2

## Funcionalidades por tab

### 📋 Posiciones
Tabla de planetas: glifo · nombre · posición (grado°signo'min) · signo · casa · retrogradación (℞)

### ⚡ Aspectos
Tabla de aspectos activos entre planetas con orbe (máximo 8°) y código de color por tipo.

### 🔵 Rueda
Rueda zodiacal generada con matplotlib:
- Fondo blanco, colores pastel por elemento
- Glyphs de signos y planetas
- Cúspides de casas marcadas (angulares más gruesas)

### 📖 Kepler — Informe completo
Secciones en orden:

1. **🌅 Ascendente** — texto ASCEN.ASC para el signo ascendente
2. **⚖️ Mayorías Planetarias** — tarjetas de color por elemento (🔥🌍💨💧) y modalidad (⚡🔷🔄)
3. **🪐 Planetas en Signo** — por cada planeta:
   - `☉` Texto SOL.ASC (solo Sol)
   - `📍` Texto por signo (PLANETAS.ASC)
   - `🏠` Texto por casa si difiere del signo natural
4. **⚡ Aspectos** — textos ASPECTOS.ASC para cada aspecto activo
5. **🏛️ Regentes de Casas** — regente clásico de cada casa, su posición y texto REGENTES.ASC
- Botón **📄 Exportar PDF**

### 🌍 Tránsitos
- Fecha libre con selector día/mes/año + hora/min (rellena automáticamente con hoy)
- Calcula planetas transitantes con pyswisseph para esa fecha
- Orbes diferenciados por planeta: Luna 1°, Sol/inferiores 2°, superiores (Jup-Plu) 3°
- Detecta retrogradación (muestra ℞)
- Textos de ASPECTOS.ASC (Kepler 4 no distinguía natal/tránsito)
- Ordenados: con texto primero, luego por orbe creciente
- Sin texto → atenuados con indicador "sin texto en DB"
- Botón **📄 PDF**

### 💞 Sinastría
- Formulario independiente para **Persona 1** y **Persona 2**
- Cada persona puede cargarse desde:
  - Selector de cartas guardadas
  - `⭐ Buscar famoso...` — campo de búsqueda con desplegable (rosa) sobre 8502 cartas históricas
  - Botón `📋 Cargar carta natal → P1` para la carta recién calculada
- Orbe configurable (por defecto 6°)
- Busca aspectos entre todos los planetas de P1 y P2 (incluye ASC y MC)
- Textos de PAREJA.ASC — busca en ambos órdenes (XY e YX)
- Iconos astrológicos: ☌ △ ⚹ □ ☍
- Ordenados: con texto primero, luego por orbe
- Botón **📄 PDF**

### 📄 Exportar PDF (todos los informes)
- Abre ventana nueva con el informe limpio (sin sidebar ni tabs)
- Encabezado con nombre, fecha y botón 🖨️ Imprimir / PDF
- Lanza el diálogo de impresión del navegador automáticamente
- Usar "Guardar como PDF" en el destino de impresión
- Sin dependencias — usa el motor PDF del navegador

## Motor de interpretaciones — kepler_interp.py

```python
get_planeta(planeta, signo, casa)       # PLANETAS.ASC + SOL.ASC
get_aspecto(p1, p2, asp)                # ASPECTOS.ASC
get_transito(p_trans, p_natal, asp)     # alias de get_aspecto para tránsitos
get_regente(casa_origen, casa_regente)  # REGENTES.ASC (busca por LIKE en cabecera)
get_sinastria(p1, p2, asp)              # PAREJA.ASC (prueba ambos órdenes XY/YX)
mayorias_planetarias(planets_lon)       # conteo por elemento y modalidad
generar_informe_completo(carta)         # HTML completo informe natal
generar_informe_sinastria(c1, c2, orbe) # HTML completo sinastría
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
| POST | `/calcular` | Carta natal: planetas, casas, aspectos, rueda PNG base64, informe Kepler HTML |
| POST | `/transitos` | Tránsitos de una fecha sobre carta natal de referencia |
| POST | `/sinastria` | Sinastría entre dos cartas con textos PAREJA.ASC |
| GET | `/famosos/buscar?q=` | Búsqueda en 8502 cartas históricas (nombre o descripción) |
| POST | `/cartas/guardar` | Guardar carta como JSON en `~/astro_cartas/` |
| GET | `/cartas/listar` | Listar cartas guardadas |
| GET | `/cartas/cargar/<nombre>` | Cargar carta guardada |
| DELETE | `/cartas/borrar/<nombre>` | Borrar carta guardada |

## Regencias clásicas (para sección Regentes)

| Signo | Regente |
|---|---|
| Aries / Escorpio | Marte |
| Tauro / Libra | Venus |
| Géminis / Virgo | Mercurio |
| Cáncer | Luna |
| Leo | Sol |
| Sagitario / Piscis | Júpiter |
| Capricornio / Acuario | Saturno |

## Notas técnicas

- Ejecutar siempre con `py -X utf8` para evitar problemas de encoding en Windows
- Flask `debug=False` — matar el proceso antes de relanzar (no hay recarga automática)
- `importlib.reload(ki)` en cada request para recargar kepler_interp sin reiniciar
- Cartas guardadas en `%USERPROFILE%\astro_cartas\` como JSON
- DB en ruta absoluta: `C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db`
- Matar todos los procesos Python antes de relanzar: `Get-Process python* | Stop-Process -Force`

## Compartir con otros (ngrok)

Para compartir la app sin despliegue, usando túnel desde la máquina local:

```bash
# Instalar una vez
winget install ngrok

# Con la app corriendo en :5000
ngrok http 5000
# → URL pública tipo https://abc123.ngrok.io
```

La URL funciona mientras el PC esté encendido y ngrok activo.

## Famosos en Sinastría

En el tab Sinastría, P1 y P2 tienen cada uno un buscador de famosos
(campo rosa `⭐ Buscar famoso...`) además del selector de cartas guardadas.
Escribe 2+ letras → desplegable con resultados de las 8502 cartas históricas
→ click rellena todos los campos automáticamente. Combinaciones libres:
P1 carta guardada + P2 famoso, ambos famosos, uno manual, etc.

## Exportar PDF

Botón `📄 PDF` en tres tabs:

| Tab | Ubicación |
|---|---|
| 📖 Kepler | Esquina superior derecha del panel |
| 🌍 Tránsitos | Junto al botón Calcular |
| 💞 Sinastría | Junto al botón Calcular |

Abre ventana nueva con informe limpio (sin sidebar ni controles), encabezado
con nombre y fecha, y lanza el diálogo de impresión automáticamente.
Seleccionar "Guardar como PDF" en destino. Sin dependencias externas —
usa el motor PDF del navegador (Chrome / Edge).

## Roadmap

- [ ] Retorno Solar
- [ ] Firdaria / Profecciones anuales
- [ ] Rueda zodiacal con líneas de aspecto dibujadas
- [ ] Tránsitos en rango de fechas (listado de eventos de un periodo)
- [ ] Despliegue en servidor (Render / Railway) con rutas relativas
