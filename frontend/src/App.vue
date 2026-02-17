<template>
  <div class="min-h-screen flex flex-col">
    <Navbar />
    <main class="flex-1">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>
