#!/usr/bin/env python3
"""validate.py — CI del catálogo c2-dect-plugins (Fase 14, punto 5).

Verifica, sin ejecutar nada contra red ni agentes:
1. Schema de cada `plugins/*/plugin.yml` (claves, semver, scope, MITRE,
   entry existente, nombre == carpeta == basename del entry).
2. Scope declarado: el `.lua` del plugin trae `-- scope: <etiqueta>` y
   coincide con el `scope` del manifiesto.
3. Simetría `.dectm`: cada fichero en `dectm/` es byte-idéntico a su gemelo
   en c2-dect (`scripts/lua/`, `tools/dls/examples/`).
4. Compilación: cada `.dectm` pasa `dls.py check` del c2-dect clonado.

Uso:
    python3 validate.py --c2-dect ../c2-dect
Requiere PyYAML (pip install pyyaml). Sale 0 si todo ok, 1 con la lista.
"""

import argparse
import os
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

ROOT = os.path.dirname(os.path.abspath(__file__))
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
MITRE = re.compile(r"^T\d{4}(\.\d{3})?$")
PLUGIN_KEYS = {"name", "version", "scope", "mitre", "runtime", "entry",
               "description", "tested_with"}

errors = []


def bad(msg):
    errors.append(msg)


def check_plugin(d, c2d):
    yml = os.path.join(d, "plugin.yml")
    if not os.path.isfile(yml):
        bad(f"{d}: falta plugin.yml")
        return
    with open(yml, encoding="utf-8") as fh:
        m = yaml.safe_load(fh)
    if not isinstance(m, dict):
        bad(f"{yml}: manifiesto no es mapa")
        return
    for k in ("name", "version", "scope", "mitre", "runtime", "entry"):
        if k not in m:
            bad(f"{yml}: falta clave {k!r}")
    name = os.path.basename(d)
    if m.get("name") != name:
        bad("{}: name {!r} != carpeta".format(yml, m.get("name")))
    if not isinstance(m.get("version"), str) or not SEMVER.match(m["version"]):
        bad(f"{yml}: version semver requerida")
    if not isinstance(m.get("scope"), str) or not m["scope"].strip():
        bad(f"{yml}: scope vacío")
        return
    scope = m["scope"].strip()
    mitre = m.get("mitre", [])
    if not isinstance(mitre, list) or not mitre or not all(
            isinstance(t, str) and MITRE.match(t) for t in mitre):
        bad(f"{yml}: mitre lista de Txxxx")
    if m.get("runtime") not in ("lua", "wasm"):
        bad(f"{yml}: runtime lua|wasm")
    entry = os.path.join(d, str(m.get("entry", "")))
    if not os.path.isfile(entry):
        bad("{}: entry {!r} no existe".format(yml, m.get("entry")))
        return
    if os.path.basename(entry) != name + ".lua":
        bad(f"{yml}: entry debe ser <name>.lua")
    with open(entry, encoding="utf-8") as fh:
        head = "".join(fh.readlines()[:5])
    if "-- scope:" not in head:
        bad(f"{entry}: sin header -- scope:")
        return
    if scope not in head:
        bad(f"{entry}: scope del manifiesto ({scope!r}) no está en el header")


def check_dectm_symmetry(c2d):
    local = os.path.join(ROOT, "dectm")
    if not os.path.isdir(local):
        bad("falta carpeta dectm/")
        return
    candidates = [
        os.path.join(c2d, "scripts", "lua"),
        os.path.join(c2d, "tools", "dls", "examples"),
    ]
    for fname in sorted(os.listdir(local)):
        if not fname.endswith(".dectm"):
            continue
        with open(os.path.join(local, fname), "rb") as fh:
            data = fh.read()
        match = False
        for cdir in candidates:
            cand = os.path.join(cdir, fname)
            if not os.path.isfile(cand):
                continue
            with open(cand, "rb") as fh:
                if fh.read() == data:
                    match = True
                    break
        if not match:
            bad(f"dectm/{fname}: sin gemelo byte-idéntico en c2-dect")
            continue
        # Compila con el transpilador del repo principal.
        sys.path.insert(0, os.path.join(c2d, "tools", "dls"))
        try:
            import dls
            bundle = dls.compile_dls(os.path.join(local, fname))
            assert bundle["scope"] and bundle["script_id"]
        except Exception as exc:
            bad(f"dectm/{fname}: no compila: {exc}")
        finally:
            sys.path.remove(os.path.join(c2d, "tools", "dls"))
            sys.modules.pop("dls", None)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--c2-dect", required=True)
    args = ap.parse_args(argv)
    if yaml is None:
        print("falta PyYAML (pip install pyyaml)", file=sys.stderr)
        return 1
    c2d = args.c2_dect
    if not os.path.isdir(os.path.join(c2d, "tools", "dls")):
        print("--c2-dect debe apuntar al repo c2-dect", file=sys.stderr)
        return 1
    plugdir = os.path.join(ROOT, "plugins")
    if not os.path.isdir(plugdir):
        bad("falta carpeta plugins/")
    else:
        for name in sorted(os.listdir(plugdir)):
            p = os.path.join(plugdir, name)
            if os.path.isdir(p):
                check_plugin(p, c2d)
    check_dectm_symmetry(c2d)
    if errors:
        print(f"validate: {len(errors)} fallos:")
        for e in errors:
            print(f"  - {e}")
        return 1
    nplug = len([d for d in os.listdir(plugdir)]) if os.path.isdir(plugdir) else 0
    print(f"validate: ok ({nplug} plugins + dectm simétricos y compilables)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
