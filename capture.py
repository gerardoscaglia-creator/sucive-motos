# -*- coding: utf-8 -*-
"""
SUCIVE Motos - Captura y parseo mensual de empadronamientos Cat. C (motos).
Descarga los PDF estables de SUCIVE, parsea marca x departamento, y acumula
en SQLite + snapshot JSON por mes. Pensado para correr 1 vez por mes (Task Scheduler).

Uso:  python capture.py
"""
import os, re, sqlite3, json, urllib.request, ssl, sys

BASE = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE, "pdfs")
DATA_DIR = os.path.join(BASE, "data")
DB = os.path.join(BASE, "sucive.db")

# Reportes SUCIVE (URLs estables, no de sesion)
REPORTS = {
    "catC_marca_depto": "https://sucive.gub.uy/?-1.-empCatCPorMarcaYDepto",  # motos por marca y depto
}

DEPTOS = {"Artigas","Canelones","Cerro Largo","Colonia","Durazno","Flores","Florida",
    "Lavalleja","Maldonado","Montevideo","Paysandu","Paysandú","Rio Negro","Río Negro",
    "Rivera","Rocha","Salto","San Jose","San José","Soriano","Tacuarembo","Tacuarembó",
    "Treinta y Tres"}

def norm_depto(d):
    return (d.replace("Paysandu","Paysandú").replace("Rio Negro","Río Negro")
             .replace("San Jose","San José").replace("Tacuarembo","Tacuarembó"))

def download(url, dest):
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r, open(dest,"wb") as f:
        f.write(r.read())

def parse_pdf(path):
    import pypdf
    r = pypdf.PdfReader(path)
    full = "\n".join(p.extract_text() for p in r.pages)
    lines = [l.strip() for l in full.split("\n") if l.strip()]
    # periodo: "01/05/2026" ... "31/05/2026" -> usamos mes/anio del inicio
    # El periodo SIEMPRE arranca el dia 01 (ej "01/05/2026"); la "Fecha de
    # actualizacion" no, asi evitamos confundirla con el periodo real.
    periodo = None
    m = re.search(r"\b01/(\d{2})/(\d{4})", full)
    if m:
        periodo = f"{m.group(2)}-{m.group(1)}"
    data = {}; subtotals = {}; cur = None
    for l in lines:
        # OJO: un departamento puede ocupar varias paginas y el encabezado se
        # repite. Usamos setdefault (no reset) para NO perder las marcas de la
        # primera pagina al reaparecer el header.
        if l in DEPTOS: cur = norm_depto(l); data.setdefault(cur, {}); continue
        st = re.match(r"subtotal\s*(\d+)\s+(\d+)", l, re.I)
        if st:
            # el PDF imprime el subtotal oficial de cada depto: lo guardamos
            # como control de integridad del parseo.
            if cur: subtotals[cur] = int(st.group(1))
            cur = None; continue
        # \s* permite nombres largos pegados al numero (ej "HARLEY DAVIDSON1 1")
        m = re.match(r"^(.+?)\s*(\d+)\s+(\d+)$", l)
        if cur and m:
            marca = m.group(1).strip()
            data[cur][marca] = data[cur].get(marca, 0) + int(m.group(2))
    return periodo, data, subtotals

def validate(periodo, data, subtotals):
    """Devuelve lista de errores. Si NO esta vacia, el PDF parseo mal y NO se
    debe escribir/commitear (protege contra corrupcion silenciosa si SUCIVE
    cambia el formato del PDF)."""
    errs = []
    if not periodo:
        errs.append("no se detecto el periodo (formato de fecha cambiado?)")
    if len(data) < 19:
        errs.append(f"solo {len(data)} departamentos parseados (esperado 19)")
    total = sum(sum(m.values()) for m in data.values())
    if total < 1500:
        errs.append(f"total pais implausible: {total} (esperado >1500)")
    for b in ("BACCIO", "YUMBO", "ZANELLA"):
        if not any(b in m for m in data.values()):
            errs.append(f"marca conocida ausente en todo el pais: {b}")
    # CONTROL FUERTE: la suma por depto debe coincidir con el subtotal que el
    # propio PDF de SUCIVE imprime. Si no coincide, el parseo esta roto.
    for dep, st in subtotals.items():
        calc = sum(data.get(dep, {}).values())
        if calc != st:
            errs.append(f"subtotal {dep}: PDF dice {st}, parseamos {calc}")
    if len(subtotals) < 19:
        errs.append(f"solo {len(subtotals)} subtotales detectados (esperado 19)")
    return errs

def init_db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS emp(
        periodo TEXT, depto TEXT, marca TEXT, cantidad INTEGER,
        PRIMARY KEY(periodo,depto,marca))""")
    c.commit(); return c

def main():
    os.makedirs(PDF_DIR, exist_ok=True); os.makedirs(DATA_DIR, exist_ok=True)
    pdf = os.path.join(PDF_DIR, "catC_marca_depto_latest.pdf")
    download(REPORTS["catC_marca_depto"], pdf)
    periodo, data, subtotals = parse_pdf(pdf)
    # VALIDACION: si el PDF no parsea bien, abortamos SIN escribir nada para no
    # pisar los datos buenos del mes anterior con basura.
    errs = validate(periodo, data, subtotals)
    if errs:
        print("ABORTADO: el PDF de SUCIVE no paso la validacion:")
        for e in errs:
            print("  -", e)
        print("No se escribio ni commiteo nada. Revisar si SUCIVE cambio el formato.")
        sys.exit(1)
    # snapshot json del mes
    snap = os.path.join(DATA_DIR, f"{periodo}.json")
    with open(snap, "w", encoding="utf-8") as f:
        json.dump({"periodo": periodo, "data": data}, f, ensure_ascii=False, indent=2)
    # archivar el pdf del mes
    import shutil; shutil.copy(pdf, os.path.join(PDF_DIR, f"catC_{periodo}.pdf"))
    # upsert en db
    c = init_db()
    n = 0
    for depto, marcas in data.items():
        for marca, cant in marcas.items():
            c.execute("INSERT OR REPLACE INTO emp VALUES(?,?,?,?)",(periodo,depto,marca,cant)); n+=1
    c.commit()
    total = sum(sum(m.values()) for m in data.values())
    sor = sum(data.get("Soriano",{}).values())
    print(f"OK periodo={periodo} deptos={len(data)} filas={n} total_pais={total} soriano={sor}")
    c.close()

if __name__ == "__main__":
    main()
