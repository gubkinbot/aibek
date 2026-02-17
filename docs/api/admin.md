# API — Администрирование

Все admin-эндпоинты находятся под префиксом `/api/admin` и требуют аутентификации + соответствующих permissions.

::: info Проверка доступа
Каждый эндпоинт проверяет наличие конкретного permission у пользователя. Superadmin автоматически проходит все проверки. Подробнее: [Система ролей (RBAC)](../architecture/rbac).
:::

## Управление пользователями

### Список пользователей

```http
GET /api/admin/users?page=1&per_page=20&search=иванов&role=admin&is_active=true
Authorization: Bearer <токен>
```

**Параметры запроса:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `page` | int | Номер страницы (от 1) |
| `per_page` | int | Количество на странице (1–100, по умолчанию 20) |
| `search` | string | Поиск по ФИО, email, телефону |
| `role` | string | Фильтр по имени роли |
| `is_active` | bool | Фильтр по статусу (активен/заблокирован) |
| `auth_provider` | string | Фильтр по типу авторизации (`email`, `telegram`) |

**Ответ (200):**

```json
{
  "items": [
    {
      "id": "550e8400-...",
      "email": "ivanov@utg.uz",
      "full_name": "Иванов Иван",
      "phone": null,
      "auth_provider": "email",
      "is_active": true,
      "is_verified": true,
      "created_at": "2026-02-17T09:30:00Z",
      "role_names": ["admin"]
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

**Permission:** `users.view`

### Детали пользователя

```http
GET /api/admin/users/{user_id}
```

Возвращает полную информацию, включая роли (с деталями), группы и подразделения.

**Permission:** `users.view`

### Создать пользователя

```http
POST /api/admin/users
Content-Type: application/json

{
  "email": "petrov@utg.uz",
  "full_name": "Петров Пётр",
  "password": "optional-password",
  "role_ids": ["uuid-роли-admin"]
}
```

Если `password` не указан, генерируется временный пароль и возвращается в ответе. Пользователь создаётся сразу верифицированным.

**Ответ (201):**

```json
{
  "message": "Пользователь petrov@utg.uz создан. Временный пароль: aB3dEf9x",
  "temp_password": "aB3dEf9x"
}
```

**Permission:** `users.create`

### Редактировать пользователя

```http
PATCH /api/admin/users/{user_id}
Content-Type: application/json

{
  "full_name": "Петров Пётр Сергеевич",
  "email": "p.petrov@utg.uz",
  "phone": "+998901234567"
}
```

Все поля опциональны — передавайте только то, что нужно изменить.

**Permission:** `users.edit`

### Заблокировать пользователя

```http
POST /api/admin/users/{user_id}/block
Content-Type: application/json

{
  "reason": "Нарушение правил использования"
}
```

Заблокированный пользователь не может войти в систему. Его `is_active` устанавливается в `false`, фиксируется дата и причина блокировки.

**Permission:** `users.block`

::: warning Защита
Суперадминистратора нельзя заблокировать. Попытка вернёт `403 Forbidden`.
:::

### Разблокировать пользователя

```http
POST /api/admin/users/{user_id}/unblock
```

**Permission:** `users.block`

### Сбросить пароль

```http
POST /api/admin/users/{user_id}/reset-password
```

Генерирует новый временный пароль. Если почта включена — отправляет его пользователю на email.

**Ответ (200):**

```json
{
  "message": "Пароль сброшен для petrov@utg.uz",
  "temp_password": "xK9mNp2v"
}
```

**Permission:** `users.reset_password`

### Удалить пользователя

```http
DELETE /api/admin/users/{user_id}
```

Полное удаление пользователя из базы данных.

**Ограничения:**
- Нельзя удалить суперадминистратора
- Нельзя удалить самого себя

**Permission:** `users.delete`

### Назначить роли

```http
PUT /api/admin/users/{user_id}/roles
Content-Type: application/json

{
  "role_ids": ["uuid-роли-1", "uuid-роли-2"]
}
```

**Заменяет** все текущие роли пользователя на указанные. Для удаления всех ролей — передайте пустой массив.

**Permission:** `roles.manage`

::: warning
Назначить роль `superadmin` может только суперадминистратор.
:::

### Назначить группы

```http
PUT /api/admin/users/{user_id}/groups
Content-Type: application/json

