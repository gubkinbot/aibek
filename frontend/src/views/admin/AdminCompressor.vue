<template>
  <div class="w-[80%] mx-auto py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('navbar.adminCompressor') }}</h1>

      <select
        v-model="selectedCode"
        class="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50"
      >
        <option value="">{{ t('modules.compressor.selectStation') }}</option>
        <option v-for="s in store.stations" :key="s.code" :value="s.code">{{ s.name }}</option>
      </select>
    </div>

    <CompressorSettings :selected-code="selectedCode" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCompressorStore } from '../../stores/compressor'
import CompressorSettings from '../modules/CompressorSettings.vue'

const { t } = useI18n()
const store = useCompressorStore()
const selectedCode = ref('')

onMounted(async () => {
  await store.fetchStations()
  if (store.stations.length > 0 && !selectedCode.value) {
    selectedCode.value = store.stations[0].code
  }
})
</script>
