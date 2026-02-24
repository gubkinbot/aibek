# API — Компрессорные станции

Модуль мониторинга и управления компрессорными станциями через OPC UA. Все эндпоинты начинаются с `/api/modules/compressor`.

## Станции

### Список станций

```http
GET /api/modules/compressor/stations
Authorization: Bearer <token>
```

**Permission:** `compressor.view`

**Ответ:**
```json
[
  {
    "id": "550e8400-...",
    "name": "КС Ахангарон",
    "code": "ahangaron",
    "opc_url": "opc.tcp://10.231.241.122:49320",
    "opc_security_policy": "Basic128Rsa15",
    "opc_security_mode": "Sign",
    "opc_cert_path": "/app/certificates/ahangaron/cert.der",
    "opc_key_path": "/app/certificates/ahangaron/key.pem",
    "polling_interval": 300,
    "realtime_interval": 1,
    "is_active": true,
    "description": "Ахангаронская КС",
    "tags_count": 42,
    "created_at": "2026-02-20T10:00:00Z",
    "updated_at": "2026-02-23T15:30:00Z"
  }
]
```

### Создание станции

```http
POST /api/modules/compressor/stations
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "КС Ахангарон",
  "code": "ahangaron",
  "opc_url": "opc.tcp://10.231.241.122:49320",
  "opc_security_policy": "Basic128Rsa15",
  "opc_security_mode": "Sign",
  "polling_interval": 300,
  "realtime_interval": 1,
  "is_active": true,
  "description": "Ахангаронская компрессорная станция"
}
```

**Permission:** `compressor.admin`

::: info Код станции
`code` — slug в формате `^[a-z0-9_-]+$`, используется в URL и Redis ключах. Уникален, не может быть изменён после создания.
:::

### Статус подключения

```http
GET /api/modules/compressor/stations/{code}/status
```

**Permission:** `compressor.view`

Возвращает текущий статус OPC-подключения из Redis (`opc:status:{code}`):

```json
{
  "connected": false,
  "last_seen": "2026-02-23T17:54:47Z",
  "error": "TimeoutError",
  "tags_count": 1
}
```

### Генерация сертификата

```http
POST /api/modules/compressor/stations/{code}/generate-cert
```

**Permission:** `compressor.admin`

Генерирует самоподписанный OPC UA сертификат (RSA 2048):
- Сертификат в формате DER (для импорта в Kepware)
- Приватный ключ в формате PEM
- Срок действия: 10 лет
- SAN: `urn:utg:opcua:{code}`

```json
{
  "message": "Сертификат сгенерирован",
  "cert_path": "/app/certificates/ahangaron/cert.der",
  "key_path": "/app/certificates/ahangaron/key.pem"
}
```

### Скачивание сертификата

```http
GET /api/modules/compressor/stations/{code}/download-cert
```

**Permission:** `compressor.admin`

Возвращает файл `{code}_opc_cert.der` для импорта в OPC-сервер (Kepware).

---

## Теги

### Список тегов станции

```http
GET /api/modules/compressor/stations/{code}/tags
```

**Permission:** `compressor.view`

### Создание тега

```http
POST /api/modules/compressor/stations/{code}/tags
Content-Type: application/json

{
  "opc_path": "Channel1.Device1.Temperature",
  "name": "Температура на входе",
  "unit": "°C",
  "data_type": "Float",
  "category": "Температура",
  "sort_order": 1,
  "valid_min": -40.0,
  "valid_max": 200.0,
  "stale_timeout": 300
}
```

**Permission:** `compressor.manage`

### Массовое создание тегов

```http
POST /api/modules/compressor/stations/{code}/tags/bulk
Content-Type: application/json

{
  "tags": [
    {"opc_path": "Ch1.Dev1.Temp", "name": "Температура", "unit": "°C", "category": "Температура"},
    {"opc_path": "Ch1.Dev1.Press", "name": "Давление", "unit": "bar", "category": "Давление"}
  ]
}
```

