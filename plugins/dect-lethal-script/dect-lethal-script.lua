-- scope: lab-only
-- mitre: T1082, T1057, T1016, T1033, T1083, T1018
-- DECT Lethal Script: triage autonomo multi-fase para Red Team AUTORIZADO.
-- Solo lectura + KV: no borra, no mueve, no persiste, no exfiltra.
-- Requiere runtime Fase 2+ (c2.task/log/beacon/exec/crypto/fs/kv).
--
-- Uso (envelope):
--   {"lang":"lua","source":"<este fichero>","args":"{\"mode\":\"quick\"}"}
-- Multi-round: guarda cursor en c2.kv ("dect-lethal:round",
-- "dect-lethal:digest") para continuar con
-- {"lang":"lua","script_id":"<sha256>","args":"..."}.
-- Firmado (Fase 8+): anadir "sig" (+ "kid"/"exp"/"nbf" segun campana).

local function say(level, msg)
  c2.log(level, "[DECT-Lethal] " .. msg)
end

-- Args opcionales: {"mode":"quick"|"full"} (defecto full).
local mode = "full"
local a = c2.args()
if a ~= nil then
  local m = string.match(a, '"mode"%s*:%s*"(%w+)"')
  if m == "quick" or m == "full" then mode = m end
end

-- Contexto del beacon (tenant visible desde Fase 11).
local b = c2.beacon()
say("info", string.format("inicio mode=%s host=%s os=%s/%s tenant=%s sid=%s",
  mode, b.hostname, b.os, b.arch, tostring(b.tenant_id), b.session_id))

-- Fase 1: enumeracion del sistema (allowlist read-only de c2.task).
local checks = {"sysinfo", "ps", "netinfo", "env", "connections", "services"}
local findings = {}
for _, cmd in ipairs(checks) do
  local out, err = c2.task(cmd)
  if out == nil then
    say("warn", cmd .. " no disponible: " .. tostring(err))
  else
    say("info", cmd .. " bytes=" .. tostring(#out))
    findings[cmd] = out
  end
  if mode == "quick" and cmd == "netinfo" then break end
end

-- Fase 2: triage condicional (patrones sobre ps + red).
local hits = {}
if findings["ps"] then
  local low = string.lower(findings["ps"])
  for _, pat in ipairs({"mimikatz", "psexec", "nmap", "bloodhound", "rubeus", "lazagne"}) do
    if string.find(low, pat, 1, true) then hits[#hits + 1] = pat end
  end
end
local interesting_ports = {}
if findings["connections"] then
  for _, p in ipairs({":445", ":3389", ":5985", ":22", ":3306", ":1433"}) do
    if string.find(findings["connections"], p, 1, true) then
      interesting_ports[#interesting_ports + 1] = p
    end
  end
end
say(#hits > 0 and "warn" or "info",
  "iocs=" .. (#hits > 0 and table.concat(hits, ",") or "ninguno"))
say(#interesting_ports > 0 and "warn" or "info",
  "puertos=" .. (#interesting_ports > 0 and table.concat(interesting_ports, ",") or "ninguno"))

-- Fase 3: fs acotado (lista del home; read solo si quick no lo pide todo).
local listing, lerr = c2.fs.list("")
if listing == nil then
  say("warn", "fs.list: " .. tostring(lerr))
else
  local n = 0
  for _ in string.gmatch(listing, "\n") do n = n + 1 end
  say("info", "home_entries~" .. tostring(n))
end

-- Fase 4: identidad del que ejecuta (shell auditable, con fallback).
local who, werr = c2.exec("whoami")
if who == nil then
  say("warn", "whoami: " .. tostring(werr))
else
  say("info", "who=" .. string.gsub(who, "%s+$", ""))
end

-- Fase 5: digest + cursor multi-round (KV).
local digest = c2.crypto.sha256(
  (findings["sysinfo"] or "") .. "\n" .. (findings["ps"] or ""))
say("info", "digest=" .. digest)
local prev = c2.kv.get("dect-lethal:digest")
if prev == nil then
  say("info", "primera ronda: baseline guardado")
else
  say(prev == digest and "info" or "warn",
    prev == digest and "sin cambios vs baseline" or "CAMBIO vs baseline")
end
c2.kv.set("dect-lethal:digest", digest)
local r = c2.kv.get("dect-lethal:round")
local n = tonumber(r or "0") or 0
c2.kv.set("dect-lethal:round", tostring(n + 1))
say("info", "round=" .. tostring(n + 1) .. " fin")
