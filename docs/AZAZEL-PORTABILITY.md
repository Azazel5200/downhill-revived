# Azazel5200 / Nexo — plan de portabilidad nativa

**Estado:** planificación técnica; no hay ports adicionales compilados.

**Base del fork al iniciar:** Downhill Revived v0.7.11, commit `5a3883285ad102a0d5c8d6b69e1ae915ad3b2d96`.

**Auditoría inicial:** v0.7.10, commit `f7be0e2c5db9739b8b5dc77f875a8bdbd418cc3d`.
**Fecha:** 2026-11-05.

Este documento registra el trabajo del futuro fork de Azazel5200. No modifica
el código de decompilación que debe seguir coincidiendo con el ejecutable de
PS2. Los cambios del port deberán permanecer en `port/` y someterse a las
pruebas establecidas por `AGENTS.md`, `docs/TESTING.md` y `tools/check.py`.

## Objetivo

Mantener el juego original, sus físicas, rivales, recursos, audio, menús y
progresión mientras se desarrollan versiones nativas para:

| Destino | Prioridad del usuario | Soporte confirmado del proyecto base | Estado del fork |
|---|---|---|---|
| Windows x64 moderno | referencia | Sí | Heredado, aún no probado localmente |
| Windows ARM64 | media | No | Análisis inicial |
| Windows 8.1 x64 / Celeron N2805 | alta | No | Análisis inicial |
| PS Vita ARMv7 | alta | No | Análisis inicial |

No confundir compilación, lanzamiento de una ventana, ejecución de menús y
jugabilidad completa; son hitos distintos.

## Idioma del juego: español (requisito del jugador)

El usuario quiere **jugar en español**: menús, opciones, mensajes, pantallas de
carga y textos durante el juego. La documentación de upstream
(`docs/findings/100-other-releases.md`) confirma que la edición europea
`SLES-52202` incluye español entre cinco idiomas; sus bancos de voces son
idénticos a los estadounidenses y por tanto **las voces siguen en inglés**.

La versión actual de Downhill Revived solamente acepta la edición
estadounidense `SCUS-97177`. No afirmar que el fork ya está traducido ni que
la ISO europea funciona. Hay dos rutas de investigación, aún sin elegir:

1. **Localización sobre el núcleo estadounidense:** mapear de forma verificable
   las cadenas y los recursos visibles, evaluar un mecanismo de sustitución
   compatible con el sistema de textos y las fuentes, sin alterar físicas o
   progreso. No asumir que cambiar cadenas por sí solo cubre los recursos.
2. **Núcleo europeo:** adaptar la edición `SLES-52202`, conservando sus tablas
   de cinco idiomas, fuentes, menús y recursos. Upstream estima 180–290 horas
   para el soporte regional: es una estimación de investigación, no una tarea
   completada ni un plazo prometido.

**Pruebas de idioma pendientes:**

- [ ] `ES0` — Inventariar en el código y recursos locales los textos, fuentes
  y elementos gráficos que requieren localización, sin publicar datos del juego.
- [ ] `ES1` — Probar el método elegido en menú principal, configuración,
  selección de piloto/bicicleta, HUD y pantallas de carga.
- [ ] `ES2` — Verificar tildes, `ñ`, caracteres especiales, ancho de texto y
  legibilidad a 960×544, 720p y resoluciones de escritorio.
- [ ] `ES3` — Verificar que la traducción no modifica física, IA, partidas ni
  lógica temporal; comprobar persistencia del idioma elegido.

Por defecto, la preferencia del port será español, con opción para restaurar
el idioma original cuando se implemente. Los recursos originales serán
aportados localmente por el usuario; no subir texto extraído, videos,
fuentes comerciales ni otros datos protegidos al fork.

## Arquitectura que debemos conservar

1. `port/tools/build_wasm.py`: transforma la lógica original en el módulo
   `wasm32` del juego. Requiere archivos de la copia personal del disco del
   usuario. No modificar `src/` para adaptar plataformas.
2. `port/tools/build_host64.py`: convierte `wasm32` con wasm2c e integra
   host C, SDL3, `fiber`, memoria y renderer Rust/wgpu. Las variantes actuales
   son `win-x64`, `linux-x64`, `macos-arm64`, `android-arm64`.
3. `port/gs/`: conserva interfaces de la GS y la ruta exacta frente a la
   nativa. Las operaciones que alimentan el estado del juego deben seguir
   siendo correctas; optimizar la imagen no autoriza cambiar las físicas.
4. `port/hle/`, `port/runtime/`: reutilización sujeta a trazas de estado,
   contratos de coma flotante y pruebas de memoria.

## Gates de Windows ARM64

