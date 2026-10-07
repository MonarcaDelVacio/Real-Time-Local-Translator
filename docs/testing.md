# Windows test procedure

## Objetivo

Validar la primera Preview distribuible sobre Windows real. GitHub Actions puede comprobar instalación, tests y construcción, pero no puede sustituir la prueba del audio de reproducción del PC.

## 1. Instalar

Usa `RealTimeLocalTranslatorSetup-0.3.0.exe`.

No necesitas instalar Python.

## 2. Preparar el audio

1. Conecta los auriculares o altavoces que utilizas normalmente.
2. Comprueba que Windows los tenga como dispositivo de salida predeterminado.
3. Reproduce una voz clara: vídeo, reunión grabada o navegador.
4. Abre el traductor.

## 3. Primera prueba

1. Selecciona **Español** como destino.
2. Pulsa **Iniciar**.
3. Espera unos segundos.
4. Comprueba que aparezcan segmentos en la ventana.
5. Cambia el audio de origen si quieres comprobar otros idiomas.
6. Pulsa **Detener**.

## Resultado esperado

La cadena debe funcionar así:

Windows playback
→ WASAPI Loopback
→ VAD
→ faster-whisper
→ detección de idioma
→ Argos Translate
→ interfaz

## Si no captura audio

La versión de desarrollo incluye:

`scripts\\diagnose_audio.py`

Ejecuta el diagnóstico mientras se está reproduciendo audio. Debe detectar el dispositivo de reproducción predeterminado y bloques no silenciosos.

## Limitaciones conocidas de la Preview

- La calidad de traducción depende de los paquetes Argos instalados.
- El modelo Whisper `small` prioriza equilibrio entre precisión y consumo de CPU.
- La latencia todavía debe medirse en hardware real.
- La Preview utiliza un VAD energético; posteriormente se puede sustituir por un VAD neuronal.
- El soporte de distintos dispositivos de audio y configuraciones multicanal se seguirá ampliando.

La Preview no debe considerarse una versión final hasta completar estas pruebas.
