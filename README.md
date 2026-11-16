## Структура проекта
.
├── app.py                  # FastAPI-сервер с веб-интерфейсом
├── solution.py             # Точка входа для автоматической оценки
├── assistant.py            # Логика формирования ответов
├── indexer.py              # Построение и поиск по индексу
├── loader.py               # Загрузка документов
├── config.py               # Конфигурация из переменных окружения
├── requirements.txt        # Зависимости Python
├── Dockerfile              # Образ Docker
├── compose.yaml            # Docker Compose конфигурация
├── .env.example            # Пример переменных окружения
├── .dockerignore           # Исключения для Docker
├── README.md               # Документация
├── templates/
│   └── index.html          # HTML-шаблон чата
├── static/
│   ├── css/
│   │   └── style.css       # Стили интерфейса
│   └── js/
│       └── app.js          # Логика клиентской части
└── data/
    ├── knowledge-base/     # База знаний (не в репозиторий)
    └── questions.csv       # Вопросы для оценки (не в репозиторий)

## Возможности

- **Гибридный поиск**: векторный (FAISS) + лексический (BM25) с реранкингом
- **Контроль достоверности**: отказ от ответа при недостатке информации, выявление ошибок в вопросах
- **Веб-интерфейс**: чат с отображением источников и фрагментов документов
- **Автоматическая оценка**: генерация ответов для LLM-судьи через solution.py

### Компоненты

- **`solution.py`** — точка входа для автоматической оценки на платформе хакатона. Читает вопросы из `questions.csv`, генерирует ответы, записывает в `submission.csv`
- **`app.py`** — FastAPI-сервер с веб-интерфейсом чата
- **`assistant.py`** — логика формирования ответов с системным промптом
- **`indexer.py`** — построение и поиск по индексу (FAISS + BM25 + RRF + реранкер)
- **`loader.py`** — загрузка документов из PDF, DOCX, HTML, TXT
- **`config.py`** — конфигурация из переменных окружения

## Запуск через Docker

```bash
# Сборка и запуск
docker-compose up --build

# Открыть в браузере
# http://localhost:8000
# http://127.0.0.1:8000
```

<img width="990" height="597" alt="image" src="https://github.com/user-attachments/assets/e4a145d1-e50a-4c2e-b167-08abb949bdf7" />
<img width="756" height="294" alt="image" src="https://github.com/user-attachments/assets/00c4bf0f-24d8-4457-8096-7846d3165f90" />
<img width="1831" height="1016" alt="image" src="https://github.com/user-attachments/assets/98db4a1e-9e22-4307-8e12-2737b5c81730" />

## Локальный запуск
```
# Установка зависимостей
pip install -r requirements.txt

# Создание виртуального окружения (опционально)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate.bat     # Windows

# Запуск веб-интерфейса
python app.py

# Запуск автоматической оценки
python solution.py
Переменные окружения вносятся в .env на основе .env.example:
```

LLM_API_KEY --- API-ключ для доступа к LLM (EMPTY, подставляется из переменных окружения организаторами хакатона или просто локально)  
LLM_BASE_URL --- URL OpenAI-совместимого прокси (http://localhost:8000/v1)  
LLM_MODEL --- Идентификатор генеративной модели (deepseek-v4.1-flash)  
EMB_MODEL --- Модель для эмбеддингов (BAAI/bge-m3)  
RERANKER_MODEL --- Модель для реранкинга (Qwen3 Reranker 8B)  
RERANKER_TOP_N --- Количество документов после реранкинга (5)  
DATA_DIR --- Путь к каталогу с данными (data)  
KB_PATH --- Путь к базе знаний (data/knowledge-base)  
TEMPERATURE --- Температура генерации (0.0)  
MAX_TOKENS --- Максимальное количество токенов в ответе (2000)  
MAX_WORKERS --- Количество параллельных потоков (4)  
TOP_K --- Количество документов для поиска (15)  
CHUNK_SIZE --- Размер чанка при разбиении документов (800)  
CHUNK_OVERLAP --- Перекрытие между чанками (100)  

## Проверка основного сценария
```
docker-compose up --build
```
Откройте http://localhost:8000 в браузере.  
Введите вопрос: "Какие документы нужно проверить перед заключением договора?"  
Убедитесь, что бот ответил со ссылками на источники  
Проверьте панель "Источники" — должны отображаться найденные документы  
Задайте вопрос с несуществующей статьёй: "Что говорит статья 999.1 ГК РФ?"  
Бот должен указать на ошибку в вопросе

## Зависимости
Основные зависимости (полный список в requirements.txt):  
- FastAPI — веб-фреймворк для API  
- OpenAI — клиент для работы с LLM  
- FAISS — векторный поиск  
- rank-bm25 — лексический поиск  
- langchain-text-splitters — разбиение документов на чанки  
- pypdf — чтение PDF  
- python-docx — чтение DOCX  
- beautifulsoup4 — парсинг HTML  

## Технологии
Язык: Python 3.11  
Веб-фреймворк: FastAPI + Uvicorn  
Векторная база: FAISS  
LLM: DeepSeek V4.1 Flash (через OpenAI-совместимый API)  
Эмбеддинги: BAAI/bge-m3  
Реранкер: Qwen3 Reranker 8B  

## Лицензия
Проект создан для хакатона Hack&Change 2026 по заказу ПСБ.
