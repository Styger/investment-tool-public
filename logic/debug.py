# debug_import.py - Führen Sie dieses Script aus
import os
import sys

print("=== DEBUG IMPORT PROBLEM ===")
print(f"Aktuelles Arbeitsverzeichnis: {os.getcwd()}")
print(f"Python Pfad: {sys.executable}")
print(f"Python Version: {sys.version}")

# 1. Prüfe ob die Datei existiert
api_file_path = "api/fmp_api.py"
print(f"\n1. Datei-Existenz:")
print(f"   {api_file_path} existiert: {os.path.exists(api_file_path)}")

if os.path.exists(api_file_path):
    # 2. Prüfe Dateiinhalt
    with open(api_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"\n2. Datei-Analyse:")
    print(f"   Dateigröße: {len(content)} Zeichen")
    print(f"   'def get_current_price' gefunden: {'def get_current_price' in content}")

    # Zeige alle Funktionen in der Datei
    lines = content.split("\n")
    functions = [line.strip() for line in lines if line.strip().startswith("def ")]
    print(f"   Gefundene Funktionen: {len(functions)}")
    for func in functions:
        print(f"     - {func}")

# 3. Prüfe __init__.py
init_file = "api/__init__.py"
print(f"\n3. __init__.py Check:")
print(f"   {init_file} existiert: {os.path.exists(init_file)}")

# 4. Versuche Import
print(f"\n4. Import-Test:")
try:
    # Importiere das Modul
    import api.fmp_api as fmp

    print(f"   Import erfolgreich!")
    print(f"   Geladene Datei: {fmp.__file__}")

    # Zeige alle Attribute
    attrs = [attr for attr in dir(fmp) if not attr.startswith("_")]
    print(f"   Verfügbare Funktionen ({len(attrs)}):")
    for attr in attrs:
        print(f"     - {attr}")

    # Spezifischer Test
    has_func = hasattr(fmp, "get_current_price")
    print(f"   get_current_price vorhanden: {has_func}")

    if has_func:
        print(f"   Funktionstyp: {type(getattr(fmp, 'get_current_price'))}")

except Exception as e:
    print(f"   Import FEHLER: {e}")
    import traceback

    traceback.print_exc()

# 5. Versuche direkten Import
print(f"\n5. Direkter Import Test:")
try:
    from api.fmp_api import get_current_price

    print(f"   Direkter Import erfolgreich!")
    print(f"   Funktionstyp: {type(get_current_price)}")
except Exception as e:
    print(f"   Direkter Import FEHLER: {e}")

print("\n=== DEBUG ENDE ===")
