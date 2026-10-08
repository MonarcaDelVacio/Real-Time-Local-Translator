# Real-Time Local Translator

Traductor de audio del sistema en tiempo real para Windows, diseñado para reuniones, clases, llamadas y contenido multimedia.

## Objetivo

Capturar el audio que reproduce el PC, detectar automáticamente el idioma hablado, transcribirlo y traducirlo localmente.

## Principios

- **Gratis y local:** no requiere API de pago, cuenta, suscripción, créditos ni servidor externo.
- **Offline durante el uso:** la compilación distribuida incluye los modelos locales preparados; no necesita Internet para transcribir o traducir.
- **Audio del sistema:** utiliza Windows WASAPI Loopback mediante SoundCard.
- **Arquitectura reemplazable:** los motores están aislados detrás de contratos de dominio.
- **Interfaz sin bloqueo:** Whisper y la captura se inicializan en un hilo de trabajo.

## Arquitectura

Windows system audio → WASAPI Loopback → VAD → faster-whisper → idioma detectado → Argos Translate → PySide6

faster-whisper puede cargar un modelo CTranslate2 desde un directorio local y usar `local_files_only=True`, evitando descargas durante el uso normal.

SoundCard proporciona captura de loopback para Windows.

Argos Translate usa paquetes de traducción instalados localmente y permite utilizar idiomas intermedios cuando existen los paquetes necesarios.

## Tecnologías

- Python 3.11+
- PySide6
- SoundCard + Windows WASAPI Loopback
- faster-whisper / Whisper local
- Argos Translate local
- NumPy
- pytest
- PyInstaller
- Inno Setup

## Preview 0.3.1

La primera compilación descargable está enfocada en una validación completa y manejable del circuito:

**Inglés ↔ Español**

Incluye:

- modelo Whisper `base` multilingüe;
- detección automática del idioma mediante Whisper;
- traducción local Inglés → Español;
- traducción local Español → Inglés;
- captura del audio de salida de Windows;
- instalador Windows x64;
- Python y dependencias incluidos;
- modelos incluidos;
- funcionamiento sin Internet después de la instalación.

La selección de más idiomas se ampliará después de validar correctamente audio, latencia, consumo y estabilidad en hardware Windows real.

## Probar la versión descargable

La compilación Windows se genera mediante GitHub Actions. El instalador resultante se publica como artefacto del workflow. Hasta que el workflow termine correctamente, no debe considerarse un instalador validado.

El instalador resultante es:

`RealTimeLocalTranslatorSetup-0.3.1.exe`

El instalador no requiere Python.

### Primera prueba

1. Instala el `.exe`.
2. Inicia **Real-Time Local Translator**.
3. Selecciona **Español** como destino.
4. Reproduce una voz en inglés por los altavoces/auriculares de Windows.
5. Pulsa **Iniciar**.
6. Espera unos segundos para que aparezca el primer segmento.
7. Pulsa **Detener**.

Después puedes probar el recorrido contrario seleccionando **English** y reproduciendo español.

## Desarrollo

1. Instala Python 3.11.
2. Ejecuta `scripts\\run_dev.bat`.
3. La preparación descarga el modelo Whisper y los paquetes Argos necesarios.
4. Reproduce audio por los altavoces/auriculares.
5. Ejecuta `scripts\\diagnose_audio.py` si quieres comprobar primero la captura.

## Estado

- [x] Arquitectura por capas
- [x] Captura Windows WASAPI loopback
- [x] VAD local básico
- [x] faster-whisper local
- [x] Detección automática de idioma mediante Whisper
- [x] Argos Translate local
- [x] Paquetes Argos portables
- [x] Segmentación por silencio
- [x] Límite de duración/buffer
- [x] Errores aislados por segmento
- [x] Inicialización de motores fuera del hilo GUI
- [x] Build PyInstaller reproducible
- [x] Instalador Inno Setup
- [x] Build automatizado de Windows
- [ ] Validación real de WASAPI en hardware Windows
- [ ] Medición de latencia y rendimiento
- [ ] VAD neuronal
- [ ] Historial de sesiones
- [ ] Selector avanzado de dispositivo
- [ ] Ampliación de idiomas
- [ ] Firma digital

**Importante:** la Preview está preparada para la primera prueba de hardware, pero no se considera versión final hasta comprobar captura, ASR, traducción y estabilidad en Windows real.

## Privacidad

El audio no se envía a un proveedor externo. Los modelos y paquetes se procesan localmente.

## Licencia

MIT para el código del proyecto. Las licencias de modelos y dependencias de terceros deben revisarse antes de una distribución comercial.