{
  "group_ids": ["uuid-группы-1"]
}
```

**Permission:** `groups.manage`

### Назначить подразделения

```http
PUT /api/admin/users/{user_id}/departments
Content-Type: application/json

{
  "department_ids": ["uuid-подразделения-1"]
}
```

**Permission:** `departments.manage`

---

## Управление ролями

### Список ролей

```http
GET /api/admin/roles
```

Возвращает все роли, отсортированные: системные сначала, затем по имени. Каждая роль включает `user_count` — количество пользователей с этой ролью.

**Permission:** `roles.view`

### Создать роль

```http
POST /api/admin/roles
Content-Type: application/json

{
  "name": "operator",
  "display_name": "Оператор",
  "description": "Оператор производственных процессов"
}
```

Имя роли (`name`) — уникальный идентификатор: только буквы, цифры, `_` и `-`, минимум 2 символа.

**Permission:** `roles.manage`

### Детали роли

```http
GET /api/admin/roles/{role_id}
```

Возвращает роль со списком всех её permissions.

**Permission:** `roles.view`

### Обновить роль

```http
PATCH /api/admin/roles/{role_id}
Content-Type: application/json

{
  "display_name": "Новое отображаемое имя",
  "description": "Обновлённое описание"
}
```

::: warning
Системные роли (`superadmin`, `admin`, `user`) нельзя редактировать.
:::

**Permission:** `roles.manage`

### Удалить роль

```http
DELETE /api/admin/roles/{role_id}
```

**Ограничения:**
- Системные роли нельзя удалять
- Нельзя удалить роль, назначенную пользователям

**Permission:** `roles.manage`

### Установить permissions для роли

```http
PUT /api/admin/roles/{role_id}/permissions
Content-Type: application/json

{
  "permission_ids": ["uuid-perm-1", "uuid-perm-2", "uuid-perm-3"]
}
```

**Заменяет** все permissions роли на указанные.

::: info
Роль `superadmin` не нуждается в permissions — суперадминистратор автоматически проходит все проверки.
:::

**Permission:** `roles.manage`

---

## Управление группами

Группы — это наборы пользователей с общими permissions. Пользователь может состоять в нескольких группах.

### Список групп

```http
GET /api/admin/groups
```

**Permission:** `groups.view`

### Создать группу

```http
POST /api/admin/groups
Content-Type: application/json

{
  "name": "Аналитики газопроводов",
  "description": "Доступ к аналитическим данным"
}
```

**Permission:** `groups.manage`

### Детали группы

```http
GET /api/admin/groups/{group_id}
```

Возвращает группу со списком permissions.

**Permission:** `groups.view`

### Обновить группу

```http
PATCH /api/admin/groups/{group_id}
Content-Type: application/json

{
  "name": "Новое название",
  "description": "Новое описание"
}
```

**Permission:** `groups.manage`

### Удалить группу

```http
DELETE /api/admin/groups/{group_id}
```

Нельзя удалить группу, в которой есть участники — сначала уберите всех пользователей.

**Permission:** `groups.manage`

### Установить permissions для группы

```http
PUT /api/admin/groups/{group_id}/permissions
Content-Type: application/json

{
  "permission_ids": ["uuid-perm-1", "uuid-perm-2"]
}
```

**Permission:** `groups.manage`

### Установить участников группы

```http
PUT /api/admin/groups/{group_id}/members
Content-Type: application/json

{
  "user_ids": ["uuid-user-1", "uuid-user-2"]
}
```

**Заменяет** всех текущих участников на указанных.

**Permission:** `groups.manage`

---

## Управление подразделениями

Подразделения образуют иерархическую структуру (дерево). Каждое подразделение может иметь родительское подразделение и дочерние.

### Дерево подразделений

```http
GET /api/admin/departments
```

Возвращает дерево подразделений:

```json
[
  {
    "id": "...",
    "name": "Центральный аппарат",
    "description": null,
    "parent_id": null,
    "created_at": "2026-02-17T09:00:00Z",
    "user_count": 15,
    "children": [
      {
        "id": "...",
        "name": "IT-отдел",
        "parent_id": "...",
        "user_count": 5,
        "children": []
      }
    ]
  }
]
```

**Permission:** `departments.view`

### Создать подразделение

```http
POST /api/admin/departments
Content-Type: application/json

