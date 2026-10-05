-- scope: lab-only
-- mitre: T1057
-- DECT Lethal Script: watchdog de procesos (automatización concisa).
-- Ronda 1: guarda baseline en KV. Rondas siguientes (mismo script_id):
-- reporta ALTAS/BAJAS y actualiza el baseline. Re-ejecutar periódicamente
-- desde el operador o scheduler para vigilancia continua.
-- Solo lectura + KV: no toca el sistema.

local function say(level, msg)
  c2.log(level, "[DECT-Lethal:watchdog] " .. msg)
end

local function toset(blob)
  -- Clave = solo nombre del ejecutable (la salida real es CSV tipo tasklist:
  -- "nombre","pid",... y PID/memoria fluctúan entre rondas).
  local t = {}
  for line in string.gmatch(blob .. "\n", "([^\n]*)\n") do
    local name = string.lower(
      string.match(line, '^%s*"([^"]+)"') or string.match(line, "%S+") or "")
    if name ~= "" then t[name] = true end
  end
  return t
end

local function keys(t)
  local names = {}
  for name in pairs(t) do names[#names + 1] = name end
  table.sort(names)
  return names
end

local out, err = c2.task("ps")
if out == nil then
  say("error", "ps no disponible: " .. tostring(err))
  return
end
local cur = toset(out)

local prev_raw = c2.kv.get("dect-lethal:watchdog:ps")
if prev_raw == nil then
  c2.kv.set("dect-lethal:watchdog:ps", table.concat(keys(cur), "\n"))
  say("info", "baseline guardado")
  return
end

local base = toset(prev_raw)
local altas, bajas = {}, {}
for name in pairs(cur) do
  if not base[name] then altas[#altas + 1] = name end
end
for name in pairs(base) do
  if not cur[name] then bajas[#bajas + 1] = name end
end

if #altas == 0 and #bajas == 0 then
  say("info", "sin cambios")
else
  table.sort(altas)
  table.sort(bajas)
  if #altas > 0 then say("warn", "ALTAS: " .. table.concat(altas, ",")) end
  if #bajas > 0 then say("warn", "BAJAS: " .. table.concat(bajas, ",") ) end
  c2.kv.set("dect-lethal:watchdog:ps", table.concat(keys(cur), "\n"))
  say("info", "baseline actualizado")
end
