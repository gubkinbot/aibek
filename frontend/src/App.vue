<template>
  <div class="h-dvh overflow-y-auto">
    <Navbar />
    <main :class="containerClass">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'

const route = useRoute()

const containerClass = computed(() => {
  if (!route.meta.requiresAuth || route.meta.noContainer) return ''
  return 'px-4 sm:px-6 lg:w-[80%] lg:px-0 mx-auto'
})
</script>
