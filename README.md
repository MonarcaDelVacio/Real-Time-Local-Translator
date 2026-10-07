# Real-Time Local Translator

Traductor de audio del sistema en tiempo real para Windows, diseñado para reuniones, clases, llamadas y contenido multimedia.

## Objetivo

Capturar el audio que reproduce el PC, detectar automáticamente el idioma hablado, transcribirlo y traducirlo localmente.

## Principios

- **Gratis y local:** no requiere API de pago, cuenta, suscripción, créditos ni servidor externo.
- **Offline durante el uso:** la compilación distribuida incluye los modelos locales preparados; no necesita Internet para transcribir o traducir.
- **Audio del sistema:** utiliza Windows WASAPI Loopback mediante SoundCard, por lo que puede capturar Zoom, Meet, Teams, Discord, navegador y otras aplicaciones que reproduzcan audio.
- **Arquitectura reemplazable:** los motores están aislados detrás de contratos de dominio.
- **Interfaz sin bloqueo:** Whisper y la captura se inicializan en un hilo de trabajo, no en el hilo de la interfaz.

## Arquitectura

Windows system audio → WASAPI Loopback → VAD → faster-whisper → idioma detectado → Argos Translate → PySide6

faster-whisper puede cargar un modelo CTranslate2 desde un directorio local y usar `local_files_only=True`, evitando descargas durante el uso normal.

SoundCard proporciona captura de loopback para Windows.

Argos Translate usa paquetes de traducción instalados localmente y puede utilizar idiomas intermedios cuando existen los paquetes necesarios.

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

## Probar la versión descargable

La compilación de Windows se genera automáticamente mediante GitHub Actions. El paquete de prueba contiene:

- instalador `RealTimeLocalTranslatorSetup-0.3.0.exe`;
- versión portable;
- modelos locales incluidos;
- dependencias Python incluidas;
- ejecutable sin consola.

El instalador está pensado para Windows 10/11 de 64 bits.

### Primera prueba

1. Instala el `.exe`.
2. Inicia **Real-Time Local Translator**.
3. Selecciona el idioma destino.
4. Reproduce un vídeo, música con voz, una reunión o cualquier audio por el dispositivo de salida predeterminado de Windows.
5. Pulsa **Iniciar**.
6. Espera unos segundos para que aparezca el primer segmento traducido.
7. Pulsa **Detener** para finalizar.

La aplicación no necesita Python instalado cuando se usa el instalador.

### Desarrollo

Para trabajar sobre el código:

1. Instala Python 3.11.
2. Ejecuta `scripts\\run_dev.bat`.
3. La primera preparación descarga Whisper y los paquetes Argos.
4. Reproduce audio por los altavoces/auriculares de Windows.
5. Ejecuta `scripts\\diagnose_audio.py` si quieres comprobar la captura.
6. La aplicación se abre después de preparar los modelos.

## Estado de la versión 0.3.0 Preview

- [x] Arquitectura por capas
- [x] Captura Windows WASAPI loopback
- [x] VAD local básico
- [x] faster-whisper local
- [x] Detección automática de idioma mediante Whisper
- [x] Argos Translate local
- [x] Paquetes Argos portables dentro de `models/argos`
- [x] Segmentación por silencio
- [x] Límite de duración/buffer
- [x] Errores aislados por segmento
- [x] Inicialización de motores fuera del hilo GUI
- [x] Build PyInstaller reproducible
- [x] Instalador Inno Setup
- [x] Build automatizado de Windows mediante GitHub Actions
- [ ] Validación real de WASAPI en hardware Windows
- [ ] Medición de latencia y rendimiento en equipos modestos
- [ ] VAD neuronal de mejor calidad
- [ ] Historial de sesiones
- [ ] Configuración avanzada de dispositivo/modelo
- [ ] Pulido visual y accesibilidad
- [ ] Firma digital del instalador

**Importante:** la Preview está preparada para la primera prueba de hardware, pero la captura WASAPI y el rendimiento real deben validarse en el PC del usuario. No se debe considerar una versión final hasta completar esa validación.

## Privacidad

El audio de las reuniones no se envía a un proveedor externo. Los modelos y paquetes se procesan localmente. Los datos de ejecución, logs y grabaciones de diagnóstico no se incluyen en Git.

## Licencia

MIT para el código de este proyecto. Las licencias de modelos y dependencias de terceros deben revisarse antes de redistribuir una versión comercial o pública.
