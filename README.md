# c2-dect-plugins — DECT Lethal Script plugins

Colección curada de plugins de scripting para
[c2-dect](https://github.com/Nakano-04/c2-dect) (módulo scripting, Fases 2–13).
Cada plugin es un script Lua validado contra el runtime real del agente
(`cmd/agent_go`, ver `scripting_example_test.go` en el repo principal).

> **USO AUTORIZADO ÚNICAMENTE.** Todo plugin aquí es **lab-only** (solo
> lectura + estado KV): no borra, no persiste, no exfiltra, no se propaga.
> Úsalo solo en sistemas propios o con autorización escrita explícita.
> Lee [ETHICS.md](ETHICS.md) antes de usar o contribuir. El acceso no
> autorizado a sistemas informáticos es ilegal.

## Plugins

| Plugin | Qué hace | MITRE |
|--------|----------|-------|
| [`dect-lethal-script`](plugins/dect-lethal-script/) | Triage autónomo 5 fases (beacon → `c2.task` → condicional → `fs.list` → digest + KV multi-round), modos `quick`/`full` | T1082, T1057, T1016, T1033, T1083, T1018 |
| [`dect-lethal-watchdog`](plugins/dect-lethal-watchdog/) | Baseline de procesos en KV + diff ALTAS/BAJAS por ronda | T1057 |

## Fuentes `.dectm` (`dectm/`)

Manifiestos YAML del DSL (Fase 14 en c2-dect) que generan el Lua firmado:
`hello, sysinfo, beacon-jitter, loot-collect, cleanup` (migrados de
`scripts/lua/`) + `sweep` (ejemplo) + `dect-lethal-full` (**port completo
del triage 5 fases en un solo archivo**, con `when`/`scan`/`baseline`).
Byte-idénticos a los del repo principal. Se transpilan con
`tools/dls/dls.py` (`dls.py compile x.dectm`), que valida y firma antes de
desplegar. Ver `PLUGIN_SPEC.md § Fuentes`.

## Uso (operador autorizado, lab con c2-dect corriendo)

```powershell
# 1. Publicar (el marketplace exige header `-- scope: lab-only`, ya incluido)
$src = Get-Content plugins/dect-lethal-script/dect-lethal-script.lua -Raw
$body = @{name="dect-lethal-script.lua"; source=$src} | ConvertTo-Json
Invoke-RestMethod -Uri "https://<c2>:8443/api/scripts/upload" -Method Post `
  -Headers @{Authorization="Bearer $TOK"} -Body $body -ContentType "application/json"
# → {script_id, scope, sig?, kid?}
# 2. Encolar en sesión (añade sig/kid/exp según campaña)
# POST /api/sessions/:id/task {"command":"script","args":"{...}"}
# 3. Re-ejecutar por script_id (multi-round, p. ej. watchdog cada 5 min)
# POST /api/sessions/:id/task {"command":"script","args":"{\"lang\":\"lua\",\"script_id\":\"...\"}"}
```

Ver [PLUGIN_SPEC.md](PLUGIN_SPEC.md) para el formato de plugin (manifiesto,
headers obligatorios, sandbox, firmado) y [ETHICS.md](ETHICS.md) para las
reglas de contribución.
