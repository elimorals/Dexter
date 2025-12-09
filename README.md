# Dexter 🤖

Dexter es un agente autónomo de investigación financiera que piensa, planifica y aprende mientras trabaja. Realiza análisis utilizando planificación de tareas, auto-reflexión y datos de mercado en tiempo real. Piensa en Claude Code, pero construido específicamente para investigación financiera.

<img width="979" height="651" alt="Screenshot 2025-10-14 at 6 12 35 PM" src="https://github.com/user-attachments/assets/5a2859d4-53cf-4638-998a-15cef3c98038" />

## Resumen

Dexter toma preguntas financieras complejas y las convierte en planes de investigación claros y paso a paso. Ejecuta esas tareas utilizando datos de mercado en vivo, verifica su propio trabajo y refina los resultados hasta tener una respuesta confiable respaldada por datos.

**Capacidades Clave:**
- **Planificación Inteligente de Tareas**: Descompone automáticamente consultas complejas en pasos de investigación estructurados
- **Ejecución Autónoma**: Selecciona y ejecuta las herramientas correctas para recopilar datos financieros
- **Auto-Validación**: Verifica su propio trabajo e itera hasta que las tareas estén completas
- **Datos Financieros en Tiempo Real**: Acceso a estados de resultados, balances y estados de flujo de efectivo
- **Características de Seguridad**: Detección de bucles incorporada y límites de pasos para prevenir ejecución descontrolada

