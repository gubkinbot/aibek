import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'AI-платформа Узтрансгаз',
  description: 'Документация AI-платформы АО «Узтрансгаз»',
  lang: 'ru-RU',
  base: '/docs/',

  vite: {
    server: {
      allowedHosts: ['.utg.uz'],
    },
  },

  themeConfig: {
    nav: [
      { text: 'Главная', link: '/' },
      { text: 'Руководство', link: '/guide/getting-started' },
      { text: 'API', link: '/api/overview' },
      { text: 'Архитектура', link: '/architecture/overview' },
      { text: 'ML-проекты', link: '/ml/overview' },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Руководство',
          items: [
            { text: 'Начало работы', link: '/guide/getting-started' },
            { text: 'Установка и запуск', link: '/guide/installation' },
            { text: 'Конфигурация', link: '/guide/configuration' },
          ],
        },
      ],
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Обзор', link: '/api/overview' },
            { text: 'Аутентификация', link: '/api/authentication' },
            { text: 'Администрирование', link: '/api/admin' },
          ],
        },
      ],
      '/architecture/': [
        {
          text: 'Архитектура',
          items: [
            { text: 'Обзор системы', link: '/architecture/overview' },
            { text: 'Стек технологий', link: '/architecture/tech-stack' },
            { text: 'Система ролей (RBAC)', link: '/architecture/rbac' },
            { text: 'Фронтенд', link: '/architecture/frontend' },
          ],
        },
      ],
      '/ml/': [
        {
          text: 'ML-проекты',
          items: [
            { text: 'Обзор', link: '/ml/overview' },
            { text: '1. Компрессорные станции', link: '/ml/compressor-stations' },
            { text: '2. Прогноз потребления газа', link: '/ml/gas-consumption' },
            { text: '3. Погодные риски', link: '/ml/weather-risks' },
            { text: '4. Цифровой департамент идей', link: '/ml/ideas-department' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/gubkinbot/aibek' },
    ],

    search: {
      provider: 'local',
    },

    outline: {
      label: 'На этой странице',
    },

    docFooter: {
      prev: 'Назад',
      next: 'Далее',
    },
  },
})
