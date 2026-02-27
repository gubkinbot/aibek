# Фронтенд — Архитектура

Фронтенд построен на **Vue 3** с **Composition API**, использует **Tailwind CSS** для стилизации и **Pinia** для управления состоянием.

## Стек

| Технология | Назначение |
|-----------|------------|
| Vue 3 + Composition API | UI-фреймворк |
| Vite | Сборка и dev-сервер |
| Tailwind CSS | CSS-утилиты + dark mode |
| Vue Router | Маршрутизация + guards |
| Pinia | State management |
| Axios | HTTP-клиент |
| vue-i18n | Мультиязычность (ru/uz) |
| Chart.js | Графики мониторинга и исторических данных |
| WebSocket (native) | Realtime обновления от OPC-коллектора |

## Структура `src/`

```
src/
├── main.js           # Инициализация: Pinia, Router, i18n
├── App.vue           # Корневой компонент (Navbar + router-view)
├── style.css         # Tailwind + базовые стили
│
├── api/
│   └── index.js      # Axios инстанс с JWT и 401-обработкой
│
├── stores/           # Pinia сторы
│   ├── auth.js       # Аутентификация и permissions
│   ├── admin.js      # Админ-операции
│   ├── theme.js      # Тема (dark/light)
│   └── compressor.js # Компрессорный модуль (CRUD, realtime, WS)
│
├── composables/
│   ├── useCompressorWs.js  # WebSocket с auto-reconnect
│   └── useFullscreen.js    # Переключение полноэкранного режима
│
├── router/
│   └── index.js      # Маршруты и navigation guards
│
├── components/
│   ├── Navbar.vue    # Навигация, sidebar, тема, язык
│   ├── PulseOrb.vue     # Анимированная визуализация (дашборд)
│   ├── PulseControls.vue # Элементы управления для PulseOrb
│   └── AuthLayout.vue   # Layout для auth-страниц
│
├── views/            # Страницы
│   ├── Landing.vue
│   ├── Login.vue
│   ├── Register.vue
│   ├── VerifyEmail.vue
│   ├── ForgotPassword.vue
│   ├── Dashboard.vue
│   ├── Settings.vue
│   ├── admin/
│   │   ├── AdminUsers.vue
│   │   ├── AdminUserDetail.vue
│   │   ├── AdminAuditLogs.vue
│   │   ├── AdminSystem.vue
│   │   └── AdminCompressor.vue     # Настройки компрессорных станций
│   └── modules/
│       ├── CompressorHome.vue      # Мониторинг (realtime, аварии, аномалии, графики)
│       ├── CompressorSettings.vue  # Управление (теги, правила, диагностика, импорт)
│       ├── BalanceHome.vue
│       ├── WeatherHome.vue
│       ├── DigitalHome.vue
│       ├── AiChatHome.vue
│       └── ScadaHome.vue
│
├── i18n/
│   ├── index.js      # Настройка vue-i18n
│   ├── ru.js         # Русский
│   └── uz.js         # Узбекский
│
└── utils/
    └── date.js       # Форматирование дат
```

## Axios и аутентификация

`api/index.js` — настроенный Axios инстанс:

- **Базовый URL**: `/api` (через Nginx проксируется на бэкенд)
- **Request interceptor**: автоматически добавляет `Authorization: Bearer <token>` из `localStorage`
- **Response interceptor**: при `401` — очищает токен, сбрасывает стор, перенаправляет на `/login`

```js
// Использование
import api from '../api'

const { data } = await api.get('/auth/me')
const { data } = await api.post('/auth/login', { email, password })
```

::: info Обработка 401
При получении 401 происходит:
1. `auth.logout()` — очистка токена и данных пользователя
2. Проверка, требует ли текущая страница авторизацию
3. Если да — перенаправление на `/login`

Это предотвращает зацикливание: если пользователь на публичной странице, редиректа не будет.
:::

## Pinia сторы

### auth.js — Аутентификация

Центральный стор для управления сессией пользователя.

