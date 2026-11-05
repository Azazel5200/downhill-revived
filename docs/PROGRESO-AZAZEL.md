# Progreso en español — Downhill Domination nativo

**Equipo:** Azazel5200 / Nexo

**Fecha inicial:** 5 de noviembre de 2026

**Estado:** proyecto de portabilidad iniciado, sin ports nuevos ejecutados.

Este documento distingue los avances de **Downhill Revived** de los realizados
en este fork. Nunca se marcará una característica como completada únicamente
porque exista código: debe superar pruebas reales en su plataforma.

## 1. Base que aprovechamos (proyecto original)

| Componente | Evidencia de Downhill Revived | ¿Probado por nosotros? |
|---|---|---|
| Reconstrucción del código del juego | 3439/3474 funciones coincidentes (98,17 %) | No; dato del proyecto original |
| Reconstrucción del motor | 1088/1119 funciones coincidentes (92,76 %) | No; dato del proyecto original |
| Juego + motor, objetivo de decompilación | 4527/4593 funciones coincidentes (97,03 %) | No; dato del proyecto original |
| Windows x64 | Port nativo mantenido por upstream | No hay prueba en nuestros equipos |
| Linux x64 / macOS ARM64 / Android ARM64 | Builds experimentales documentadas | No hay prueba en nuestros equipos |

Los porcentajes corresponden al README del repositorio original revisado el
5/11/2026, no a un porcentaje de finalización de nuestros ports.

## 2. Avance propio

| Actividad | Estado | Verificación |
|---|---|---|
| Auditoría de repositorios y licencias | Hecha | Código fuente y avisos de terceros inspeccionados |
| Plan técnico ARM64, Windows 8.1 y Vita | Hecho | Documento `docs/AZAZEL-PORTABILITY.md` |
| Requisito de juego en español | Documentado | La edición europea tiene español; el núcleo estadounidense actual no lo ofrece |
| Traducción de menús, opciones y textos del juego | Pendiente | No existe implementación ni prueba propia de localización |
| Prueba independiente C11 sin datos del juego | Hecha | Compiló en Linux x64; geometría 3D por CPU y pruebas unitarias |
| Verificadores de documentación upstream | Hecha | `python3 tools/check.py docs` pasó en el clon de auditoría |
| Compilación completa de Downhill Revived en nuestros equipos | Pendiente | Requiere preparar toolchain y copia local del juego |
| Ejecutable nativo Windows ARM64 | Pendiente | No se ha compilado ni ejecutado |
| Ejecutable para Windows 8.1/Celeron N2805 | Pendiente | No se ha compilado ni ejecutado |
| VPK nativo PS Vita | Pendiente | No se ha compilado ni ejecutado |

La prueba C11 fue un **laboratorio separado**, sin código del juego ni backend
gráfico de las plataformas. No equivale a una versión jugable.

## 3. Próximas metas comprobables

1. **A0:** comprobar toolchain y dependencias de Windows ARM64; preparar una
   compilación mínima del host sin cambiar la lógica de PS2.
2. **V0/V1:** preparar pronto una pequeña aplicación VitaSDK + vitaGL con
   geometría original, controles y mediciones de memoria/tiempo.
3. **B0:** identificar los niveles reales de Direct3D/OpenGL y el driver de la
   tablet con Celeron N2805 antes de escoger backend.
4. Integrar paulatinamente la lógica y los recursos locales del usuario,
   verificando menús, carrera, físicas, IA y audio frente a la referencia.
5. **ES0:** identificar las cadenas, fuentes y recursos gráficos que se deben
   traducir; decidir entre localización del núcleo USA y soporte europeo
   después de medir el alcance de ambas opciones.

## 4. Objetivos de rendimiento (NO resultados)

| Plataforma | Meta | Estado |
|---|---|---|
| PS Vita | 960×544 / 30 FPS estables | Sin medición |
| Celeron N2805, Windows 8.1 | 1280×720 / 30 FPS | Sin medición |
| Windows ARM64 | Ejecución totalmente nativa | Sin compilación |
| Windows x64 | Mantener compatibilidad de upstream | Sin prueba local |

## 5. Cómo registraremos una prueba

Cada resultado nuevo debe indicar fecha, equipo, sistema, commit, resolución,
configuración gráfica, escena, FPS promedio/p50/p99, RAM utilizada, errores y
si se contrastó con el comportamiento del juego original.

No se publicarán ISOs, ejecutables de PS2 ni recursos comerciales. El usuario
proporcionará localmente su propia copia cuando corresponda.

## 6. Créditos y licencias

Juego original: Incognito Entertainment / Sony Computer Entertainment America.
Base y decompilación: skuza-oss y colaboradores de Downhill Revived.
Investigación complementaria: Pedro Soto, Brandon Gil y colaboradores de
DownHill-Port-PC. Adaptaciones y pruebas nuevas: Azazel5200 / Nexo.
Conservar avisos y condiciones GPL-3.0-or-later y las licencias individuales
de cada herramienta o biblioteca realmente incorporada.
