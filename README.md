# Satellite AD Agent — AI-агент детекции аномалий в телеметрии спутников

LLM-агент (ReAct + LangGraph) для автоматизированного анализа телеметрии спутников. Оператор взаимодействует через чат-интерфейс на естественном языке — задаёт вопросы, получает сводки и визуализации. Агент самостоятельно выбирает инструменты детекции: spike detection (MAD), trend shift detection (CUSUM), range check, ML-аномалии (PyOD) и кросс-канальную корреляцию.

## Возможности

- **Чат-интерфейс** на Svelte 5 с потоковым стримингом (SSE), Markdown/KaTeX/изображения
- **6 инструментов анализа**: `analyze`, `compare_channels`, `visualize`, `list_segments`, `generate_daily_report`, `get_anomalous_hours`
- **4 метода детекции**: MAD-spikes, CUSUM-shifts, range check, PyOD ML-детекторы
- **Кросс-канальный анализ** с корреляцией Пирсона
- **Автоматические ежедневные отчёты** с композитным score и ранжированием по severity
- **Контейнеризация**: Docker Compose (агент + nginx)

## Архитектура

```
┌──────────────┐   SSE stream     ┌────────────────────────────────────┐
│  Svelte 5     │ ◄──────────────► │  LangGraph Agent Server            │
│  (nginx:80)   │   POST /api/runs  │  (Python 3.12, port 2024)          │
│               │                  │  ReAct Loop: call_model → run_tools │
└──────────────┘                  └────────────────────────────────────┘
```

## Быстрый старт

```bash
cp .env.template .env
# Отредактируйте .env: установите OPENAI_API_KEY

docker compose up --build
```

Откройте `http://localhost`.

## Локальная разработка

**Требования:** Python 3.12+, [uv](https://docs.astral.sh/uv/), [bun](https://bun.sh/).

```bash
# Бэкенд
cp .env.template .env
uv sync
uv run langgraph dev --port 2024 --host 0.0.0.0

# Фронтенд (отдельный терминал)
cd frontend
bun install
bun run dev  # :5173, прокси /api → localhost:2024
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `OPENAI_API_KEY` | `sk-...` | API-ключ LLM-провайдера |
| `OPENAI_MODEL` | `google/gemma-4-e2b` | Модель |
| `OPENAI_BASE_URL` | — | Кастомный base URL (Ollama и т.п.) |
| `SEGMENTS_DATA` | `segments-unlabeled.csv` | Файл данных |
| `LANGCHAIN_TRACING_V2` | — | Трассировка LangSmith |
| `LANGCHAIN_API_KEY` | — | Ключ LangSmith |

## Инструменты агента

| Инструмент | Назначение |
|---|---|
| `list_segments` | Список доступных каналов и временных окон |
| `analyze` | Ядро детекции: MAD-спайки, CUSUM-сдвиги, range check, PyOD |
| `compare_channels` | Кросс-канальная корреляция Пирсона |
| `visualize` | Построение графика временного ряда (base64 PNG) |
| `generate_daily_report` | Сканирование всех каналов за дату |
| `get_anomalous_hours` | Детализация аномальных окон |

## Структура проекта

```
├── agent/           # Python-бэкенд: LangGraph агент, инструменты, модели
├── frontend/        # Svelte 5 SPA
├── data/            # Датасет OPS-SAT-AD (~300k точек)
├── tests/           # Pytest-тесты
├── docs/            # Документация
├── docker-compose.yml
├── Dockerfile.agent
└── pyproject.toml
```

## Тестирование

```bash
uv run pytest           # Python-тесты
cd frontend && bun test # JS-тесты
```

## Технологии

**Бэкенд:** Python 3.12, LangGraph, LangChain, FastAPI, NumPy/SciPy/statsmodels, PyOD, Matplotlib, Pydantic

**Фронтенд:** Svelte 5, Vite, TypeScript, Tailwind CSS 4, @langchain/svelte

**Инфраструктура:** Docker Compose, uv, bun

## Источник данных

[OPS-SAT-AD](https://github.com/ESA-ADLab/OPS-SAT-AD) — открытый набор данных Европейского космического агентства (ESA): ~300 000 точек телеметрии с бинарной разметкой аномалий.

## Лицензия

MIT
