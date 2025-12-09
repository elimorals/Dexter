# Configuración de API Local de Inferencia

Este documento describe cómo configurar Dexter para usar una API local de inferencia en lugar de la API de OpenAI.

## Cambios Realizados

Se han modificado los siguientes archivos para soportar APIs locales compatibles con OpenAI:

1. **`src/dexter/model.py`** - Soporte para `OPENAI_BASE_URL` en Python
2. **`dexter-ts/src/model/llm.ts`** - Soporte para `OPENAI_BASE_URL` en TypeScript
3. **`src/dexter/utils/env.py`** - Validación de API key opcional para APIs locales
4. **`dexter-ts/src/utils/env.ts`** - Validación de API key opcional para APIs locales
5. **`env.example`** - Documentación de la nueva variable de entorno

## Configuración

### Variables de Entorno

Para usar una API local, configura las siguientes variables de entorno en tu archivo `.env`:

```bash
# URL base de la API local (debe incluir /v1 al final)
OPENAI_BASE_URL=http://localhost:1234/v1

# API key (opcional para APIs locales sin autenticación)
# Puede ser cualquier valor o incluso omitirse
OPENAI_API_KEY=local-key-123
```

### Ejemplo de Uso

1. Asegúrate de que tu servidor local esté corriendo en `http://localhost:1234`

2. Crea o edita tu archivo `.env`:
   ```bash
   OPENAI_BASE_URL=http://localhost:1234/v1
   OPENAI_API_KEY=local-key-123
   ```

3. Ejecuta Dexter normalmente:
   ```bash
   uv run dexter-agent
   ```

### Formato de la API Local

La API local debe ser compatible con el formato de OpenAI. El endpoint esperado es:

```
POST http://localhost:1234/v1/chat/completions
```

Con el siguiente formato de request (ejemplo del usuario):

```json
{
    "model": "qwen3-vl-30b-a3b-thinking",
    "messages": [
        {
            "role": "system",
            "content": "Always answer in rhymes. Today is Thursday"
        },
        {
            "role": "user",
            "content": "What day is it today?"
        }
    ],
    "temperature": 0.7,
    "max_tokens": -1,
    "stream": false
}
```

### Notas Importantes

- La URL base debe incluir `/v1` al final (por ejemplo: `http://localhost:1234/v1`)
- LangChain añadirá automáticamente `/chat/completions` al hacer las peticiones
- Si tu API local no requiere autenticación, puedes usar cualquier valor para `OPENAI_API_KEY` o incluso omitirlo
- El modelo que especifiques debe coincidir con el nombre del modelo en tu servidor local (ej: `qwen3-vl-30b-a3b-thinking`)

### Cambiar el Modelo

Puedes cambiar el modelo usando el comando `/model` en el CLI de Dexter. El modelo que especifiques debe estar disponible en tu servidor local.

## Compatibilidad

Esta implementación es compatible con:
- Servidores que implementan la API compatible con OpenAI (como LM Studio, Ollama con servidor OpenAI-compatible, etc.)
- APIs que soportan el formato estándar de mensajes de OpenAI
- Streaming y no-streaming
- Structured output (function calling)

## Compatibilidad con LM Studio

LM Studio es una aplicación popular para ejecutar modelos localmente. Dexter está optimizado para trabajar con LM Studio, pero hay algunas consideraciones importantes:

### Problemas Conocidos y Soluciones

#### 1. Error: "Invalid tool_choice type: 'object'"

**Problema**: LM Studio solo acepta `tool_choice` como string ("none", "auto", "required"), no como objeto. LangChain a veces envía tool_choice como objeto cuando usa `with_structured_output`.

**Solución**: El código ahora detecta automáticamente cuando se usa una API local y maneja este error:
- Intenta usar `json_mode` como método alternativo para structured output
- Si falla, hace un fallback a llamadas regulares y parsea la respuesta manualmente
- Los errores de tool_choice se manejan automáticamente con reintentos

#### 2. Error de LangSmith (403 Forbidden)

**Problema**: Si `LANGSMITH_TRACING=true` pero no tienes una API key válida, verás errores 403.

**Solución**: 
- El código ahora desactiva automáticamente LangSmith si está habilitado pero no hay API key válida
- Para deshabilitar manualmente, configura en tu `.env`:
  ```bash
  LANGSMITH_TRACING=false
  ```
  O simplemente no incluyas las variables de LangSmith

### Configuración Recomendada para LM Studio

```bash
# API Local
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio  # Cualquier valor funciona

# Deshabilitar LangSmith (opcional, se desactiva automáticamente si no hay API key)
LANGSMITH_TRACING=false
```

### Modelos Compatibles

LM Studio funciona mejor con modelos que soportan function calling:
- Llama 3.1 (8B, 70B)
- Qwen2.5
- Mistral
- Otros modelos que soporten OpenAI-compatible function calling

**Nota**: Algunos modelos pueden no soportar structured output perfectamente. En ese caso, el código hará fallback automático a respuestas regulares.

## Troubleshooting

Si encuentras problemas:

1. **Verifica que tu servidor local esté corriendo**: Asegúrate de que LM Studio (o tu servidor) esté ejecutándose y escuchando en el puerto correcto
2. **Verifica la URL base**: Debe incluir `/v1` al final (por ejemplo: `http://localhost:1234/v1`)
3. **Prueba con curl**: Verifica que la API funciona manualmente:
   ```bash
   curl http://localhost:1234/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "tu-modelo", "messages": [{"role": "user", "content": "test"}]}'
   ```
4. **Revisa los logs**: Revisa los logs de LM Studio para ver si las peticiones están llegando
5. **Deshabilita LangSmith**: Si ves errores 403 de LangSmith, configura `LANGSMITH_TRACING=false`
6. **Verifica el modelo**: Asegúrate de que el nombre del modelo coincida exactamente con el que está cargado en LM Studio
