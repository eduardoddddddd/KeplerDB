# KeplerDB — Kepler 4 de Miguel García en Python moderno

**Versión:** 1.2  
**Autor:** Eduardo Abdul Malik Arias  
**Descripción:** Migración completa del programa de astrología Kepler 4 (DOS, años 90) de Miguel García a una aplicación web moderna con Flask, SQLite y pyswisseph.

---

## 🚀 Cómo lanzar la aplicación

### Opción 1 — Doble clic (más fácil)
```
Doble clic en: ARRANCAR.bat
```
El navegador se abre solo en `http://localhost:5000`

### Opción 2 — Línea de comandos
```bat
cd C:\Users\Edu\Documents\ClaudeWork\KeplerDB
py -X utf8 app\app.py
```
Luego abre `http://localhost:5000` en el navegador.

### Para cerrar la app
Cierra la ventana de comando que se abrió, o pulsa `Ctrl+C` en ella.

> **No es un HTML estático** — es una app Flask (Python) que necesita estar ejecutándose.
> El navegador solo muestra la interfaz; todos los cálculos se hacen en Python local.

---

## 📋 Requisitos

```
Python 3.12+
pip install flask pyswisseph matplotlib numpy
```

Todos instalados en el sistema. Si falta alguno:
```bat
pip install flask pyswisseph matplotlib numpy
```

---

## 🗂️ Estructura del proyecto

```
KeplerDB/
├── ARRANCAR.bat              ← Doble clic para lanzar
├── app/
│   ├── app.py                ← Servidor Flask (cálculos, rutas API)
│   └── templates/
│       └── index.html        ← Interfaz web
├── kepler.db                 ← Base de datos SQLite con todos los textos
├── kepler_interp.py          ← Motor de interpretaciones (consulta kepler.db)
├── build_kepler_db.py        ← Regenera kepler.db desde los .ASC originales
├── README.md                 ← Este fichero
└── test_db.py                ← Tests de consulta SQL
```

Las cartas guardadas se almacenan en `~/astro_cartas/` (JSON).

---

## 🔧 Funcionalidades

### Carta natal
- Cálculo con pyswisseph (efemérides suizas precisas)
- Sistema de casas: Placidus (default), Koch, Whole Sign, Equal, Campanus, Regiomontanus
- 4 tabs: **Posiciones · Aspectos · Rueda zodiacal · Interpretaciones Kepler**

### Interpretaciones Kepler (tab 📖)
- Textos originales del Kepler 4 de Miguel García
- **Por signo**: texto para cada planeta en su signo zodiacal
- **Por casa**: texto para cada planeta en su casa (cuando signo ≠ casa)
- **Aspectos**: Conjunción / Armónico (trígono+sextil) / Tensión (cuad+opoc)
- 597 bloques interpretativos en español

### Guardar/cargar cartas
- Botón **💾 Guardar Carta** tras calcular
- Panel lateral con lista de cartas guardadas
- Click en nombre → carga y recalcula automáticamente
- **✕** para borrar

---

## 🗃️ Base de datos

```sql
-- Texto para un planeta en su signo
SELECT cabecera, texto FROM interpretaciones
WHERE planeta1='Sol' AND signo='Libra' AND fichero='PLANETAS.ASC';

-- Texto para un planeta en su casa
SELECT cabecera, texto FROM interpretaciones
WHERE planeta1='Luna' AND casa=12 AND fichero='PLANETAS.ASC';

-- Aspecto entre dos planetas
SELECT aspecto, cabecera, texto FROM interpretaciones
WHERE planeta1='Sol' AND planeta2='Saturno' AND fichero='ASPECTOS.ASC';
-- aspecto puede ser: Conjunción / Armónico / Tensión

-- Buscar texto libre
SELECT i.cabecera, i.texto
FROM interpretaciones_fts fts JOIN interpretaciones i ON fts.rowid=i.id
WHERE interpretaciones_fts MATCH 'voluntad energía' ORDER BY rank LIMIT 5;

-- Cartas de famosos
SELECT nombre, lugar, anio, mes, dia, descripcion FROM cartas
WHERE fichero_origen='FAMOSOS.DAT' ORDER BY nombre;
```

---

## 🔄 Regenerar la base de datos

Si tienes acceso al directorio original del Kepler 4:
```bat
py -X utf8 build_kepler_db.py
```
Requiere `C:\Program Files (x86)\Kepler 4\` con los ficheros `.ASC` originales.

---

## 📡 API endpoints (Flask)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/calcular` | Calcula carta natal completa |
| GET | `/cartas/listar` | Lista cartas guardadas |
| POST | `/cartas/guardar` | Guarda carta actual |
| GET | `/cartas/cargar/<nombre>` | Carga carta por nombre |
| DELETE | `/cartas/borrar/<nombre>` | Borra carta |

---

## 📖 Sobre el Kepler 4 original

El **Kepler 4** fue desarrollado por **Miguel García Ferrández** (matemático, Orihuela 1952),
junto a **Tito Maciá** para investigación astrológica. Programa DOS de los años 90, muy valorado
en el mundo hispanohablante por sus gráficos claros y sistema interpretativo.

Los textos interpretativos están en ficheros `.ASC` (CP850) con separadores `#`.
El motor de selección usa un lenguaje propio **RPN** (Reverse Polish Notation) que indexa
los bloques de texto por número de signo (1=Aries...12=Piscis) y casa.

Los aspectos se agrupan en tres categorías:
- **Conjunción** — aspectos de 0°
- **Armónico** — trígono (120°) y sextil (60°)
- **Tensión** — cuadratura (90°) y oposición (180°)