### Импорт тегов из Excel

```http
POST /api/modules/compressor/stations/{code}/tags/import-excel
Content-Type: multipart/form-data

file: tags.xlsx
```

**Permission:** `compressor.manage`

**Формат Excel:**
- Колонки: `opc_path`, `name`, `unit`, `data_type`, `category`, `sort_order`, `valid_min`, `valid_max`, `stale_timeout`
- Обязательные: `opc_path`, `name`
- Строка 1 — заголовки, строка 2 — описания (пропускается), данные с строки 3

**Ответ:**
```json
{
  "created": 42,
  "skipped": 3,
  "imported": 0,
  "errors": ["Row 15: duplicate opc_path 'Ch1.Dev1.Temp'"]
}
```

### Скачать шаблон тегов

```http
GET /api/modules/compressor/tags/template-excel
```

Возвращает `.xlsx` файл с заголовками, описаниями и 5 примерами данных.

---

## Вычисляемые теги

### Создание

```http
POST /api/modules/compressor/stations/{code}/computed-tags
Content-Type: application/json

{
  "name": "Статус ГПА-1",
  "compute_type": "status_map",
  "category": "Статус",
  "config": {
    "source_tags": ["uuid-1", "uuid-2", "uuid-3"],
    "rules": [
      {"when": {"uuid-1": 0, "uuid-2": 0, "uuid-3": 1}, "status": "В работе", "value": 1}
    ],
    "default": {"status": "Остановлен", "value": 0}
  }
}
```

**Типы:** `status_map` (маппинг бинарных тегов в статус), `formula` (арифметика из тегов).

---

## Данные

### Realtime snapshot

```http
GET /api/modules/compressor/stations/{code}/realtime
```

Возвращает последний snapshot из Redis (`opc:snapshot:{code}`):

```json
{
  "station": "ahangaron",
  "timestamp": "2026-02-23T15:30:00Z",
  "connected": true,
  "tags": {
    "tag-uuid-1": {
      "value": 42.5,
      "quality": "good",
      "name": "Температура на входе",
      "unit": "°C",
      "category": "Температура"
    }
  },
  "computed": {
    "ct-uuid-1": {
      "value": 1,
      "status": "В работе",
      "name": "Статус ГПА-1",
      "category": "Статус"
    }
  }
}
```

### История

```http
GET /api/modules/compressor/stations/{code}/history?tag_ids=uuid1,uuid2&from=2026-02-22T00:00:00Z&to=2026-02-23T00:00:00Z&interval=1h
```

**Query params:**

| Параметр | Описание |
|----------|----------|
| `tag_ids` | UUID тегов через запятую |
| `from` | Начало периода (ISO 8601) |
| `to` | Конец периода (ISO 8601) |
| `interval` | Интервал агрегации: `1m`, `5m`, `15m`, `1h`, `1d` |

Использует TimescaleDB `time_bucket()` для агрегации (avg, min, max).

### Импорт истории из Excel

```http
POST /api/modules/compressor/stations/{code}/history/import-excel
Content-Type: multipart/form-data

file: history.xlsx
```

**Формат Excel:** колонки `datetime`, `opc_path`, `value`, `health`.

---

## Аварии

### Правила аварий

```http
POST /api/modules/compressor/stations/{code}/alarm-rules
Content-Type: application/json

{
  "tag_id": "uuid-tag",
  "name": "Высокая температура",
  "condition": "gt",
  "threshold": 90.0,
  "severity": "critical",
  "is_active": true
}
```

**Условия:** `gt` (>), `lt` (<), `gte` (>=), `lte` (<=).

**Важность:** `info`, `warning`, `critical`.

### Журнал аварий

```http
GET /api/modules/compressor/stations/{code}/alarms?page=1&per_page=20&severity=critical
```

