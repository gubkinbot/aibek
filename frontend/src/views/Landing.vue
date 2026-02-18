<template>
  <div class="relative w-full h-full bg-white dark:bg-[#020204] transition-colors duration-500">
    <PulseOrb
      :state="orbState"
      :intensity="orbIntensity"
      :pulse-mode="orbPulseMode"
      :dark="themeStore.theme === 'dark'"
    />
    <PulseControls
      v-model:state="orbState"
      v-model:intensity="orbIntensity"
      v-model:pulse-mode="orbPulseMode"
      :dark="themeStore.theme === 'dark'"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useFullscreen } from '../composables/useFullscreen'
import { useThemeStore } from '../stores/theme'
import PulseOrb from '../components/PulseOrb.vue'
import PulseControls from '../components/PulseControls.vue'

const themeStore = useThemeStore()
const { isFullscreen } = useFullscreen()

const orbState = ref(0)
const orbIntensity = ref(1)
const orbPulseMode = ref(0)
</script>
