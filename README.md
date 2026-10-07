# Real-Time Local Translator

Traductor de audio del sistema en tiempo real para Windows, diseñado para reuniones, clases, llamadas y contenido multimedia.

## Objetivo

Capturar el audio que reproduce el PC, detectar automáticamente el idioma hablado, transcribirlo y traducirlo localmente.

## Principios

- **Gratis y local:** no requiere API de pago, cuenta, suscripción, créditos ni servidor externo.
- **Offline después de la preparación:** Internet se utiliza durante la instalación inicial para descargar modelos y paquetes; el procesamiento normal es local.
- **Audio del sistema:** utiliza Windows WASAPI Loopback mediante SoundCard, por lo que puede capturar Zoom, Meet, Teams, Discord, navegador y otras aplicaciones que reproduzcan audio.
- **Arquitectura reemplazable:** los motores están aislados detrás de contratos de dominio.

## Arquitectura

Windows system audio → WASAPI Loopback → VAD → faster-whisper → idioma detectado → Argos Translate → PySide6

faster-whisper permite cargar un modelo CTranslate2 desde un directorio local y ejecutar con 'local_files_only=True'; esto evita descargas durante el uso normal.

SoundCard proporciona captura de loopback para Windows.

Argos Translate funciona con paquetes de traducción instalados localmente y puede encadenar idiomas intermedios cuando existen los paquetes necesarios.

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

## Probar en Windows

### Opción de desarrollo

1. Instala Python 3.11.
2. Descarga/clona el repositorio.
3. Ejecuta scripts\\run_dev.bat.
4. La primera preparación descarga el modelo Whisper y los paquetes Argos.
5. Reproduce audio por los altavoces/auriculares de Windows.
6. Ejecuta scripts\\diagnose_audio.py si quieres validar primero la captura.
7. La aplicación se abre después de preparar los modelos.

La primera preparación puede tardar y ocupar varios cientos de MB. Después, el procesamiento no necesita conexión.

### Crear el instalador

En Windows, con las dependencias preparadas:

powershell -ExecutionPolicy Bypass -File build\\build_windows.ps1

Después abre installer\\RealTimeLocalTranslator.iss con Inno Setup para generar el instalador.

El build copia los modelos locales dentro de la distribución. El objetivo es que el instalador final pueda ejecutarse sin Python instalado.

## Estado de la versión 0.2.0

- [x] Arquitectura por capas
- [x] Captura Windows WASAPI loopback
- [x] VAD local básico
- [x] faster-whisper local
- [x] Detección automática de idioma mediante Whisper
- [x] Argos Translate local
- [x] Paquetes Argos portables dentro de models/argos
- [x] Segmentación por silencio
- [x] Límite de duración/buffer
- [x] Errores aislados por segmento
- [x] Interfaz PySide6 inicial
- [x] Build PyInstaller
- [x] Instalador Inno Setup
- [x] Build automatizado de Windows mediante GitHub Actions
- [ ] Validación real de WASAPI en hardware Windows
- [ ] Medición de latencia y rendimiento en equipos modestos
- [ ] VAD neuronal de mejor calidad
- [ ] Historial de sesiones
- [ ] Configuración avanzada de dispositivo/modelo
- [ ] Pulido visual y accesibilidad
- [ ] Firma digital del instalador

**Importante:** esta versión ya tiene una ruta de construcción para obtener un ejecutable de Windows, pero no debe considerarse una versión final hasta probar captura, ASR y traducción en un Windows real.

## Privacidad

El audio de las reuniones no se envía a un proveedor externo. Los modelos y paquetes se procesan localmente. Los datos de ejecución, logs y grabaciones de diagnóstico no se incluyen en Git.

## Licencia

MIT para el código de este proyecto. Las licencias de modelos y dependencias de terceros deben revisarse antes de redistribuir una versión comercial o pública.
