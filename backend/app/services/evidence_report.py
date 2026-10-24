"""Printable, escaped evidence reports; no executable user content."""
from html import escape


def render_value(value):
    if isinstance(value, dict):
        return ''.join(f'<section><h3>{escape(str(k).replace("_"," "))}</h3>{render_value(v)}</section>' for k,v in value.items())
    if isinstance(value, list):
        if not value: return '<p class="muted">No observations</p>'
        if all(isinstance(r,dict) for r in value):
            columns=list(dict.fromkeys(k for r in value for k in r))
            head=''.join(f'<th>{escape(str(k).replace("_"," "))}</th>' for k in columns)
            rows=''.join('<tr>'+''.join(f'<td>{render_value(r.get(k))}</td>' for k in columns)+'</tr>' for r in value)
            return f'<div class="table"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
        return '<ul>'+''.join(f'<li>{render_value(v)}</li>' for v in value)+'</ul>'
    return '<span>'+escape('Not available' if value is None else str(value))+'</span>'


def evidence_document(row, stale):
    status='Historical result: the active dataset has changed.' if stale else 'Dataset revision matched at export.' if row.dataset_revision else 'Not tied to a dataset revision.'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(row.title)}</title>
    <style>body{{font:15px/1.55 system-ui;max-width:1080px;margin:40px auto;padding:24px;color:#27221e}}header{{border-bottom:3px solid #795338;margin-bottom:28px}}h1{{font-size:30px}}h3{{font-size:14px;text-transform:capitalize;margin-bottom:8px}}section{{margin:16px 0}}.muted,footer{{color:#666;font-size:12px}}.table{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:9px;border:1px solid #ddd;text-align:left;vertical-align:top}}th{{background:#f5f1eb}}td section{{margin:4px}}td h3{{font-size:12px}}span{{white-space:pre-wrap;overflow-wrap:anywhere}}@media print{{body{{margin:0;padding:8px}}thead{{display:table-header-group}}tr{{break-inside:avoid}}.table{{overflow:visible}}}}</style></head><body>
    <header><p class="muted">DATALYZE · Evidence report #{row.id}</p><h1>{escape(row.title)}</h1><p class="muted">Saved {row.created_at.isoformat()} · Author #{row.user_id}</p><p>{status}</p><p class="muted">Source revision: {escape(row.dataset_revision or 'None')}</p></header>
    {render_value(row.content)}<footer><hr>Computed results retain their method, parameters and source revision. User-authored findings and actions require business review. Correlation and contribution analysis do not establish causation.</footer></body></html>'''
