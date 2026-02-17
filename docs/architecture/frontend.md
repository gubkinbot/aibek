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
│   ├── auth.js       # Аутентификация
│   ├── admin.js      # Админ-операции
│   └── theme.js      # Тема (dark/light)
│
├── router/
│   └── index.js      # Маршруты и navigation guards
│
├── components/
│   └── Navbar.vue    # Навигация, sidebar, тема, язык
│
├── views/            # Страницы
│   ├── Landing.vue
│   ├── Login.vue
│   ├── Register.vue
│   ├── VerifyEmail.vue
│   ├── ForgotPassword.vue
│   ├── Dashboard.vue
│   ├── Settings.vue
│   └── admin/
│       ├── AdminUsers.vue
│       ├── AdminUserDetail.vue
│       ├── AdminRoles.vue
│       ├── AdminGroups.vue
│       ├── AdminDepartments.vue
│       └── AdminAuditLogs.vue
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
- `isAdmin` — есть ли роль `admin` или `superadmin`
- `isSuperAdmin` — есть ли роль `superadmin`

**Методы:**
- `init()` — загружает данные пользователя при первом переходе
- `login(email, password)` — вход + загрузка профиля
- `register(email, password, fullName)` — регистрация
- `verifyEmail(email, code)` — подтверждение email
- `logout()` — очистка сессии
- `fetchUser()` — загрузка `/auth/me`
- `forgotPassword(email)` / `resetPassword(...)` — сброс пароля
- `changePassword(...)` / `updateProfile(...)` — профиль

**Паттерн инициализации:**

```js
// В router.beforeEach — однократная загрузка пользователя
await auth.init()
// init() вызывает fetchUser() только если:
// 1. Есть токен
// 2. Данные пользователя ещё не загружены
// 3. Инициализация ещё не выполнялась
```

### admin.js — Админ-операции

Стор для всех CRUD-операций администрирования.

**Основные методы:**

| Группа | Методы |
|--------|--------|
| Пользователи | `fetchUsers(params)`, `fetchUser(id)`, `createUser(data)`, `updateUser(id, data)`, `blockUser(id, reason)`, `unblockUser(id)`, `resetPassword(id)`, `deleteUser(id)` |
| Роли | `fetchRoles()`, `createRole(data)`, `updateRole(id, data)`, `deleteRole(id)`, `fetchRole(id)`, `setRolePermissions(id, permIds)` |
| Группы | `fetchGroups()`, `createGroup(data)`, `updateGroup(id, data)`, `deleteGroup(id)`, `fetchGroup(id)`, `setGroupPermissions(id, permIds)`, `setGroupMembers(id, userIds)` |
| Подразделения | `fetchDepartments()`, `createDepartment(data)`, `updateDepartment(id, data)`, `deleteDepartment(id)`, `setDepartmentMembers(id, userIds)` |
| Назначение | `assignUserRoles(userId, roleIds)`, `assignUserGroups(userId, groupIds)`, `assignUserDepartments(userId, deptIds)` |
| Permissions | `fetchPermissions()` |
| Аудит | `fetchAuditLogs(params)` |

### theme.js — Тема

- `isDark` — текущая тема (из `localStorage`)
- `toggle()` — переключение dark/light
- Устанавливает класс `dark` на `<html>` для Tailwind CSS

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
| `/admin/users` | AdminUsers | requiresAuth + requiresAdmin |
| `/admin/users/:id` | AdminUserDetail | requiresAuth + requiresAdmin |
| `/admin/roles` | AdminRoles | requiresAuth + requiresAdmin |
| `/admin/groups` | AdminGroups | requiresAuth + requiresAdmin |
| `/admin/departments` | AdminDepartments | requiresAuth + requiresAdmin |
| `/admin/audit-logs` | AdminAuditLogs | requiresAuth + requiresAdmin |

### Navigation Guards

```
Перед каждым переходом (beforeEach):

1. Загрузить данные пользователя (auth.init())
2. Страница требует авторизации (requiresAuth)?
   → Не авторизован? → redirect /login
   → Требует admin (requiresAdmin)?
     → Не admin? → redirect /dashboard
3. Страница только для гостей (guestOnly)?
   → Авторизован? → redirect /dashboard
```

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
  dashboard: { ... },    // Дашборд
  settings: { ... },     // Настройки
  admin: {               // Админ-панель
    users: { ... },
    roles: { ... },
    groups: { ... },
    departments: { ... },
    audit: { ... },
    permissions: { ... },
  },
  months: [...],         // Названия месяцев (полные)
  monthsShort: [...],    // Названия месяцев (сокращённые)
}
```

### Форматирование дат

Браузеры не всегда поддерживают локаль `uz-Latn-UZ`, поэтому используется кастомный форматтер на основе i18n:

```js
import { useDateFormat } from '../utils/date'

const { formatDate, formatDateTime } = useDateFormat()
formatDate('2026-02-17T09:30:00Z')  // "17 фев 2026" (ru) / "17 fev 2026" (uz)
formatDateTime('2026-02-17T09:30:00Z')  // "17 фев 2026, 14:30"
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
- Настройки
- **Для admin/superadmin:**
  - Разделитель «Администрирование»
  - Пользователи
  - Роли
  - Группы
  - Подразделения
  - Журнал действий
- Кнопка «Выход»

**Верхняя панель:**
- Логотип и название
- Переключатель языка (RU / UZ)
- Переключатель темы (солнце / луна)
- Гамбургер-меню
