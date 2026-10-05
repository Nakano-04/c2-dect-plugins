# PLUGIN_SPEC v1 — formato de plugin DECT Lethal Script

Un plugin es una carpeta `plugins/<nombre>/` con:

```
plugins/<nombre>/
  plugin.yml            # manifiesto (obligatorio)
  <nombre>.lua          # fuente (obligatorio; pasa el validador)
```

## plugin.yml

```yaml
name: dect-lethal-script      # == carpeta y fichero .lua
version: 1.0.0               # semver; bump en cada cambio
scope: lab-only              # == header `-- scope:` del .lua
mitre: [T1082, T1057]        # técnicas ATT&CK (lista honesta, sin inflar)
runtime: lua                 # lua | wasm
entry: dect-lethal-script.lua
description: Triage autónomo 5 fases, modos quick/full.
tested_with: c2-dect master  # commit/rama del runtime validado
```

## Reglas (las hace cumplir el marketplace + este spec)

1. **Header obligatorio** (primeras 5 líneas): `-- scope: <etiqueta>` y
   `-- mitre: Txxxx`. Sin header → 400 al publicar.
2. **Sandbox**: prohibido `os.execute, loadfile, dofile, io.popen,
   os.remove, os.rename`; `require()` solo `string/table/math`. Fuente
   ≤ 1 MiB. Ver `docs/SCRIPTING_API.md` en c2-dect para la API `c2.*` real.
3. **Simetría con el repo principal**: el `.lua` aquí debe ser byte-idéntico
   al validado por `cmd/agent_go/scripting_example_test.go` en c2-dect.
   Verificación: `sha256sum plugins/*/*.lua` vs `scripts/lua/*.lua`.
4. **Firmado en campaña**: el marketplace devuelve `sig/kid`; el envelope
   de ejecución añade `sig` (+ `kid/exp/nbf`). Sin firma solo corre en lab.
5. **No destructivo**: ver ETHICS.md §3. El revisor rechaza cualquier
   primitiva fuera de lectura + KV.

## Publicar una versión

1. Edita en c2-dect (`scripts/lua/`), valida con
   `go test -run TestDectLethal ./cmd/agent_go/`.
2. Copia el `.lua` validado aquí + bump `version` en `plugin.yml`.
3. Sube al marketplace de tu lab y ejecuta por `script_id` (multi-round).

## Fuentes `.dectm` (carpeta `dectm/`)

Los manifiestos YAML del DSL (v1, `tools/dls/` en c2-dect) son la fuente de
las plantillas rectilíneas: se transpilan a Lua firmado (`dls.py compile`)
con validación compile-time (allowlist, confirms, topes, firmas). Reglas:

- **Simetría**: cada `.dectm` aquí debe ser byte-idéntico a su gemelo en
  c2-dect (`scripts/lua/*.dectm`, `tools/dls/examples/*.dectm`). El CI lo
  verifica (job `validate`).
- **El Lua emitido NO se versiona**: es artefacto determinista (`dls.py
  compile` → mismo `script_id`); se regenera, no se almacena. Lo que vive
  en `plugins/` es Lua **escrito a mano** (control de flujo que el DSL no
  expresa), validado contra el runtime real.
- Lo que no es expresable en el DSL (ramas sobre datos salvo `when`,
  loops salvo `foreach` desenrollado, capacidades sensibles) queda como
  `.lua` a mano, solo con autorización explícita (ver ETHICS.md).