{
  "name": "IT-отдел",
  "description": "Информационные технологии",
  "parent_id": "uuid-родительского-подразделения"
}
```

`parent_id` — опционален. Если не указан, подразделение будет корневым.

**Permission:** `departments.manage`

### Обновить подразделение

```http
PATCH /api/admin/departments/{dept_id}
Content-Type: application/json

{
  "name": "Обновлённое название",
  "parent_id": "uuid-нового-родителя"
}
```

**Permission:** `departments.manage`

### Удалить подразделение

```http
DELETE /api/admin/departments/{dept_id}
```

**Ограничения:**
- Нельзя удалить подразделение, у которого есть дочерние
- Нельзя удалить подразделение, в котором есть сотрудники

**Permission:** `departments.manage`

### Установить участников подразделения

```http
PUT /api/admin/departments/{dept_id}/members
Content-Type: application/json

{
  "user_ids": ["uuid-user-1", "uuid-user-2"]
}
```

**Permission:** `departments.manage`

---

## Разрешения (Permissions)

### Список всех permissions

```http
GET /api/admin/permissions
```

Возвращает permissions, сгруппированные по категориям:

```json
[
  {
    "category": "users",
    "permissions": [
      {
        "id": "...",
        "codename": "users.view",
        "display_name": "Просмотр пользователей",
        "category": "users"
      },
      {
        "id": "...",
        "codename": "users.create",
        "display_name": "Создание пользователей",
        "category": "users"
      }
    ]
  },
  {
    "category": "roles",
    "permissions": [...]
  }
]
```

**Permission:** `roles.view`

---

## Журнал действий (Audit Log)

### Получить журнал

```http
GET /api/admin/audit-logs?page=1&per_page=20&action=user.block&target_type=user
```

**Параметры запроса:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `page` | int | Номер страницы |
| `per_page` | int | Количество на странице (1–100) |
| `actor_id` | UUID | Фильтр по автору действия |
| `action` | string | Фильтр по типу действия |
| `target_type` | string | Фильтр по типу объекта (`user`, `role`, `group`, `department`) |
| `target_id` | UUID | Фильтр по ID объекта |
| `date_from` | datetime | Начало периода |
| `date_to` | datetime | Конец периода |

**Ответ (200):**

```json
{
  "items": [
    {
      "id": "...",
      "actor_id": "uuid-admin",
      "actor_name": "Иванов Иван",
      "action": "user.block",
      "target_type": "user",
      "target_id": "uuid-пользователя",
      "details": {"reason": "Нарушение правил"},
      "ip_address": "10.1.30.50",
      "created_at": "2026-02-17T14:30:00Z"
    }
  ],
  "total": 120,
  "page": 1,
  "per_page": 20,
  "pages": 6
}
```

**Типы действий** (поле `action`):

| Действие | Описание |
|----------|----------|
| `user.create` | Создание пользователя |
| `user.edit` | Редактирование пользователя |
| `user.block` | Блокировка пользователя |
| `user.unblock` | Разблокировка пользователя |
| `user.delete` | Удаление пользователя |
| `user.reset_password` | Сброс пароля |
| `user.roles.assign` | Назначение ролей |
| `user.groups.assign` | Назначение групп |
| `user.departments.assign` | Назначение подразделений |
| `role.create` | Создание роли |
| `role.edit` | Редактирование роли |
| `role.delete` | Удаление роли |
| `role.permissions.set` | Изменение permissions роли |
| `group.create` | Создание группы |
| `group.edit` | Редактирование группы |
| `group.delete` | Удаление группы |
| `group.permissions.set` | Изменение permissions группы |
| `group.members.set` | Изменение участников группы |
| `department.create` | Создание подразделения |
| `department.edit` | Редактирование подразделения |
| `department.delete` | Удаление подразделения |
| `department.members.set` | Изменение участников подразделения |

**Permission:** `audit.view`
