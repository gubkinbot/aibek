import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'AI-платформа Узтрансгаз',
  description: 'Документация AI-платформы АО «Узтрансгаз»',
  lang: 'ru-RU',
  base: '/docs/',

  themeConfig: {
    nav: [
      { text: 'Главная', link: '/' },
      { text: 'Руководство', link: '/guide/getting-started' },
      { text: 'API', link: '/api/overview' },
      { text: 'Архитектура', link: '/architecture/overview' },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Введение',
          items: [
            { text: 'Начало работы', link: '/guide/getting-started' },
            { text: 'Установка и запуск', link: '/guide/installation' },
            { text: 'Конфигурация', link: '/guide/configuration' },
          ],
        },
      ],
      '/api/': [
        {
          text: 'API',
          items: [
            { text: 'Обзор', link: '/api/overview' },
            { text: 'Аутентификация', link: '/api/authentication' },
          ],
        },
      ],
      '/architecture/': [
        {
          text: 'Архитектура',
          items: [
            { text: 'Обзор системы', link: '/architecture/overview' },
            { text: 'Стек технологий', link: '/architecture/tech-stack' },
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
