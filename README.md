# Real-Time Local Translator

Traductor de audio del sistema en tiempo real para Windows, diseñado para reuniones, clases, llamadas y contenido multimedia.

## Objetivo

Capturar el audio que reproduce Windows, transcribirlo y traducirlo localmente para el modo actual Inglés ↔ Español.

## Principios

- **Sin servicios de transcripción en la nube durante el uso:** el audio se procesa localmente.
- **Preparación inicial con Internet:** el instalador estándar no incluye los modelos pesados; la aplicación los verifica y descarga al primer inicio.
- **Captura del audio del sistema:** utiliza WASAPI Loopback mediante SoundCard.
- **Reconocimiento en dos etapas:** Nemotron/Sherpa-ONNX ofrece vistas previas de baja latencia; Whisper Small refina las frases finales.
- **Traducción local:** Argos Translate proporciona Inglés ↔ Español.
- **Interfaz desacoplada:** el procesamiento de audio y la preparación de modelos se ejecutan fuera del hilo principal de Qt.

## Arquitectura actual

Audio Windows → WASAPI Loopback → Nemotron/Sherpa-ONNX streaming → Whisper Small (refinamiento final) → Argos Translate → PySide6.

El idioma de origen se selecciona según el idioma de destino en el modo actual de dos idiomas. No es un detector universal de idiomas: con destino español se espera inglés, y con destino inglés se espera español.

## Tecnologías

- Python 3.11+
- PySide6
- SoundCard + Windows WASAPI Loopback
- sherpa-onnx / Nemotron 3.5 ASR streaming
- faster-whisper / Whisper Small local
- Argos Translate local
- NumPy y pytest
- PyInstaller e Inno Setup

## Estado de la versión

El proyecto sigue siendo experimental. Las compilaciones automatizadas verifican las pruebas y el empaquetado, pero todavía es necesario validar el audio, la latencia, el consumo y la recuperación de modelos en equipos Windows reales.

## Probar la versión descargable

La compilación Windows se genera mediante GitHub Actions. El instalador resultante se publica como artefacto del workflow. Hasta que el workflow termine correctamente, no debe considerarse un instalador validado.

El instalador actual usa el esquema de preparación inicial de la versión 0.4.2. El `.exe` no contiene los modelos pesados; estos se descargan en la carpeta de datos del usuario durante el primer inicio.

El instalador no requiere Python.

### Primera prueba

1. Instala el `.exe`.
2. Inicia **Real-Time Local Translator**.
3. Espera a que finalice la preparación inicial de modelos y dependencias. El botón **Iniciar** permanecerá desactivado mientras tanto.
4. Selecciona **Español** como destino.
5. Reproduce una voz en inglés por los altavoces/auriculares de Windows.
6. Pulsa **Iniciar**.
7. Espera unos segundos para que aparezca el primer segmento.
8. Pulsa **Detener**.

Después puedes probar el recorrido contrario seleccionando **English** y reproduciendo español.

Si la preparación inicial falla, la aplicación muestra un cuadro de error con texto seleccionable y botón para copiarlo.

## Desarrollo

1. Instala Python 3.11.
2. Ejecuta `scripts\\run_dev.bat`.
3. La preparación descarga el modelo Whisper y los paquetes Argos necesarios.
4. Reproduce audio por los altavoces/auriculares.
5. Ejecuta `scripts\\diagnose_audio.py` si quieres comprobar primero la captura.

## Estado

El proyecto sigue siendo experimental. El CI valida pruebas automatizadas y empaquetado, pero no sustituye las pruebas reales de audio y rendimiento en Windows.

- [x] Captura del audio del sistema mediante WASAPI Loopback.
- [x] Transcripción provisional en vivo con Nemotron/Sherpa-ONNX.
- [x] Refinamiento de frases finalizadas con Whisper Small.
- [x] Traducción local Inglés ↔ Español mediante Argos.
- [x] Preparación y comprobación de modelos al iniciar.
- [x] Reparación de configuraciones Whisper inválidas y paquetes Argos no utilizables.
- [x] Refinamiento Whisper desacoplado del consumidor de audio.
- [x] Historial visual acotado y transcripción original guardada por separado.
- [x] SHA-256 generado para el instalador de cada compilación.
- [ ] Validación de extremo a extremo en equipos Windows reales.
- [ ] Pruebas de estrés prolongadas para cuantificar pérdida de audio y latencia.
- [ ] Bloqueo completo de versiones de dependencias para builds reproducibles.
- [ ] Firma digital del instalador.
- [ ] Centralizar todos los modelos en activos propios de GitHub Releases.

### Procedencia de los recursos

En el flujo actual, el modelo Nemotron/Sherpa se obtiene desde GitHub Releases, Whisper Small desde Hugging Face y los paquetes Argos desde su índice de paquetes. La preparación inicial necesita Internet; el procesamiento de audio y la traducción posteriores se realizan localmente.

## Privacidad

El audio no se envía a un proveedor externo. Los modelos y paquetes se procesan localmente.

## Licencia

MIT para el código del proyecto. Las licencias de modelos y dependencias de terceros deben revisarse antes de una distribución comercial.


## Historial técnico

### Experimental 0.4.1 quality pass

This branch uses stabilized streaming translation: partial ASR is not sent to the translator, the source language is forced for the current English↔Spanish mode, and the Nemotron 1120 ms profile is used for additional look-ahead context.

### Experimental 0.4.2 accuracy pass

The streaming path now uses a two-stage ASR design: Nemotron provides immediate live transcription, while each completed utterance is re-transcribed locally with Whisper Small before translation. This second pass is intended to recover words missed or misrecognized during fast speech. Endpoint timing was also tightened so natural pauses are recognized sooner without translating unstable partial hypotheses.
