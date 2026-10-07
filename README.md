# Real-Time Local Translator

Traductor de audio en tiempo real para Windows, diseñado para reuniones, clases, llamadas y contenido multimedia.

## Objetivo

Capturar el audio que reproduce el PC, detectar el idioma hablado, transcribirlo y traducirlo localmente en tiempo real.

## Principio fundamental

**Local First:** el uso normal no requiere API, cuenta, suscripción, créditos, servidor externo ni pago por minuto. Después de preparar los modelos y paquetes locales, el procesamiento puede realizarse sin conexión.

## Arquitectura

Audio de Windows → WASAPI Loopback → VAD → faster-whisper → idioma detectado → Argos Translate → interfaz PySide6

La aplicación mantiene una separación estricta entre dominio, aplicación, infraestructura y presentación para poder reemplazar motores sin rehacer la interfaz.

## Tecnologías

- Python 3.11+
- PySide6
- SoundCard + Windows WASAPI loopback
- faster-whisper / Whisper local
- Argos Translate local
- NumPy
- pytest
- PyInstaller
- Inno Setup

faster-whisper ejecuta Whisper mediante CTranslate2 y permite cargar modelos locales; Argos Translate es un motor de traducción offline que utiliza paquetes de idiomas locales.

## Desarrollo en Windows

1. Instala Python 3.11 o superior.
2. Ejecuta `powershell -ExecutionPolicy Bypass -File scripts\\run_dev.ps1`.
3. El script crea el entorno virtual, instala las dependencias y prepara los modelos locales.
4. Para validar primero la captura de audio, ejecuta `python scripts\\diagnose_audio.py` mientras se reproduce audio por Windows.
5. Ejecuta las pruebas con `pytest`.

La preparación inicial puede necesitar Internet porque descarga los modelos y paquetes. Una vez instalados, el funcionamiento normal no depende de servicios externos.

## Estado actual

- [x] Estructura por capas
- [x] Contratos de dominio
- [x] Captura Windows WASAPI loopback
- [x] VAD local básico por energía
- [x] Adaptador faster-whisper
- [x] Adaptador Argos Translate
- [x] Pipeline streaming inicial
- [x] Interfaz de escritorio inicial
- [x] Preparación local de modelos
- [x] Script de diagnóstico de audio
- [x] Base PyInstaller/Inno Setup
- [ ] VAD neuronal optimizado
- [ ] Detección y segmentación avanzada de idioma
- [ ] Subtítulos incrementales de baja latencia
- [ ] Configuración completa de dispositivos/modelos
- [ ] Historial y sesiones
- [ ] Instalador final autocontenido
- [ ] Validación de rendimiento en distintos equipos

## Privacidad

El audio de reuniones no se envía a un proveedor de traducción o transcripción. Las grabaciones de diagnóstico son temporales y están excluidas de Git.

## Licencias

Las licencias de las dependencias y modelos deberán revisarse antes de publicar una distribución final. El proyecto no incorpora servicios de pago ni APIs comerciales obligatorias.