**Состояние:**
- `user` — объект пользователя (`null` если не авторизован)
- `token` — JWT токен (из `localStorage`)
- `loading` — флаг загрузки
- `initialized` — был ли выполнен первый fetch

**Computed:**
- `isAuthenticated` — есть ли токен
- `isAdmin` — есть ли permission из категории `users.*` (доступ к админ-панели)
- `isSuperAdmin` — `user.is_superadmin === true`
- `hasPermission(codename)` — проверяет наличие permission в массиве `user.permissions`

**Данные пользователя** (из `/auth/me`):
```json
{
  "id": "...",
  "email": "user@utg.uz",
  "full_name": "Иванов Иван",
  "is_superadmin": false,
  "permissions": ["compressor.access", "compressor.view", "compressor.edit", "users.view", "audit.view"],
  "module_access": {
    "compressor": "operator",
    "admin": "viewer"
  }
}
```

**Методы:**
- `init()` — загружает данные пользователя при первом переходе
- `login(email, password)` — вход + загрузка профиля
- `register(email, password, fullName)` — регистрация
- `verifyEmail(email, code)` — подтверждение email
- `logout()` — очистка сессии
- `fetchUser()` — загрузка `/auth/me`
- `forgotPassword(email)` / `resetPassword(...)` — сброс пароля
- `changePassword(...)` / `updateProfile(...)` — профиль

### admin.js — Админ-операции

Стор для всех CRUD-операций администрирования.

| Группа | Методы |
|--------|--------|
| Пользователи | `fetchUsers(params)`, `fetchUser(id)`, `createUser(data)`, `updateUser(id, data)`, `blockUser(id, reason)`, `unblockUser(id)`, `resetPassword(id)`, `deleteUser(id)` |
| Суперадмин | `toggleSuperadmin(userId)` |
| Уровни доступа | `fetchModuleLevels()`, `setModuleAccess(userId, module, level)`, `removeModuleAccess(userId, module)` |
| Аудит | `fetchAuditLogs(params)` |
| Система | `fetchSystemStatus()`, `fetchServerStats()`, `fetchDockerStats()` |

### compressor.js — Компрессорный модуль

Стор для работы с компрессорными станциями: CRUD станций, тегов, правил + realtime данные.

**Состояние:**
- `stations` — список станций
- `currentStation` — текущая станция
- `tags` / `computedTags` — теги станции
- `realtimeData` — snapshot от WebSocket
- `stationStatus` — диагностика (OPC connected/disconnected, ошибки)
- `alarmRules` / `anomalyRules` — правила
- `alarms` / `anomalies` — пагинированные журналы событий

**Основные методы (26 actions):**

| Группа | Методы |
|--------|--------|
| Станции | `fetchStations`, `fetchStation`, `createStation`, `updateStation`, `deleteStation`, `fetchStationStatus` |
| Сертификаты | `generateCert`, `downloadCert` |
| Теги | `fetchTags`, `createTag`, `updateTag`, `deleteTag`, `importTagsExcel`, `downloadTagsTemplate` |
| Вычисляемые | `fetchComputedTags`, `createComputedTag`, `updateComputedTag`, `deleteComputedTag` |
| Данные | `fetchRealtime`, `fetchHistory`, `importHistoryExcel`, `downloadHistoryTemplate` |
| Аварии | `fetchAlarmRules`, `createAlarmRule`, `updateAlarmRule`, `deleteAlarmRule`, `fetchAlarms`, `acknowledgeAlarm` |
| Аномалии | `fetchAnomalyRules`, `createAnomalyRule`, `updateAnomalyRule`, `deleteAnomalyRule`, `fetchAnomalies`, `acknowledgeAnomaly` |
| WebSocket | `handleWsMessage` — обрабатывает realtime/alarm/anomaly сообщения |

### theme.js — Тема

- `isDark` — текущая тема (из `localStorage`)
- `toggle()` — переключение dark/light
- Устанавливает класс `dark` на `<html>` для Tailwind CSS

## Composables

