# -*- coding: utf-8 -*-
"""Job mensual: baja el PDF del mes, parsea y reconstruye el dataset.
   Programar en Task Scheduler ~el 5 de cada mes (SUCIVE actualiza a principio de mes).
   Equivale a: python capture.py && python build_dataset.py"""
import subprocess, sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
for step in ("capture.py", "build_dataset.py"):
    print("==>", step)
    r = subprocess.run([sys.executable, os.path.join(BASE, step)])
    if r.returncode != 0:
        sys.exit(r.returncode)
print("Actualizacion mensual completa.")