- [ ] `A0` — Preparar compiladores ARM64 nativos: LLVM/clang-cl, SDK y CRT
  Windows ARM64, Rust `aarch64-pc-windows-msvc`, SDL3 y DXC apropiados.
- [ ] `A1` — Añadir destino `win-arm64` sin afectar `win-x64`; `--fiber-test`
  compila. Implementar ABI Windows ARM64 con manejo correcto de pila,
  registros y unwind; no copiar sin adaptar el `fiber_arm64.c` de AAPCS64.
- [ ] `A2` — Verificar memoria guest (incluidos aliases, guard pages y fallos)
  con el test de fibers y fixtures sintéticos.
- [ ] `A3` — Crear y presentar imagen con renderer wgpu en DX12 o Vulkan;
  verificar el dispositivo físico elegido y la ruta de compilación shaders.
- [ ] `A4` — Boot del juego desde imagen local aportada por el usuario;
  comparar trazas de título, menús y carrera contra una versión x64 base.
- [ ] `A5` — Medir fps/p50/p99, RAM, CPU y GPU en Windows 11 ARM64 real.

## Gates de Windows 8.1 / Bay Trail

- [ ] `B0` — Medir las características reales de la Intel HD (D3D11 feature
  levels, OpenGL y controlador) y memoria libre de la tablet.
- [ ] `B1` — Reemplazar en el backend Windows antiguo el uso de `VirtualAlloc2`
  y `MapViewOfFile3`, que requieren Windows 10; preservar los espejos de RAM y
  detectar conflictos de reserva/mapeo. Ejecutar pruebas de fallos de memoria.
- [ ] `B2` — Backend gráfico Direct3D 11 u OpenGL según evidencia; revisar
  código histórico `v0.3.1` sólo como referencia (fue retirado del main).
- [ ] `B3` — Detectar CPU, memoria y GPU; evitar exigencias DX12/Vulkan, y
  permitir resoluciones desde 640×360 hasta 1280×720.
- [ ] `B4` — Boot y carrera; comparar estado y medir p50/p99 y consumo en
  N2805 con Windows 8.1 x64. 720p/30 es un objetivo, no un resultado.

## Gates de PlayStation Vita

- [ ] `V0` — Compilar una app ARMv7 con VitaSDK y empaquetar un VPK sin
  contenido comercial. Verificar ambos sticks, archivos y audio básicos.
- [ ] `V1` — Inicializar sceGxm/vitaGL, dibujar geometría 3D original a
  960×544 y medir GPU, CPU y memoria en Vita física.
- [ ] `V2` — Diseñar el espacio de direcciones guest de 32 bits. El host
  actual reserva 8 GiB *virtuales* (`guest_memory.c`), que no caben en el
  espacio de direcciones de ARMv7. No asumir que basta reducir un contador.
- [ ] `V3` — Adaptar `fiber` para ABI ARMv7 y definir presupuesto de RAM,
  stacks, texturas y búferes que respete el entorno Vita.
- [ ] `V4` — Implementar la ruta gráfica GS necesaria para el juego, incluidas
  consultas que afectan la simulación; validar contra capturas/trazas base.
- [ ] `V5` — Arranque, menús y carrera con datos locales; medir 30 FPS estables
  sólo cuando existan los casos reales reproducibles.

La prueba temprana `V0/V1` puede realizarse antes del port completo ARM64,
para detectar riesgos específicos de Vita lo antes posible.

## Pruebas, publicación y seguridad

- Ramas cortas para cambios de un solo subsistema; no desarrollar tres
  variantes paralelas de la lógica del juego.
- No fusionar directamente a `main`; cada cambio requiere PR, explicación
  de las pruebas y revisión del diff.
- `python tools/check.py docs` para documentación; `quick`/`port` y trazas
  de estado según `AGENTS.md` para cambios ejecutables.
- No publicar ISO, ELF de PS2, módulos IOP, arte comercial, savestates,
  credenciales ni rutas personales. Los tests con recursos del juego
  permanecerán localmente y fuera del seguimiento Git.
- Conservar `LICENSE`, `docs/CREDITS.md`, `port/release/THIRD-PARTY-NOTICES.txt`
  y avisos de los autores de cada código o biblioteca incorporada.
- Separar los resultados medidos de las hipótesis. El primer laboratorio
  de geometría sintética por CPU no demuestra soporte del renderer Vita/Intel.

**Créditos:** Incognito Entertainment / Sony Computer Entertainment America
(juego original); skuza-oss y colaboradores (Downhill Revived); los autores
de las dependencias utilizadas; Pedro Soto/Brandon Gil y colaboradores
(DownHill-Port-PC, cuando se utilice su investigación o código);
Azazel5200 / Nexo (adaptaciones y pruebas nuevas).