### useCompressorWs(stationCode)

Реактивная обёртка над WebSocket для realtime данных от OPC-коллектора.

**Возвращает:**
- `connected` — ref, true когда WS подключён
- `error` — ref, сообщение об ошибке

**Логика:**
- URL: `ws(s)://{host}/api/modules/compressor/ws/{code}?token={jwt}`
- При получении сообщения вызывает `store.handleWsMessage(data)`
- Auto-reconnect с exponential backoff (1с → 30с max)
- Обработка кодов закрытия: 4001 (Unauthorized), 4004 (Station not found)
- Cleanup при unmount и смене станции

## Маршрутизация

### Маршруты

| Путь | Компонент | Guard |
|------|-----------|-------|
| `/` | Landing | guestOnly |
| `/login` | Login | guestOnly |
| `/register` | Register | guestOnly |
| `/verify-email` | VerifyEmail | — |
| `/forgot-password` | ForgotPassword | — |
| `/dashboard` | Dashboard | requiresAuth |
| `/settings` | Settings | requiresAuth |
| `/compressor` | CompressorHome | requiresAuth + requiresPermission(`compressor.access`) |
| `/balance` | BalanceHome | requiresAuth + requiresPermission(`balance.access`) |
| `/weather` | WeatherHome | requiresAuth + requiresPermission(`weather.access`) |
| `/digital` | DigitalHome | requiresAuth + requiresPermission(`digital.access`) |
| `/ai-chat` | AiChatHome | requiresAuth + requiresPermission(`ai_chat.access`) |
| `/scada` | ScadaHome | requiresAuth + requiresPermission(`scada.access`) |
| `/admin/users` | AdminUsers | requiresAuth + requiresAdmin |
| `/admin/users/:id` | AdminUserDetail | requiresAuth + requiresAdmin |
| `/admin/audit-logs` | AdminAuditLogs | requiresAuth + requiresAdmin |
| `/admin/system` | AdminSystem | requiresAuth + requiresAdmin |
| `/admin/compressor` | AdminCompressor | requiresAuth + requiresPermission(`compressor.manage`) |

### Navigation Guards

```
Перед каждым переходом (beforeEach):

1. Загрузить данные пользователя (auth.init())
2. Страница требует авторизации (requiresAuth)?
   → Не авторизован? → redirect /login
   → Требует admin (requiresAdmin)?
     → Не admin? → redirect /dashboard
   → Требует permission?
     → Нет permission? → redirect /dashboard
3. Страница только для гостей (guestOnly)?
   → Авторизован? → redirect /dashboard
```

## Страницы компрессорного модуля

### CompressorHome.vue — Мониторинг

Основная страница модуля для пользователей с доступом `compressor.access`.

**Функциональность:**
- Выбор станции из dropdown
- Статус-бар: WebSocket connected/disconnected, last update, кол-во тегов
- **4 вкладки:**
  - **Realtime** — карточки тегов, сгруппированные по категориям (Температура, Давление...), с quality-индикацией (good=зелёный, stale=жёлтый, outlier=красный, bad=серый) + блок вычисляемых тегов (статусы)
  - **Аварии** — журнал аварий с severity-цветами (info=синий, warning=жёлтый, critical=красный) и кнопкой квитирования
  - **Аномалии** — журнал аномалий с типом детектора и кнопкой квитирования
  - **История** — график Chart.js с историческими данными тегов
- WebSocket через `useCompressorWs` — автообновление при получении данных

### CompressorSettings.vue — Управление

Компонент настроек, используется как на странице `/admin/compressor` (через AdminCompressor.vue), так и встраивается в CompressorHome.

