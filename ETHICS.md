# ETHICS — uso autorizado únicamente

Este repositorio distribuye plugins de scripting para ejercicios de Red Team
**autorizados** (laboratorio propio, CTFs, auditorías contratadas). Su uso
fuera de ese marco puede ser ilegal. Al usar o contribuir aceptas:

1. **Autorización previa y escrita.** Solo contra sistemas propios o con
   permiso explícito del propietario. Sin excepciones ("era solo una prueba"
   no es autorización).
2. **Alcance declarado y respetado.** Cada plugin trae `-- scope: lab-only`
   y el marketplace de c2-dect lo exige al publicar. No re-etiquetes un
   plugin a un alcance que no controlas; no ejecutes fuera del alcance
   declarado.
3. **No destructivo por diseño.** Los plugins aceptados aquí son solo
   lectura + estado (triage, inventario, watchdog). No se aceptan
   contribuciones que borren, cifren, exfiltren a terceros, persistan,
   se propaguen o eludan controles fuera del lab. Propuestas con
   capacidades ofensivas reales se rechazan (ver PLUGIN_SPEC.md).
4. **Trazabilidad.** Campañas con firma Ed25519 (`sig/kid`), ventanas
   `exp/nbf` cortas y auditoría (`script_rejected`, `tenant_rejected`) en
   el teamserver. Lo que no puedas explicar en un informe, no lo ejecutes.
5. **Divulgación responsable.** Si encuentras un abuso o una vía de escape
   del sandbox, repórtala como issue privado al mantenedor antes de
   publicarla. Sin PoCs weaponizados en issues públicos.
6. **Cumplimiento legal.** Respeta la legislación aplicable (acceso ilícito,
   interceptación, protección de datos). Si tu jurisdicción exige más que
   este documento, manda tu jurisdicción.

Violar estas reglas = causa de bloqueo y reporte. La licencia MIT cubre el
código; este documento cubre su uso.
