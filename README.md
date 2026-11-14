# nuget-dep-graph

Инструмент визуализации графа зависимостей для менеджера пакетов NuGet (.NET).

## Общее описание

Утилита командной строки, которая по имени пакета и его версии строит
транзитивный граф зависимостей на основе метаданных `.nuspec` из
репозитория NuGet, поддерживает фильтрацию пакетов, поиск обратных
зависимостей и визуализацию графа (PlantUML / PNG).

Готовые менеджеры пакетов и библиотеки получения зависимостей
(`nuget`, `dotnet`, `NuGet.Client` и т.п.) не используются —
только стандартная библиотека Python (`argparse`, `urllib.request`,
`xml.etree.ElementTree`, `json`, `zipfile`).

## Описание всех функций и настроек

### CLI-параметры

- `--package` — имя анализируемого пакета (обязательный);
- `--source` — URL репозитория NuGet (service index) или путь к
  тестовому репозиторию (обязательный);
- `--mode` — режим работы: `online` (по умолчанию) или `offline`;
- `--version` — версия пакета. Для онлайн-режима обязательна явная
  версия (значение `latest` отклоняется);
- `--output` — имя файла с изображением графа (`graph.png`);
- `--filter` — подстрока для фильтрации пакетов.

### Модули

- `src/main.py` — точка входа, разбор аргументов, валидация,
  вывод отладочной информации и прямых зависимостей.
- `src/nuget_api.py` — минимальный клиент NuGet v3 API:
  - `fetch_url(url)` — HTTP GET, кидает `RuntimeError` при ошибке;
  - `discover_base_address(url)` — находит `PackageBaseAddress/3.0.0`
    в service index;
  - `build_nuspec_url(base, package, version)` — собирает URL `.nuspec`;
  - `parse_direct_dependencies(nuspec_xml)` — извлекает прямые
    зависимости из `.nuspec`, учитывая пространства имён;
  - `get_direct_dependencies(pkg, ver, service_index)` — полный
    конвейер: discovery → загрузка `.nuspec` → парсинг.

## Сборка, запуск, тесты

### Запуск

```cmd
run.bat --package Microsoft.Extensions.Logging ^
        --source https://api.nuget.org/v3/index.json ^
        --version 8.0.0