**Секции (доступ по permissions):**
1. **Станции** (`compressor.admin`) — таблица станций, CRUD, генерация/скачивание сертификатов
2. **Диагностика** (`compressor.manage`) — 5 карточек статуса (OPC, сертификат, теги, обновление, ошибка) + чеклист-подсказки
3. **Теги** (`compressor.manage`) — таблица тегов, CRUD, импорт из Excel, скачивание шаблона
4. **Вычисляемые теги** (`compressor.manage`) — список, CRUD с JSON-конфигом (status_map / formula)
5. **Правила аварий** (`compressor.manage`) — список правил, CRUD (condition + threshold + severity)
6. **Правила аномалий** (`compressor.manage`) — список правил, CRUD с JSON-конфигом детектора
7. **Импорт истории** (`compressor.manage`) — загрузка Excel с историческими данными, скачивание шаблона

**5 модальных окон** для создания/редактирования каждой сущности.

### AdminCompressor.vue — Admin wrapper

Обёртка для страницы `/admin/compressor`: заголовок, выбор станции и компонент `CompressorSettings`.

## Дашборд

Дашборд (`Dashboard.vue`) отображает **карточки доступных модулей**. Модуль отображается только если у пользователя есть permission `{module}.access`:

```js
const availableModules = computed(() =>
  modules.filter(m => auth.hasPermission(m.permission))
)
```

Суперадминистратор видит все модули.

## Мультиязычность (i18n)

### Поддерживаемые языки

- **ru** — Русский (по умолчанию)
- **uz** — Узбекский

Язык сохраняется в `localStorage` и применяется при загрузке.

### Структура переводов

Файлы `i18n/ru.js` и `i18n/uz.js` содержат вложенные объекты:

```js
export default {
  navbar: { ... },       // Навигация
  landing: { ... },      // Главная страница
  login: { ... },        // Вход
  register: { ... },     // Регистрация
  verifyEmail: { ... },  // Подтверждение email
  forgotPassword: { ... }, // Сброс пароля
  modules: {
    compressor: {
      name, description,
      selectStation, noStations,
      status, connected, disconnected,
      realtime, alarmsTab, anomaliesTab, history,
      value, quality, noData, category,
      severity: { info, warning, critical },
      acknowledge, acknowledged, notAcknowledged,
      importTags, importHistory, importResult,
      settings: {
        stationsTitle, addStation, editStation, deleteStation,
        tagsTitle, addTag, editTag,
        computedTitle, addComputed, computeType,
        alarmRulesTitle, anomalyRulesTitle,
        diagnosticsTitle, certReady, certMissing,
        diagStationActive, diagCertOk, diagTagsOk, diagCollectorOk,
        downloadTemplate, importExcel,
        // ... и другие (~145 ключей)
      },
    },
    balance: { name, description },
    // ... другие модули
    accessLevel, capabilities,
    levelNames: { viewer, operator, manager, admin, superadmin },
  },
  dashboard: { ... },
  settings: { ... },
  admin: {
    users: { ... },
    moduleAccess: { ... },
    audit: { ... },
    systemPage: { ... },
  },
  months: [...],
}
```

## Тёмная тема

Tailwind CSS с `darkMode: 'class'`. Класс `dark` устанавливается на `<html>`:

```html
<!-- Светлая тема -->
<html>
  <div class="bg-white text-gray-900">

<!-- Тёмная тема -->
<html class="dark">
  <div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
```

Переключатель темы находится в Navbar (иконки солнце/луна). Выбор сохраняется в `localStorage`.

## Навигация (Navbar)

Navbar — боковая панель (sidebar), которая открывается по нажатию на гамбургер-меню.

**Для неавторизованных:**
- Кнопки «Вход» и «Регистрация»

**Для авторизованных:**
- Аватар, имя, email пользователя
- Dashboard
- Модули (отображаются по permissions):
  - Компрессорные станции (`compressor.access`)
  - И другие модули
- Настройки
- **Для пользователей с admin-доступом:**
  - Разделитель «Администрирование»
  - Пользователи
  - Журнал действий
  - Система (мониторинг)
  - Компрессорные станции (настройки, если `compressor.manage`)
- Кнопка «Выход»

**Верхняя панель:**
- Логотип и название
- Переключатель языка (RU / UZ)
- Переключатель темы (солнце / луна)
- Гамбургер-меню
