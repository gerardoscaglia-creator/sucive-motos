# -*- coding: utf-8 -*-
"""Consolida data/*.json -> dataset.json con metricas de analista:
   share, penetracion geografica, indice de fuerza local, concentracion (HHI),
   segmentacion de marcas (economica/media/premium/electrica)."""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DEFAULT_FOCUS = "Soriano"
TRACK = ["YUMBO", "BACCIO", "ZANELLA"]

# Segmentacion del mercado moto uruguayo (estimada por marca)
SEG = {
 "economica": ["YUMBO","BACCIO","ZANELLA","VITAL","KIOTO","LIFAN","LONCIN","GILERA","WINNER",
   "TANGO","BAW","DAYUN","DARKO","DIRTY","ARES","ARSEN","MOTOMEL","GARELLI","FENIX","RAVELAND",
   "XMOTOS","XAPRIL","TITAN","CITY COCO","DANIOU","MASINI","SUMO","ZUType","TRIKE"],
 "media": ["KEEWAY","BAJAJ","TVS","CFMOTO","CFLITE","HERO","BENELLI","VOGE","ZONTES","HAOJUE","BETA"],
 "premium": ["HONDA","YAMAHA","SUZUKI","KAWASAKI","BMW","KTM","DUCATI","HARLEY","HARLEY DAVIDSON",
   "ROYAL ENFIELD","VESPA","TRIUMPH","PIAGGIO","APRILIA","MOTO GUZZI","PEUGEOT"],
 "electrica": ["E-YUMBO","E-ZANELLA","VOLT","SUNRA","SERO","STARK","VELOSOLEX","E-MOTO"],
}
def seg_of(marca):
    m = marca.upper()
    for s, lst in SEG.items():
        if m in lst: return s
    return "otras"

def load():
    out = {}
    for f in glob.glob(os.path.join(DATA, "20*.json")):
        j = json.load(open(f, encoding="utf-8"))
        out[j["periodo"]] = j["data"]
    return dict(sorted(out.items()))

def main():
    periods = load()
    by_period = {}
    all_deptos = set()
    for per, data in periods.items():
        nac = {}
        deptos = {}
        for d, ms in data.items():
            all_deptos.add(d)
            deptos[d] = {"total": sum(ms.values()),
                         "marcas": dict(sorted(ms.items(), key=lambda x: -x[1]))}
            for mk, v in ms.items():
                nac[mk] = nac.get(mk, 0) + v
        total = sum(nac.values())
        ndep = len(deptos)
        # stats por marca: total, share, penetracion (en cuantos deptos), presencia por depto
        brand_stats = {}
        for mk, tot in nac.items():
            present = {d: o["marcas"][mk] for d, o in deptos.items() if mk in o["marcas"]}
            brand_stats[mk] = {"total": tot, "share": round(tot/total*100, 2) if total else 0,
                               "n_deptos": len(present), "penetracion": round(len(present)/ndep*100) if ndep else 0,
                               "seg": seg_of(mk), "presencia": present}
        # concentracion del mercado nacional
        shares = sorted([v/total for v in nac.values()], reverse=True) if total else []
        hhi = round(sum((s*100)**2 for s in shares))  # 0-10000
        top3 = round(sum(shares[:3])*100, 1)
        # split por segmento (nacional)
        seg_tot = {}
        for mk, tot in nac.items():
            seg_tot[seg_of(mk)] = seg_tot.get(seg_of(mk), 0) + tot
        by_period[per] = {
            "total_pais": total,
            "n_marcas": len(nac),
            "hhi": hhi, "top3_share": top3,
            "nac_marcas": dict(sorted(nac.items(), key=lambda x: -x[1])),
            "deptos": dict(sorted(deptos.items(), key=lambda x: -x[1]["total"])),
            "brand_stats": brand_stats,
            "seg_tot": seg_tot,
        }
    plist = list(by_period.keys())
    dataset = {
        "default_focus": DEFAULT_FOCUS, "deptos": sorted(all_deptos),
        "track": TRACK, "segments": SEG,
        "periods": plist, "latest": plist[-1] if plist else None,
        "prev": plist[-2] if len(plist) > 1 else None,
        "by_period": by_period,
        "nota": "Datos oficiales de SUCIVE (empadronamientos del mes). La serie se arma sola, mes a mes. La 'fuerza local' compara cuanto se vende una marca en una zona contra su promedio en el pais (1.3x = se vende mas ahi; 0.7x = menos). Segmentacion de marcas estimada.",
    }
    json.dump(dataset, open(os.path.join(BASE, "dataset.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    L = by_period[plist[-1]]
    print(f"dataset.json OK | {len(plist)} periodos | {len(all_deptos)} deptos | {L['n_marcas']} marcas | HHI={L['hhi']} top3={L['top3_share']}%")

if __name__ == "__main__":
    main()
