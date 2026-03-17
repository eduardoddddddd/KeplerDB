# KeplerDB — Base de datos del Kepler 4 de Miguel García

**Generado:** 2026-03-17  
**Fuente:** `C:\Program Files (x86)\Kepler 4\`  
**Base de datos:** `kepler.db` (SQLite 3, 2.4 MB)  
**Encoding original:** CP850 (DOS español) → UTF-8 en la DB

---

## Resumen de contenido

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `interpretaciones` | **743** | Textos interpretativos de todos los .ASC |
| `cartas` | **8.502** | Cartas natales de los .DAT originales |
| `rpn_scripts` | **22** | Scripts .RPN del motor de Kepler |
| `interpretaciones_fts` | (virtual) | Índice full-text sobre interpretaciones |

---

## Tabla: `interpretaciones`

La tabla principal. Todos los textos interpretativos del Kepler normalizados y con metadatos inferidos.

### Columnas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER | Clave primaria |
| `fichero` | TEXT | Fichero .ASC origen |
| `indice` | INTEGER | Índice 1-based dentro del fichero |
| `cabecera` | TEXT | Título del bloque (ej: "SOL EN ARIES O CASA 1") |
| `texto` | TEXT | Texto interpretativo completo |
| `planeta1` | TEXT | Planeta principal (Sol, Luna, Marte...) |
| `planeta2` | TEXT | Planeta secundario (para aspectos) |
| `signo` | TEXT | Signo zodiacal (Aries, Tauro...) |
| `casa` | INTEGER | Casa astrológica (1-12) |
| `aspecto` | TEXT | Tipo de aspecto (Conjunción, Trígono...) |
| `codigo_pareja` | TEXT | Código sinastría (ej: EAB, EAM) solo en PAREJA.ASC |
| `valencia` | TEXT | Beneficioso / Tenso (solo PAREJA.ASC) |
| `palabras_clave` | TEXT | Primeras palabras del texto |

### Distribución por fichero

| Fichero | Bloques | Contenido |
|---------|---------|-----------|
| `PAREJA.ASC` | 173 | Sinastría — sistema de códigos ==EAB/EAM etc. |
| `CASAS.ASC` | 145 | Planetas en casas (extendido) |
| `REGENTES.ASC` | 144 | Regentes de casas |
| `ASPECTOS.ASC` | 136 | Aspectos entre planetas |
| `PLANETAS.ASC` | 120 | Planetas en signo/casa (principal) |
| `ASCEN.ASC` | 12 | Ascendente en signo |
| `SOL.ASC` | 12 | Sol — textos complementarios |
| `FIGURASD.ASC` | 1 | Doc. congreso figuras geométricas (texto libre) |

---

## Tabla: `cartas`

Base de datos de cartas natales del Kepler original.

### Columnas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | INTEGER | Clave primaria |
| `fichero_origen` | TEXT | Fichero .DAT de origen |
| `nombre` | TEXT | Nombre del nativo |
| `lugar` | TEXT | Lugar de nacimiento |
| `anio/mes/dia` | INTEGER | Fecha de nacimiento |
| `hora/min` | INTEGER | Hora de nacimiento |
| `gmt` | REAL | Diferencia horaria GMT (ej: -1.0 = España invierno) |
| `lat` | REAL | Latitud (positivo = Norte) |
| `lon` | REAL | Longitud (positivo = Este) |
| `tags` | TEXT | Etiquetas originales separadas por coma |
| `descripcion` | TEXT | Profesión/descripción libre |

### Ficheros de cartas disponibles

| Fichero | Cartas | Temática |
|---------|--------|----------|
| `ESTUDI.DAT` | 1.309 | Estudio general |
| `CESQUIZO.DAT` | 1.308 | Esquizofrenia (investigación) |
| `MEDFRA.DAT` | 1.082 | Médicos franceses |
| `CURFRA.DAT` | 883 | Curadores/sanadores franceses |
| `MEDESP.DAT` | 764 | Médicos españoles |
| `CARTAS1.DAT` | 465 | Cartas generales |
| `MU.DAT` | 488 | Muertos/fallecidos |
| `CMURDE.DAT` / `MURDE.DAT` | 589 | Homicidas/crímenes |
| `CART.DAT` | 340 | Cartas generales |
| `ESTUDIO3.DAT` | 260 | Estudio 3 |
| `FAMOSOS.DAT` | 362 | Personajes famosos |
| `MUNDIAL.DAT` | 21 | Eventos mundiales |
| `CONCILIO.DAT` | 19 | Concilios religiosos |
| `POLITIC.DAT` | 9 | Políticos |
| `HORARIAS.DAT` | 5 | Cartas horarias |
| `ELCCION.DAT` | 4 | Elecciones |
| `RIPS.DAT` | 4 | Fallecidos destacados |
| `MGF.DAT` | 1 | Carta del autor (Miguel García) |

---

## Tabla: `rpn_scripts`

Scripts .RPN del motor de interpretación de Kepler (texto legible).

### Ficheros RPN guardados

El motor RPN usa un lenguaje stack-based (postfix). Elementos clave:
- `sol signo !!` → calcula signo del Sol y lo empuja al stack
- `\SELECT fichero.asc -N` → muestra bloque N del .ASC
- `@S1` → sustituye por valor en posición 1 del stack (ej: "ARIES")
- `$comentario` → comentario

| Fichero | Descripción |
|---------|-------------|
| `PLANETAS.RPN` | Motor planetas en signo/casa |
| `CASAS.RPN` | Motor de casas |
| `ASPECTOS.RPN` | Motor de aspectos |
| `R_SOLAR.RPN` | Revolución Solar |
| `T_INDIVI.RPN` | Tránsitos individuales |
| `T_PAREJA.RPN` | Tránsitos de pareja |
| `S_PAREJA.RPN` | Sinastría |
| `RADICAL.RPN` | Carta radical |
| `ESTRUC1/2/3.RPN` | Estructuras Celestes (figuras geométricas) |
| `ARMOGRAM.RPN` | Armogramas |
| `ARMOPLNT/LUNA/SOL.RPN` | Armónicos varios |
| `SENDEROS.RPN` | Senderos de vida |
| `SEFIRAS.RPN` | Séfiras cabalísticas |
| `JONES.RPN` | Figuras de Jones |
| `BLOQUEOS.RPN` | Bloqueos psicológicos |

---

## Consultas SQL de ejemplo

### Buscar texto para una posición natal concreta
```sql
-- Sol en Libra
SELECT cabecera, texto
FROM interpretaciones
WHERE planeta1 = 'Sol' AND signo = 'Libra';

