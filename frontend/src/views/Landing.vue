<template>
  <div class="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
    <h1 class="text-4xl font-bold text-gray-900 mb-4">
      AI-платформа АО «Узтрансгаз»
    </h1>
    <p class="text-lg text-gray-600 max-w-2xl mb-8">
      Интеллектуальная платформа для анализа данных, прогнозирования и автоматизации
      бизнес-процессов с использованием искусственного интеллекта.
    </p>
    <div class="flex gap-4">
      <router-link
        to="/register"
        class="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg hover:bg-blue-700 transition"
      >
        Начать работу
      </router-link>
      <router-link
        to="/login"
        class="border border-blue-600 text-blue-600 px-6 py-3 rounded-lg text-lg hover:bg-blue-50 transition"
      >
        Войти
      </router-link>
    </div>
  </div>
</template>
