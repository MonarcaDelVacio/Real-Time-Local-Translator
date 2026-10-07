# Real-Time Local Translator

Traductor de audio en tiempo real para reuniones, clases, llamadas y contenido reproducido en el PC.

## Objetivo

El proyecto busca ofrecer una alternativa local, gratuita y sin límites artificiales para capturar audio, detectar el idioma, transcribirlo y traducirlo al idioma elegido.

El procesamiento está diseñado para ejecutarse localmente, sin API de pago ni cuenta en la nube.

## Estado actual

**Versión:** 0.1.0-dev

La primera etapa establece la arquitectura y los contratos del dominio. Todavía no se ha conectado ningún motor real de audio, ASR o traducción.

## Arquitectura

`Audio → VAD → ASR → detección de idioma → traducción → sesión → UI`

- `app/presentation`: interfaz gráfica.
- `app/application`: casos de uso y orquestación.
- `app/domain`: modelos y contratos independientes.
- `app/infrastructure`: integraciones concretas.
- `engines/`: adaptadores de motores reemplazables.
- `tests/`: pruebas automatizadas.
- `docs/`: documentación técnica.

## Principio principal

**Local First:** el funcionamiento normal no depende de servidores externos ni servicios de pago.

## Desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Las dependencias de ejecución se incorporarán después de validar cada componente durante la Fase 0.

## Licencia

La licencia se definirá antes de la primera versión pública estable.