-- Luna en Casa 12
SELECT cabecera, texto
FROM interpretaciones
WHERE planeta1 = 'Luna' AND casa = 12;

-- Saturno en Leo (cualquier casa o signo)
SELECT cabecera, texto
FROM interpretaciones
WHERE planeta1 = 'Saturno' AND signo = 'Leo';
```

### Buscar aspectos
```sql
-- Todos los aspectos de Marte
SELECT cabecera, texto
FROM interpretaciones
WHERE (planeta1 = 'Marte' OR planeta2 = 'Marte')
  AND aspecto IS NOT NULL;

-- Conjunciones Sol-Luna
SELECT cabecera, texto
FROM interpretaciones
WHERE planeta1 = 'Sol' AND planeta2 = 'Luna' AND aspecto = 'Conjunción';
```

### Sinastría (PAREJA.ASC)
```sql
-- Todos los textos de sinastría beneficiosos
SELECT codigo_pareja, cabecera, texto
FROM interpretaciones
WHERE fichero = 'PAREJA.ASC' AND valencia = 'Beneficioso'
ORDER BY codigo_pareja;

-- Textos tensos de pareja
SELECT codigo_pareja, texto
FROM interpretaciones
WHERE fichero = 'PAREJA.ASC' AND valencia = 'Tenso';
```

### Búsqueda de texto libre (FTS5)
```sql
-- Buscar por palabras en los textos
SELECT i.cabecera, i.texto
FROM interpretaciones_fts fts
JOIN interpretaciones i ON fts.rowid = i.id
WHERE interpretaciones_fts MATCH 'intuición artística'
ORDER BY rank;

-- Buscar en un fichero específico
SELECT i.cabecera, i.texto
FROM interpretaciones_fts fts
JOIN interpretaciones i ON fts.rowid = i.id
WHERE interpretaciones_fts MATCH 'voluntad energía'
  AND i.fichero = 'PLANETAS.ASC'
ORDER BY rank;
```

### Cartas natales
```sql
-- Buscar famoso por nombre
SELECT nombre, lugar, anio, mes, dia, hora, min, lat, lon, descripcion
FROM cartas WHERE nombre LIKE '%Einstein%';

-- Nacidos en una fecha concreta
SELECT nombre, lugar, descripcion
FROM cartas WHERE anio = 1940 AND mes = 10 AND dia = 9;

-- Todos los astrólogos en la DB
SELECT nombre, lugar, anio, descripcion
FROM cartas WHERE descripcion LIKE '%stról%';
```

### Leer un script RPN
```sql
SELECT contenido FROM rpn_scripts WHERE fichero = 'PLANETAS.RPN';
```

---

## Cómo usar desde Python

```python
import sqlite3

conn = sqlite3.connect(r'C:\Users\Edu\Documents\ClaudeWork\KeplerDB\kepler.db')
cur = conn.cursor()

# Obtener texto para Sol en Libra
cur.execute("SELECT texto FROM interpretaciones WHERE planeta1='Sol' AND signo='Libra' LIMIT 1")
print(cur.fetchone()[0])

# Búsqueda libre
cur.execute("""
    SELECT i.cabecera, i.texto
    FROM interpretaciones_fts fts
    JOIN interpretaciones i ON fts.rowid = i.id
    WHERE interpretaciones_fts MATCH ?
    ORDER BY rank LIMIT 5
""", ('voluntad liderazgo',))
for row in cur.fetchall():
    print(row[0], '-', row[1][:80])

conn.close()
```

---

## Notas técnicas

- **Encoding:** CP850 (DOS español) convertido a UTF-8 en la DB
- **Separador bloques .ASC estándar:** línea con solo `#`
- **Separador PAREJA.ASC:** `==COD` al inicio de línea (COD = código 3 letras)
- **Separador campos .DAT:** `\LETRA>valor` (texto plano, no binario)
- **FTS5:** Full-text search sobre cabecera + texto + planeta + signo + aspecto
- **Índices:** planeta1, planeta2, signo, casa, aspecto, fichero, nombre (cartas)
- **Efemérides originales:** ficheros .EFE (JUP2002D, MAR2002D, VEN2002D, SAT2002D)
  — no importados, el cálculo de posiciones debe hacerse con pyswisseph

---

## Ficheros generados

| Fichero | Descripción |
|---------|-------------|
| `kepler.db` | Base de datos SQLite principal |
| `build_kepler_db.py` | Script de construcción (re-ejecutable) |
| `test_db.py` | Tests y consultas de ejemplo |
| `README.md` | Esta documentación |
