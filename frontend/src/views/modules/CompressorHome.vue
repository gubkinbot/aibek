<template>
  <div class="relative w-full min-h-[calc(100dvh-57px)] bg-white dark:bg-[#020204] transition-colors duration-500">
    <!-- PulseOrb background -->
    <PulseOrb
      :state="orbState"
      :intensity="orbIntensity"
      :pulse-mode="orbPulseMode"
      :dark="themeStore.theme === 'dark'"
      class="!absolute inset-0"
    />

    <!-- Content overlay -->
    <div class="relative z-10 w-[90%] max-w-7xl mx-auto py-8">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-orange-500/20 backdrop-blur-sm flex items-center justify-center">
            <svg class="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('modules.compressor.name') }}</h1>
        </div>

        <!-- Station selector -->
        <select
          v-model="selectedCode"
          class="px-4 py-2 rounded-lg bg-white/60 dark:bg-gray-800/60 backdrop-blur-xl border border-gray-200/30 dark:border-white/[0.08] text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50"
        >
          <option value="">{{ t('modules.compressor.selectStation') }}</option>
          <option v-for="s in store.stations" :key="s.code" :value="s.code">{{ s.name }}</option>
        </select>
      </div>

      <!-- No stations -->
      <div v-if="!store.loading && store.stations.length === 0" class="glass-card p-8 text-center">
        <p class="text-gray-500 dark:text-gray-400">{{ t('modules.compressor.noStations') }}</p>
      </div>

      <!-- Station dashboard -->
      <template v-if="selectedCode">
        <!-- Status bar -->
        <div class="glass-card p-4 mb-4 flex items-center gap-6 flex-wrap">
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full" :class="wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></span>
            <span class="text-sm text-gray-700 dark:text-gray-300">
              {{ wsConnected ? t('modules.compressor.connected') : t('modules.compressor.disconnected') }}
            </span>
          </div>
          <div v-if="store.realtimeData?.timestamp" class="text-xs text-gray-500 dark:text-gray-400">
            {{ t('modules.compressor.lastUpdate') }}: {{ formatTime(store.realtimeData.timestamp) }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">
            {{ t('modules.compressor.tagsCount') }}: {{ Object.keys(store.realtimeData?.tags || {}).length }}
          </div>
        </div>

        <!-- Tabs -->
        <div class="flex gap-1 mb-4">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/25'
                : 'bg-white/40 dark:bg-gray-800/40 text-gray-600 dark:text-gray-400 hover:bg-white/60 dark:hover:bg-gray-800/60'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab: Realtime -->
        <div v-if="activeTab === 'realtime'">
          <div v-if="!store.realtimeData || Object.keys(store.realtimeData.tags || {}).length === 0" class="glass-card p-8 text-center">
            <p class="text-gray-500 dark:text-gray-400">{{ t('modules.compressor.noData') }}</p>
          </div>
          <template v-else>
            <div v-for="(catTags, category) in groupedTags" :key="category" class="mb-6">
              <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider">{{ category || t('modules.compressor.category') }}</h3>
              <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                <div
                  v-for="(tag, id) in catTags"
                  :key="id"
                  :class="['glass-card p-4 rounded-xl', qualityBorder(tag.quality)]"
                >
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1 truncate">{{ tag.name }}</div>
                  <div class="text-2xl font-bold text-gray-900 dark:text-white">
                    {{ tag.value !== null && tag.value !== undefined ? Number(tag.value).toFixed(1) : '—' }}
                    <span v-if="tag.unit" class="text-sm font-normal text-gray-400">{{ tag.unit }}</span>
                  </div>
                  <div class="text-xs mt-1" :class="qualityColor(tag.quality)">{{ tag.quality }}</div>
                </div>
              </div>
            </div>

            <!-- Computed tags -->
            <div v-if="Object.keys(store.realtimeData.computed || {}).length > 0" class="mb-6">
              <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wider">{{ t('modules.compressor.status') }}</h3>
              <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                <div v-for="(ct, id) in store.realtimeData.computed" :key="id" class="glass-card p-4 rounded-xl">
                  <div class="text-xs text-gray-500 dark:text-gray-400 mb-1 truncate">{{ ct.name }}</div>
                  <div class="text-lg font-bold text-gray-900 dark:text-white">
                    {{ ct.status || ct.value }}
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Tab: Alarms -->
        <div v-if="activeTab === 'alarms'">
          <div v-if="store.alarms.items.length === 0" class="glass-card p-8 text-center">
            <p class="text-gray-500 dark:text-gray-400">{{ t('modules.compressor.noData') }}</p>
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="(alarm, idx) in store.alarms.items"
              :key="idx"
              :class="['glass-card p-4 rounded-xl border-l-4', severityBorder(alarm.severity)]"
            >
              <div class="flex items-center justify-between">
                <div>
                  <span :class="['text-xs font-bold uppercase mr-2', severityColor(alarm.severity)]">
                    {{ t(`modules.compressor.severity.${alarm.severity}`) }}
                  </span>
                  <span class="text-sm text-gray-700 dark:text-gray-300">{{ alarm.message }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="text-xs text-gray-500">{{ formatTime(alarm.time) }}</span>
                  <button
                    v-if="!alarm.acknowledged"
                    @click="doAcknowledgeAlarm(alarm)"
                    class="text-xs px-3 py-1 rounded bg-orange-500/20 text-orange-600 dark:text-orange-400 hover:bg-orange-500/30 transition-colors"
                  >
                    {{ t('modules.compressor.acknowledge') }}
                  </button>
                  <span v-else class="text-xs text-green-500">{{ t('modules.compressor.acknowledged') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Anomalies -->
        <div v-if="activeTab === 'anomalies'">
          <div v-if="store.anomalies.items.length === 0" class="glass-card p-8 text-center">
            <p class="text-gray-500 dark:text-gray-400">{{ t('modules.compressor.noData') }}</p>
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="(anomaly, idx) in store.anomalies.items"
              :key="idx"
              :class="['glass-card p-4 rounded-xl border-l-4', severityBorder(anomaly.severity)]"
            >
              <div class="flex items-center justify-between">
                <div>
                  <span :class="['text-xs font-bold uppercase mr-2', severityColor(anomaly.severity)]">
                    {{ anomaly.detector_type }}
                  </span>
                  <span class="text-sm text-gray-700 dark:text-gray-300">{{ anomaly.message }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="text-xs text-gray-500">{{ formatTime(anomaly.time) }}</span>
                  <button
                    v-if="!anomaly.acknowledged"
                    @click="doAcknowledgeAnomaly(anomaly)"
                    class="text-xs px-3 py-1 rounded bg-orange-500/20 text-orange-600 dark:text-orange-400 hover:bg-orange-500/30 transition-colors"
                  >
                    {{ t('modules.compressor.acknowledge') }}
                  </button>
                  <span v-else class="text-xs text-green-500">{{ t('modules.compressor.acknowledged') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: History -->
        <div v-if="activeTab === 'history'">
          <div class="glass-card p-6">
            <canvas ref="chartCanvas" height="300"></canvas>
            <p v-if="!chartReady" class="text-center text-gray-500 dark:text-gray-400 py-8">{{ t('modules.compressor.noData') }}</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useThemeStore } from '../../stores/theme'
import { useCompressorStore } from '../../stores/compressor'
import { useCompressorWs } from '../../composables/useCompressorWs'
import PulseOrb from '../../components/PulseOrb.vue'

const { t } = useI18n()
const themeStore = useThemeStore()
const store = useCompressorStore()

const orbState = ref(0)
const orbIntensity = ref(0.6)
const orbPulseMode = ref(0)

const selectedCode = ref('')
const activeTab = ref('realtime')
const chartCanvas = ref(null)
const chartReady = ref(false)

const tabs = computed(() => [
  { key: 'realtime', label: t('modules.compressor.realtime') },
  { key: 'alarms', label: t('modules.compressor.alarmsTab') },
  { key: 'anomalies', label: t('modules.compressor.anomaliesTab') },
  { key: 'history', label: t('modules.compressor.history') },
])

// WebSocket
const { connected: wsConnected } = useCompressorWs(computed(() => selectedCode.value))

// Group tags by category
const groupedTags = computed(() => {
  const tags = store.realtimeData?.tags || {}
  const groups = {}
  for (const [id, tag] of Object.entries(tags)) {
    const cat = tag.category || ''
    if (!groups[cat]) groups[cat] = {}
    groups[cat][id] = tag
  }
  return groups
})

// Formatting
function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function qualityBorder(q) {
  if (q === 'outlier') return 'border border-red-500/30'
  if (q === 'stale') return 'border border-yellow-500/30'
  if (q === 'bad') return 'border border-gray-500/30'
  return ''
}

function qualityColor(q) {
  if (q === 'good') return 'text-green-500'
  if (q === 'outlier') return 'text-red-500'
  if (q === 'stale') return 'text-yellow-500'
  return 'text-gray-500'
}

function severityBorder(s) {
  if (s === 'critical') return 'border-red-500'
  if (s === 'warning') return 'border-yellow-500'
  return 'border-blue-500'
}

function severityColor(s) {
  if (s === 'critical') return 'text-red-500'
  if (s === 'warning') return 'text-yellow-500'
  return 'text-blue-500'
}

// Actions
async function doAcknowledgeAlarm(alarm) {
  try {
    await store.acknowledgeAlarm(alarm.time, alarm.station_id)
    alarm.acknowledged = true
  } catch (e) {
    // ignore
  }
}

async function doAcknowledgeAnomaly(anomaly) {
  try {
    await store.acknowledgeAnomaly(anomaly.time, anomaly.station_id)
    anomaly.acknowledged = true
  } catch (e) {
    // ignore
  }
}

// Load station data when selection changes
watch(selectedCode, async (code) => {
  if (!code) return
  activeTab.value = 'realtime'
  await Promise.all([
    store.fetchStation(code),
    store.fetchRealtime(code),
    store.fetchAlarms(code),
    store.fetchAnomalies(code),
  ])
})

// Load stations on mount
onMounted(async () => {
  await store.fetchStations()
  if (store.stations.length > 0 && !selectedCode.value) {
    selectedCode.value = store.stations[0].code
  }
})
</script>

<style scoped>
.glass-card {
  @apply bg-white/60 dark:bg-gray-800/60 backdrop-blur-xl backdrop-saturate-[1.8] rounded-lg shadow-lg border border-gray-200/30 dark:border-white/[0.08];
}
</style>
