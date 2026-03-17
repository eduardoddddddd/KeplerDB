import json, shutil

NB = r'C:\Users\Edu\Downloads\astro_dashboard_v2.ipynb'
with open(NB, encoding='utf-8') as f:
    nb = json.load(f)

NUEVA_CELDA = r"""
# ═══════════════════════════════════════════════════════════════════
# TAB KEPLER — Interpretaciones automáticas desde kepler.db
# ═══════════════════════════════════════════════════════════════════
import sys
sys.path.insert(0, r'C:\Users\Edu\Documents\ClaudeWork\KeplerDB')
import importlib, kepler_interp as ki
importlib.reload(ki)   # recarga si hay cambios en el módulo

def _build_kepler():
    out_e = widgets.Output()
    out_k = widgets.Output(layout=widgets.Layout(min_height='600px'))
    lbl   = widgets.HTML(value=(
        '<i style="color:#667788">Calcula primero una carta en el tab '
        '⭐ Natal o 💾 Cartas, luego pulsa el botón.</i>'))

    btn_gen   = widgets.Button(description='📖  Generar Informe Kepler',
                               button_style='primary',
                               layout=widgets.Layout(width='250px',height='38px'))
    btn_clear = widgets.Button(description='🗑  Limpiar',
                               layout=widgets.Layout(width='110px',height='38px'))
    w_buscar  = widgets.Text(
        placeholder='Buscar en textos Kepler (ej: voluntad energía)...',
        layout=widgets.Layout(width='420px'))
    btn_buscar = widgets.Button(description='🔍 Buscar',
                                button_style='info',
                                layout=widgets.Layout(width='100px',height='34px'))

    def _generar(b=None):
        out_e.clear_output(); out_k.clear_output(wait=True)
        if not _carta_activa:
            with out_e: print('Sin carta activa — calcula primero en tab Natal o Cartas.')
            return
        with out_k:
            try:
                importlib.reload(ki)
                html = ki.generar_informe_completo(_carta_activa)
                display(HTML(html))
            except Exception:
                import traceback; traceback.print_exc()

    def _limpiar(b=None):
        out_k.clear_output(); out_e.clear_output()

    def _buscar(b=None):
        q = w_buscar.value.strip()
        if not q: return
        out_k.clear_output(wait=True); out_e.clear_output()
        try:
            rows = ki.busqueda_libre(q, limite=12)
            with out_k:
                if not rows:
                    display(HTML(f'<div style="color:#888;padding:10px">Sin resultados para: <b>{q}</b></div>'))
                    return
                html = (f'<div style="background:#1a1a2a;color:#e0e0f0;padding:10px;'
                        f'border-radius:6px;margin-bottom:8px"><b>Resultados:</b> {q}</div>')
                for fic, cab, texto in rows:
                    html += (f'<div style="background:#1a2a1a;border-left:3px solid #446;'
                             f'padding:8px 12px;margin:3px 0;border-radius:0 6px 6px 0">'
                             f'<div style="font-size:11px;color:#778;margin-bottom:2px">'
                             f'{fic} · {cab}</div>'
                             f'<div style="font-size:13px;color:#cdc;line-height:1.5">{texto}</div></div>')
                display(HTML(html))
        except Exception:
            import traceback
            with out_e: traceback.print_exc()

    btn_gen.on_click(_generar)
    btn_clear.on_click(_limpiar)
    btn_buscar.on_click(_buscar)

    return widgets.VBox([
        widgets.HTML('<div style="padding:6px 0 4px">'
                     '<b style="font-size:15px">📖 Interpretaciones Kepler 4</b>'
                     '<span style="font-size:12px;color:#889"> — 743 textos de Miguel García · kepler.db</span>'
                     '</div>'),
        lbl,
        widgets.HBox([btn_gen, btn_clear]),
        widgets.HTML('<hr style="border-color:#334;margin:8px 0">'),
        widgets.HTML('<b style="font-size:12px;color:#889">Búsqueda libre:</b>'),
        widgets.HBox([w_buscar, btn_buscar]),
        out_e, out_k,
    ])

tab_kepler = _build_kepler()
_children  = list(TABS.children) + [tab_kepler]
TABS.children = tuple(_children)
TABS.set_title(len(_children)-1, '📖 Kepler')
print('✅ Tab Kepler listo.')
"""

# Eliminar celda Kepler anterior si existe (celda 3)
if len(nb['cells']) > 3:
    nb['cells'] = nb['cells'][:3]

nb['cells'].append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [NUEVA_CELDA]
})

with open(NB, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f'Notebook actualizado. Celdas: {len(nb["cells"])}')
