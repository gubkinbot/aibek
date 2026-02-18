<template>
  <div class="h-dvh flex flex-col overflow-hidden">
    <Navbar />
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>