**Ответ (пагинация):**
```json
{
  "items": [
    {
      "time": "2026-02-23T15:30:00Z",
      "rule_id": "uuid-rule",
      "tag_id": "uuid-tag",
      "station_id": "uuid-station",
      "value": 95.2,
      "threshold": 90.0,
      "severity": "critical",
      "message": "Высокая температура: Температура на входе = 95.20 (gt 90.0)",
      "acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

### Квитирование аварии

```http
POST /api/modules/compressor/alarms/acknowledge
Content-Type: application/json

{
  "time": "2026-02-23T15:30:00Z",
  "station_id": "uuid-station"
}
```

**Permission:** `compressor.edit`

---

## Аномалии

### Правила аномалий

```http
POST /api/modules/compressor/stations/{code}/anomaly-rules
Content-Type: application/json

{
  "tag_id": "uuid-tag",
  "name": "Тренд роста температуры",
  "detector_type": "trend",
  "severity": "warning",
  "config": {
    "window_minutes": 15,
    "slope_threshold": 0.5,
    "min_r_squared": 0.7
  }
}
```

**Типы детекторов:**

| Тип | Описание | Ключевые параметры |
|-----|----------|-------------------|
| `trend` | Линейная регрессия на окне | `window_minutes`, `slope_threshold`, `min_r_squared` |
| `volatility` | Рост стандартного отклонения | `window_minutes`, `baseline_minutes`, `std_multiplier` |
| `stabilization` | Падение колебаний (залипание) | `window_minutes`, `baseline_minutes`, `std_ratio_threshold` |
| `spike` | Z-score выброс | `window_minutes`, `sigma_threshold` |

### Журнал аномалий

```http
GET /api/modules/compressor/stations/{code}/anomalies?page=1&per_page=20
```

Формат аналогичен журналу аварий, с дополнительными полями `detector_type` и `details` (JSON).

---

## WebSocket

```
WS /api/modules/compressor/ws/{station_code}?token=JWT
```

Подключение через WebSocket для получения realtime данных.

### Аутентификация

JWT передаётся в query parameter `token`. При невалидном токене — закрытие с кодом `4001`. При несуществующей станции — код `4004`.

### Формат сообщений

**Realtime данные:**
```json
{
  "type": "realtime",
  "station": "ahangaron",
  "timestamp": "2026-02-23T15:30:00Z",
  "connected": true,
  "tags": {
    "tag-uuid": {"value": 42.5, "quality": "good", "name": "Температура", "unit": "°C", "category": "Температура"}
  },
  "computed": {
    "ct-uuid": {"value": 1, "status": "В работе", "name": "Статус ГПА-1", "category": "Статус"}
  }
}
```

**Авария:**
```json
{
  "type": "alarm",
  "station": "ahangaron",
  "severity": "critical",
  "message": "Высокая температура: Температура = 95.20 (gt 90.0)",
  "tag_id": "uuid",
  "value": 95.2,
  "threshold": 90.0,
  "time": "2026-02-23T15:30:00Z"
}
```

**Аномалия:**
```json
{
  "type": "anomaly",
  "station": "ahangaron",
  "detector_type": "trend",
  "severity": "warning",
  "message": "Обнаружен тренд роста...",
  "tag_id": "uuid",
  "time": "2026-02-23T15:30:00Z"
}
```

**Статус:**
```json
{
  "type": "status",
  "station": "ahangaron",
  "connected": true,
  "last_seen": "2026-02-23T15:30:00Z"
}
```

### Nginx конфигурация

WebSocket требует отдельный `location` в nginx.conf с upgrade заголовками:

```nginx
location /api/modules/compressor/ws/ {
    proxy_pass $backend_upstream$request_uri;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

---

## Качество данных (quality)

Коллектор присваивает каждому значению качество:

| Quality | Описание | Условие |
|---------|----------|---------|
| `good` | Нормальное значение | Прошло все проверки |
| `bad` | Ошибка чтения | Значение `null` из OPC |
| `outlier` | Вне допустимого диапазона | `value < valid_min` или `value > valid_max` |
| `stale` | Залипание (нет изменений) | Значение не менялось > `stale_timeout` секунд |
