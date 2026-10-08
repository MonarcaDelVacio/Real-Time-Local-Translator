# Windows test procedure — Preview 0.3.1

## Objetivo

Validar el circuito completo sobre Windows real.

## 1. Instalar

Usa `RealTimeLocalTranslatorSetup-0.3.0.exe`.

No necesitas instalar Python.

## 2. Prueba Inglés → Español

1. Conecta tus auriculares o altavoces.
2. Comprueba que sean el dispositivo de salida predeterminado de Windows.
3. Reproduce una voz clara en inglés.
4. Abre el traductor.
5. Selecciona **Español**.
6. Pulsa **Iniciar**.
7. Espera el primer segmento traducido.
8. Pulsa **Detener**.

## 3. Prueba Español → Inglés

Repite el procedimiento reproduciendo una voz en español y seleccionando **English**.

## Resultado esperado

Windows playback
→ WASAPI Loopback
→ VAD
→ faster-whisper
→ detección de idioma
→ Argos Translate
→ interfaz

## Si no captura audio

En la versión de desarrollo puedes ejecutar:

`scripts\\diagnose_audio.py`

mientras se reproduce audio. El diagnóstico debe detectar el dispositivo de reproducción predeterminado y bloques no silenciosos.

## Limitaciones de la Preview

- Solo se distribuyen Inglés ↔ Español en esta primera prueba.
- La calidad depende del modelo Whisper y de los paquetes Argos.
- La latencia y el consumo deben medirse en hardware real.
- El VAD actual es un detector energético básico.
- La Preview no debe considerarse una versión final hasta completar las pruebas.
