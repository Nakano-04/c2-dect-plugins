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
import hashlib
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
        bad("%s: falta plugin.yml" % d)
        return
    with open(yml, encoding="utf-8") as fh:
        m = yaml.safe_load(fh)
    if not isinstance(m, dict):
        bad("%s: manifiesto no es mapa" % yml)
        return
    for k in ("name", "version", "scope", "mitre", "runtime", "entry"):
        if k not in m:
            bad("%s: falta clave %r" % (yml, k))
    name = os.path.basename(d)
    if m.get("name") != name:
        bad("%s: name %r != carpeta" % (yml, m.get("name")))
    if not isinstance(m.get("version"), str) or not SEMVER.match(m["version"]):
        bad("%s: version semver requerida" % yml)
    if not isinstance(m.get("scope"), str) or not m["scope"].strip():
        bad("%s: scope vacío" % yml)
        return
    scope = m["scope"].strip()
    mitre = m.get("mitre", [])
    if not isinstance(mitre, list) or not mitre or not all(
            isinstance(t, str) and MITRE.match(t) for t in mitre):
        bad("%s: mitre lista de Txxxx" % yml)
    if m.get("runtime") not in ("lua", "wasm"):
        bad("%s: runtime lua|wasm" % yml)
    entry = os.path.join(d, str(m.get("entry", "")))
    if not os.path.isfile(entry):
        bad("%s: entry %r no existe" % (yml, m.get("entry")))
        return
    if os.path.basename(entry) != name + ".lua":
        bad("%s: entry debe ser <name>.lua" % yml)
    with open(entry, encoding="utf-8") as fh:
        head = "".join(fh.readlines()[:5])
    if "-- scope:" not in head:
        bad("%s: sin header -- scope:" % entry)
        return
    if scope not in head:
        bad("%s: scope del manifiesto (%r) no está en el header" % (entry, scope))


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
        data = open(os.path.join(local, fname), "rb").read()
        match = None
        for cdir in candidates:
            cand = os.path.join(cdir, fname)
            if os.path.isfile(cand) and open(cand, "rb").read() == data:
                match = cand
                break
        if match is None:
            bad("dectm/%s: sin gemelo byte-idéntico en c2-dect" % fname)
            continue
        # Compila con el transpilador del repo principal.
        sys.path.insert(0, os.path.join(c2d, "tools", "dls"))
        try:
            import dls
            bundle = dls.compile_dls(os.path.join(local, fname))
            assert bundle["scope"] and bundle["script_id"]
        except Exception as exc:  # noqa: BLE001 — el mensaje es el test
            bad("dectm/%s: no compila: %s" % (fname, exc))
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
        print("validate: %d fallos:" % len(errors))
        for e in errors:
            print("  - %s" % e)
        return 1
    nplug = len([d for d in os.listdir(plugdir)]) if os.path.isdir(plugdir) else 0
    print("validate: ok (%d plugins + dectm simétricos y compilables)" % nplug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