[![Twitter Follow](https://img.shields.io/twitter/follow/virattt?style=social)](https://twitter.com/virattt)

<img width="996" height="639" alt="Screenshot 2025-11-22 at 1 45 07 PM" src="https://github.com/user-attachments/assets/8915fd70-82c9-4775-bdf9-78d5baf28a8a" />

## Arquitectura del Sistema

Dexter utiliza una arquitectura multi-agente con componentes especializados que trabajan en conjunto para realizar investigación financiera completa. El sistema está diseñado con dos implementaciones: una en **Python** y otra en **TypeScript**, ambas compartiendo la misma filosofía arquitectónica pero adaptadas a sus respectivos ecosistemas.

### Componentes Principales

#### 1. **Agente de Planificación (Task Planner)**
- **Función**: Analiza la consulta del usuario y la descompone en una lista estructurada de tareas
- **Implementación**: 
  - Python: `plan_tasks()` en `agent.py`
  - TypeScript: `TaskPlanner.planTasks()` en `task-planner.ts`
- **Proceso**: 
  - Recibe la consulta del usuario
  - Analiza las herramientas disponibles (16 herramientas financieras + búsqueda)
  - Genera tareas específicas, atómicas y secuenciales
  - Retorna una lista de tareas con IDs y descripciones

#### 2. **Agente de Ejecución (Task Executor)**
- **Función**: Ejecuta las tareas planificadas utilizando herramientas financieras
- **Implementación**:
  - Python: Loop principal en `agent.run()` con `ask_for_actions()` y `_execute_tool()`
  - TypeScript: `TaskExecutor.executeTasks()` en `task-executor.ts`
- **Proceso**:
  - Para cada tarea, genera subtareas específicas (solo en TypeScript)
  - Solicita al LLM qué herramienta usar y con qué parámetros
  - Optimiza los argumentos de las herramientas antes de ejecutarlas
  - Ejecuta las herramientas y guarda los resultados
  - Valida si la tarea está completa antes de continuar

#### 3. **Agente de Validación (Validation Agent)**
- **Función**: Verifica si las tareas están completas y si el objetivo principal se ha alcanzado
- **Implementación**:
  - Python: `ask_if_done()` y `is_goal_achieved()` en `agent.py`
  - TypeScript: Integrado en `TaskExecutor`
- **Proceso**:
  - Evalúa si una tarea individual está completa
  - Evalúa si el objetivo general de la consulta se ha cumplido
  - Utiliza los resultados de las herramientas para tomar decisiones

#### 4. **Generador de Respuestas (Answer Generator)**
- **Función**: Sintetiza todos los hallazgos en una respuesta comprensiva
- **Implementación**:
  - Python: `_generate_answer()` en `agent.py`
  - TypeScript: `AnswerGenerator.generateAnswer()` en `answer-generator.ts`
- **Proceso**:
  - Selecciona contextos relevantes de los archivos guardados
  - Carga los contextos seleccionados
  - Genera una respuesta completa basada en los datos recopilados
  - Transmite la respuesta en tiempo real (streaming)

### Flujo de Ejecución Completo

```
1. Usuario hace una consulta
   ↓
2. Agente de Planificación descompone la consulta en tareas
   ↓
3. Para cada tarea:
   a. Agente de Ejecución pregunta al LLM qué hacer
   b. LLM selecciona una herramienta y parámetros
   c. Se optimizan los argumentos de la herramienta
   d. Se ejecuta la herramienta
   e. Se guarda el resultado en el sistema de archivos (ContextManager)
   f. Se genera un resumen del resultado
   g. Agente de Validación verifica si la tarea está completa
   ↓
4. Agente de Validación verifica si el objetivo general se alcanzó
   ↓
5. Generador de Respuestas:
   a. Selecciona contextos relevantes usando LLM
   b. Carga los contextos seleccionados
   c. Genera respuesta final con streaming
```

## Integración de Modelos LLM

Dexter utiliza **LangChain** como capa de abstracción para interactuar con múltiples proveedores de modelos de lenguaje. El sistema soporta tres proveedores principales:

### Proveedores Soportados

1. **OpenAI** (por defecto)
   - Modelos: `gpt-4.1`, `gpt-4`, `gpt-3.5-turbo`, etc.
   - Clave API: `OPENAI_API_KEY`
   - Implementación: `ChatOpenAI` de LangChain

2. **Anthropic**
   - Modelos: `claude-sonnet-4.5`, `claude-3-opus`, etc.
   - Clave API: `ANTHROPIC_API_KEY`
   - Implementación: `ChatAnthropic` de LangChain

3. **Google Gemini**
   - Modelos: `gemini-3`, `gemini-pro`, etc.
   - Clave API: `GOOGLE_API_KEY`
   - Implementación: `ChatGoogleGenerativeAI` de LangChain

### Configuración de LLM

**Python** (`src/dexter/model.py`):
```python
def get_chat_model(model_name: str, temperature: float = 0, streaming: bool = False):
    if model_name.startswith("claude-"):
        return ChatAnthropic(model=model_name, ...)
    elif model_name.startswith("gemini-"):
        return ChatGoogleGenerativeAI(model=model_name, ...)
    else:
        return ChatOpenAI(model=model_name, ...)
```

**TypeScript** (`dexter-ts/src/model/llm.ts`):
```typescript
export function getChatModel(modelName: string, temperature: number = 0, streaming: boolean = false) {
  const prefix = Object.keys(MODEL_PROVIDERS).find(p => modelName.startsWith(p));
  const factory = prefix ? MODEL_PROVIDERS[prefix] : DEFAULT_PROVIDER;
  return factory(modelName, { temperature, streaming });
}
```

### Nota sobre Endpoints Personalizados

**Dexter NO utiliza el endpoint de LM Studio** (`http://localhost:1234/v1/chat/completions`). El sistema está diseñado para usar los endpoints oficiales de los proveedores a través de LangChain. Si deseas usar un modelo local como LM Studio, necesitarías:

1. Configurar LangChain para usar un endpoint personalizado
2. Modificar `get_chat_model()` para aceptar un `base_url` personalizado
3. Configurar las variables de entorno apropiadas

Actualmente, el sistema utiliza las APIs oficiales de OpenAI, Anthropic y Google.

## Sistema de Herramientas Financieras

Dexter cuenta con **17 herramientas** especializadas en investigación financiera, todas integradas con la API de **Financial Datasets** (`https://api.financialdatasets.ai`).

### Categorías de Herramientas

#### 1. **Estados Financieros Fundamentales** (4 herramientas)
- `get_income_statements`: Estados de resultados (ingresos, gastos, ganancias)
- `get_balance_sheets`: Balances (activos, pasivos, patrimonio)
- `get_cash_flow_statements`: Estados de flujo de efectivo
- `get_all_financial_statements`: Todos los estados financieros combinados

#### 2. **Documentos Regulatorios (Filings)** (4 herramientas)
- `get_filings`: Obtener todos los documentos regulatorios
- `get_10K_filing_items`: Elementos específicos de formularios 10-K (informes anuales)
- `get_10Q_filing_items`: Elementos específicos de formularios 10-Q (informes trimestrales)
- `get_8K_filing_items`: Elementos específicos de formularios 8-K (eventos actuales)

#### 3. **Métricas Financieras** (2 herramientas)
- `get_financial_metrics_snapshot`: Instantánea de métricas clave
- `get_financial_metrics`: Métricas financieras históricas

#### 4. **Precios de Acciones** (2 herramientas)
- `get_price_snapshot`: Precio actual de una acción
- `get_prices`: Precios históricos de acciones

#### 5. **Noticias y Análisis** (2 herramientas)
- `get_news`: Noticias financieras relacionadas con una empresa
- `get_analyst_estimates`: Estimaciones de analistas

#### 6. **Segmentación de Ingresos** (1 herramienta)
- `get_segmented_revenues`: Ingresos por segmento de negocio

#### 7. **Búsqueda** (1 herramienta)
- `search_google_news`: Búsqueda de noticias en Google

### Integración con Financial Datasets API

Todas las herramientas financieras utilizan la misma función base para llamar a la API:

**Python** (`src/dexter/tools/finance/api.py`):
```python
def call_api(endpoint: str, params: dict) -> dict:
    base_url = "https://api.financialdatasets.ai"
    url = f"{base_url}{endpoint}"
    headers = {"x-api-key": financial_datasets_api_key}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()
```

**TypeScript** (`dexter-ts/src/tools/finance/api.ts`):
```typescript
export async function callApi(endpoint: string, params: Record<string, ...>): Promise<...> {
  const url = new URL(`${BASE_URL}${endpoint}`);
  // ... añade parámetros
  const response = await fetch(url.toString(), {
    headers: { 'x-api-key': FINANCIAL_DATASETS_API_KEY || '' }
  });
  return response.json();
}
```

## Sistema de Gestión de Contexto

Dexter implementa un sistema sofisticado de gestión de contexto que guarda los resultados de las herramientas en el sistema de archivos para eficiencia de memoria.

### ContextManager

El `ContextManager` es responsable de:

1. **Guardar Contextos**: Cuando una herramienta se ejecuta, su resultado se guarda en un archivo JSON
2. **Generar Resúmenes**: Usa el LLM para generar resúmenes breves de cada resultado
3. **Seleccionar Contextos Relevantes**: Al generar la respuesta final, selecciona solo los contextos relevantes usando el LLM
4. **Cargar Contextos**: Carga solo los contextos seleccionados cuando se necesita generar la respuesta

### Estructura de Archivos

Los contextos se guardan en `.dexter/context/` con nombres descriptivos:
- Formato: `{TICKER}_{tool_name}_{hash}.json`
- Ejemplo: `AAPL_get_income_statements_a1b2c3d4e5f6.json`

### Flujo de Contexto

```
Ejecución de Herramienta
   ↓
Resultado guardado en archivo JSON
   ↓
Generación de resumen con LLM
   ↓
Puntero guardado en memoria (ligero)
   ↓
[Durante generación de respuesta]
   ↓
LLM selecciona contextos relevantes
   ↓
Solo se cargan los archivos seleccionados
   ↓
Respuesta generada con contextos cargados
```

**Python** (`src/dexter/utils/context.py`):
- `save_context()`: Guarda resultado y genera resumen
- `select_relevant_contexts()`: Selecciona contextos usando LLM
- `load_contexts()`: Carga archivos seleccionados

**TypeScript** (`dexter-ts/src/utils/context.ts`):
- Misma funcionalidad adaptada a TypeScript

## Estructura del Proyecto

El proyecto contiene dos implementaciones completas:

### Versión Python

```
src/dexter/
├── agent.py              # Lógica principal de orquestación del agente
├── model.py              # Interfaz LLM (multi-proveedor)
├── prompts.py            # Prompts del sistema para cada componente
├── schemas.py            # Modelos Pydantic para validación
├── cli.py                # Punto de entrada CLI
├── tools/                # Herramientas disponibles
│   ├── __init__.py       # Registro de todas las herramientas
│   ├── finance/          # 16 herramientas financieras
│   │   ├── api.py        # Cliente base para Financial Datasets API
│   │   ├── fundamentals.py
│   │   ├── filings.py
│   │   ├── metrics.py
│   │   ├── prices.py
│   │   ├── news.py
│   │   ├── estimates.py
│   │   └── segments.py
│   └── search/           # Herramientas de búsqueda
│       └── google.py
└── utils/                # Utilidades
    ├── context.py        # Gestión de contexto (offloading)
    ├── config.py         # Persistencia de configuración
    ├── env.py            # Gestión de API keys
    ├── logger.py         # Sistema de logging
    ├── ui.py             # Interfaz de usuario
    └── model_selector.py # Selector de modelos
```

### Versión TypeScript

```
dexter-ts/src/
├── agent/                # Componentes del agente
│   ├── agent.ts          # Orquestación principal
│   ├── task-planner.ts   # Planificación de tareas y subtareas
│   ├── task-executor.ts  # Ejecución de tareas con loops agenticos
│   ├── answer-generator.ts # Generación de respuestas
│   ├── prompts.ts        # Prompts del sistema
│   └── schemas.ts        # Esquemas Zod
├── components/           # Componentes React/Ink para UI
│   ├── AnswerBox.tsx     # Visualización de respuestas con streaming
│   ├── Input.tsx         # Entrada de usuario
│   ├── Intro.tsx         # Pantalla de bienvenida
│   ├── ModelSelector.tsx # Selector de modelos
│   ├── TaskProgress.tsx  # Progreso de tareas
│   └── TaskList.tsx      # Lista de tareas
├── model/
│   └── llm.ts           # Interfaz LLM (multi-proveedor)
├── tools/               # Herramientas (misma estructura que Python)
├── utils/
│   ├── context.ts       # Gestión de contexto
│   ├── config.ts        # Configuración persistente
│   └── env.ts           # Gestión de API keys
├── hooks/
│   └── useQueryQueue.ts # Cola de consultas
├── cli.tsx              # Componente CLI principal
└── index.tsx            # Punto de entrada
```

## Prerrequisitos

### Versión Python
- Python 3.10 o superior
- [uv](https://github.com/astral-sh/uv) gestor de paquetes
- Clave API de OpenAI (obtener [aquí](https://platform.openai.com/api-keys))
- Clave API de Financial Datasets (obtener [aquí](https://financialdatasets.ai))

### Versión TypeScript
- [Bun](https://bun.com) runtime (v1.0 o superior)
- Clave API de OpenAI (obtener [aquí](https://platform.openai.com/api-keys))
- Clave API de Financial Datasets (obtener [aquí](https://financialdatasets.ai))

#### Instalación de Bun

Si no tienes Bun instalado:

**macOS/Linux:**
```bash
curl -fsSL https://bun.com/install | bash
```

**Windows:**
```bash
powershell -c "irm bun.sh/install.ps1|iex"
```

Verifica la instalación:
```bash
bun --version
```

## Instalación

### Versión Python

1. Clona el repositorio:
```bash
git clone https://github.com/virattt/dexter.git
cd dexter
```

2. Instala las dependencias con uv:
```bash
uv sync
```

3. Configura las variables de entorno:
```bash
# Copia el archivo de ejemplo
cp env.example .env

# Edita .env y añade tus API keys
# OPENAI_API_KEY=tu-clave-openai
# ANTHROPIC_API_KEY=tu-clave-anthropic (opcional)
# GOOGLE_API_KEY=tu-clave-google (opcional)
# FINANCIAL_DATASETS_API_KEY=tu-clave-financial-datasets
```

### Versión TypeScript

1. Clona el repositorio:
```bash
git clone https://github.com/virattt/dexter.git
cd dexter/dexter-ts
```

2. Instala las dependencias con Bun:
```bash
bun install
```

3. Configura las variables de entorno:
```bash
# Copia el archivo de ejemplo desde el directorio padre
cp ../env.example .env

# Edita .env y añade tus API keys
# OPENAI_API_KEY=tu-clave-openai
# ANTHROPIC_API_KEY=tu-clave-anthropic (opcional)
# GOOGLE_API_KEY=tu-clave-google (opcional)
# FINANCIAL_DATASETS_API_KEY=tu-clave-financial-datasets
```

## Uso

### Versión Python

Ejecuta Dexter en modo interactivo:
```bash
uv run dexter-agent
```

### Versión TypeScript

Ejecuta Dexter en modo interactivo:
```bash
bun run start
```

O en modo desarrollo con watch:
```bash
bun run dev
```

### Cambiar Modelos

En ambas versiones, puedes cambiar el modelo escribiendo `/model` en la CLI. Esto te permitirá seleccionar entre:
- GPT 4.1 (OpenAI)
- Claude Sonnet 4.5 (Anthropic)
- Gemini 3 (Google)

## Ejemplos de Consultas

Prueba preguntarle a Dexter cosas como:
- "¿Cuál fue el crecimiento de ingresos de Apple en los últimos 4 trimestres?"
- "Compara los márgenes operativos de Microsoft y Google para 2023"
- "Analiza las tendencias de flujo de efectivo de Tesla durante el año pasado"
- "¿Cuál es la relación deuda-capital de Amazon basada en estados financieros recientes?"

Dexter automáticamente:
1. Descompone tu pregunta en tareas de investigación
2. Obtiene los datos financieros necesarios
3. Realiza cálculos y análisis
4. Proporciona una respuesta comprensiva y rica en datos

## Configuración Avanzada

### Configuración del Agente

**Python:**
```python
from dexter.agent import Agent

agent = Agent(
    max_steps=20,              # Límite global de seguridad
    max_steps_per_task=5,     # Límite de iteraciones por tarea
    model="gpt-4.1"           # Modelo LLM a usar
)
```

**TypeScript:**
```typescript
import { Agent } from './agent/agent.js';

const agent = new Agent({
  model: 'gpt-4.1',           // Modelo LLM a usar
  callbacks: {                // Callbacks para observar ejecución
    onUserQuery: (query) => console.log(query),
    onTasksPlanned: (tasks) => console.log(tasks),
    // ... más callbacks
  }
});
```

### Variables de Entorno Opcionales

```bash
# LangSmith (para tracing y debugging)
LANGSMITH_API_KEY=tu-clave-langsmith
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=dexter
LANGSMITH_TRACING=true
```

## Características de Seguridad

Dexter incluye varias características de seguridad para prevenir ejecución descontrolada:

1. **Límite Global de Pasos**: Previene loops infinitos con `max_steps`
2. **Límite por Tarea**: Cada tarea tiene un límite de iteraciones (`max_steps_per_task`)
3. **Detección de Bucles**: Detecta acciones repetitivas y aborta la ejecución
4. **Validación de Tareas**: Verifica si las tareas están completas antes de continuar
5. **Validación Meta**: Verifica si el objetivo general se ha alcanzado

## Diferencias entre Versiones

### Python
- Arquitectura más simple y directa
- Loop secuencial de tareas
- Validación en dos niveles (tarea y meta)
- Gestión de contexto integrada

### TypeScript
- Arquitectura híbrida con subtareas
- Ejecución paralela de tareas
- UI interactiva con React/Ink
- Cola de consultas para manejar múltiples preguntas
- Streaming de respuestas en tiempo real

## Cómo Contribuir

1. Haz fork del repositorio
2. Crea una rama de características
3. Realiza tus cambios
4. Haz push a la rama
5. Crea un Pull Request

**Importante**: Por favor mantén tus pull requests pequeños y enfocados. Esto facilitará la revisión y fusión.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.
