<template>
  <div class="max-w-7xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-6">{{ t('admin.systemPage.title') }}</h1>

    <!-- Quick Links -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4 text-gray-900 dark:text-white">{{ t('admin.systemPage.quickLinks') }}</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <a
          v-for="link in links"
          :key="link.url"
          :href="link.url"
          target="_blank"
          class="flex items-center gap-3 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" :class="link.bgClass">
            <svg class="w-5 h-5" :class="link.iconClass" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" :d="link.icon" />
            </svg>
          </div>
          <div class="min-w-0">
            <div class="font-medium text-gray-900 dark:text-white">{{ link.label }}</div>
            <div class="text-sm text-gray-500 dark:text-gray-400 truncate">{{ link.description }}</div>
          </div>
        </a>
      </div>
    </div>

    <!-- Service Health -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('admin.systemPage.serviceHealth') }}</h2>
        <button
          @click="loadStatus"
          :disabled="statusLoading"
          class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {{ t('admin.systemPage.refresh') }}
        </button>
      </div>

      <div v-if="statusLoading && !status" class="text-center py-8 text-gray-500">{{ t('admin.loading') }}</div>
      <div v-else-if="statusError" class="text-center py-8">
        <p class="text-red-500 mb-2">{{ t('admin.systemPage.loadError') }}</p>
        <p class="text-sm text-gray-500">{{ statusError }}</p>
      </div>

      <div v-else-if="status" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Backend (FastAPI) -->
        <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div class="flex items-center gap-2 mb-4">
            <span class="w-3 h-3 rounded-full" :class="status.backend?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'" />
            <h3 class="font-medium text-gray-900 dark:text-white">Backend (FastAPI)</h3>
          </div>
          <div class="space-y-3 text-sm">
            <MetricRow :label="t('admin.systemPage.status')" :value="status.backend?.status?.toUpperCase()" :ok="status.backend?.status === 'ok'" />
            <MetricRow :label="t('admin.systemPage.serverTime')" :value="formatTimestamp(status.backend?.timestamp)" small />
            <MetricRow :label="t('admin.systemPage.uptime')" :value="formatUptime(status.backend?.uptime_seconds)" />
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-500 dark:text-gray-400">CPU</span>
                <span class="text-gray-900 dark:text-white font-medium">{{ status.backend?.cpu_percent ?? '-' }}%</span>
              </div>
              <ProgressBar :percent="status.backend?.cpu_percent" />
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-500 dark:text-gray-400">{{ t('admin.systemPage.memory') }}</span>
                <span class="text-gray-900 dark:text-white font-medium">{{ status.backend?.memory_used_fmt }} / {{ status.backend?.memory_total_fmt }}</span>
              </div>
              <ProgressBar :percent="status.backend?.memory_percent" />
            </div>
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-500 dark:text-gray-400">{{ t('admin.systemPage.disk') }}</span>
                <span class="text-gray-900 dark:text-white font-medium">{{ status.backend?.disk_used_fmt }} / {{ status.backend?.disk_total_fmt }}</span>
              </div>
              <ProgressBar :percent="status.backend?.disk_percent" />
            </div>
            <MetricRow :label="t('admin.systemPage.processMemory')" :value="status.backend?.process_memory_fmt" />
          </div>
        </div>

        <!-- Database -->
        <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div class="flex items-center gap-2 mb-4">
            <span class="w-3 h-3 rounded-full" :class="status.database?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'" />
            <h3 class="font-medium text-gray-900 dark:text-white">{{ t('admin.systemPage.database') }}</h3>
          </div>
          <div v-if="status.database?.error" class="text-red-500 text-sm py-4">{{ status.database.error }}</div>
          <div v-else class="space-y-3 text-sm">
            <MetricRow :label="t('admin.systemPage.status')" :value="status.database?.status?.toUpperCase()" :ok="status.database?.status === 'ok'" />
            <MetricRow :label="t('admin.systemPage.version')" :value="shortenPgVersion(status.database?.version)" small />
            <MetricRow :label="t('admin.systemPage.uptime')" :value="formatUptime(status.database?.uptime_seconds)" />
            <MetricRow :label="t('admin.systemPage.dbSize')" :value="status.database?.db_size_fmt" />
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-500 dark:text-gray-400">{{ t('admin.systemPage.connections') }}</span>
                <span class="text-gray-900 dark:text-white font-medium">{{ status.database?.connections }} / {{ status.database?.max_connections }}</span>
              </div>
              <ProgressBar :percent="status.database?.connections_percent" />
            </div>
          </div>
        </div>

        <!-- Redis -->
        <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div class="flex items-center gap-2 mb-4">
            <span class="w-3 h-3 rounded-full" :class="status.redis?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'" />
            <h3 class="font-medium text-gray-900 dark:text-white">Redis</h3>
          </div>
          <div v-if="status.redis?.error" class="text-red-500 text-sm py-4">{{ status.redis.error }}</div>
          <div v-else class="space-y-3 text-sm">
            <MetricRow :label="t('admin.systemPage.status')" :value="status.redis?.status?.toUpperCase()" :ok="status.redis?.status === 'ok'" />
            <MetricRow :label="t('admin.systemPage.version')" :value="status.redis?.version" />
            <MetricRow :label="t('admin.systemPage.uptime')" :value="formatUptime(status.redis?.uptime_seconds)" />
            <div>
              <div class="flex justify-between mb-1">
                <span class="text-gray-500 dark:text-gray-400">{{ t('admin.systemPage.memory') }}</span>
                <span class="text-gray-900 dark:text-white font-medium">{{ status.redis?.memory_used_fmt }} / {{ status.redis?.memory_max_fmt }}</span>
              </div>
              <ProgressBar v-if="status.redis?.memory_percent" :percent="status.redis?.memory_percent" />
            </div>
            <MetricRow :label="t('admin.systemPage.clients')" :value="status.redis?.connected_clients" />
            <MetricRow :label="t('admin.systemPage.keys')" :value="status.redis?.keys_count" />
            <MetricRow :label="t('admin.systemPage.commands')" :value="formatNumber(status.redis?.total_commands)" />
          </div>
        </div>
      </div>
    </div>

    <!-- Docker Container Monitoring -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('admin.systemPage.dockerTitle') }}</h2>
        <div class="flex items-center gap-3">
          <select
            v-model="chartPeriod"
            @change="loadDockerHistory"
            class="border dark:border-gray-600 rounded px-3 py-1.5 bg-white dark:bg-gray-700 dark:text-white text-sm"
          >
            <option :value="60">5 {{ t('admin.systemPage.minutes') }}</option>
            <option :value="120">10 {{ t('admin.systemPage.minutes') }}</option>
            <option :value="360">30 {{ t('admin.systemPage.minutes') }}</option>
            <option :value="720">1 {{ t('admin.systemPage.hour') }}</option>
          </select>
        </div>
      </div>

      <div v-if="dockerLoading && !dockerContainers.length" class="text-center py-8 text-gray-500">{{ t('admin.loading') }}</div>

      <div v-else-if="dockerError" class="text-center py-8">
        <p class="text-red-500 mb-2">{{ t('admin.systemPage.dockerError') }}</p>
        <p class="text-sm text-gray-500">{{ dockerError }}</p>
      </div>

      <div v-else-if="dockerContainers.length">
        <!-- Current stats cards -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          <div
            v-for="name in dockerContainers"
            :key="name"
            class="border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-center"
          >
            <div class="flex items-center justify-center gap-1.5 mb-2">
              <span class="w-2 h-2 rounded-full" :class="getContainerStatus(name) === 'running' ? 'bg-green-500' : 'bg-gray-400'" />
              <span class="text-xs font-medium text-gray-900 dark:text-white truncate">{{ shortName(name) }}</span>
            </div>
            <div class="text-lg font-bold" :class="cpuColor(getContainerCpu(name))">
              {{ getContainerCpu(name).toFixed(1) }}%
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">CPU</div>
            <div class="text-sm font-semibold text-gray-900 dark:text-white mt-1">
              {{ formatBytes(getContainerMem(name)) }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ t('admin.systemPage.memory') }}</div>
          </div>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">CPU %</h3>
            <div class="h-64">
              <canvas ref="cpuChartRef" />
            </div>
          </div>
          <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">{{ t('admin.systemPage.memory') }} (MB)</h3>
            <div class="h-64">
              <canvas ref="memChartRef" />
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8 text-gray-500">
        {{ t('admin.systemPage.dockerNoData') }}
      </div>

      <!-- Last updated -->
      <div v-if="lastUpdated" class="mt-4 text-xs text-gray-400 text-right">
        {{ t('admin.systemPage.lastUpdated') }}: {{ lastUpdated }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, h, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDateFormat } from '../../utils/date'
import api from '../../api'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const { t } = useI18n()
const { formatDateTime } = useDateFormat()

// ── State ────────────────────────────────────────

const status = ref(null)
const statusLoading = ref(false)
const statusError = ref(null)

const dockerContainers = ref([])
const dockerLatest = ref(null)
const dockerHistory = ref({})
const dockerLoading = ref(false)
const dockerError = ref(null)
const chartPeriod = ref(120)

const lastUpdated = ref(null)
let refreshTimer = null

const cpuChartRef = ref(null)
const memChartRef = ref(null)
let cpuChart = null
let memChart = null

// ── Inline sub-components ────────────────────────

const MetricRow = (props) => {
  const valueClass = props.ok === true
    ? 'text-green-600 dark:text-green-400 font-medium'
    : props.ok === false
      ? 'text-red-600 dark:text-red-400 font-medium'
      : 'text-gray-900 dark:text-white'
  const sizeClass = props.small ? ' text-xs' : ''
  return h('div', { class: 'flex justify-between' }, [
    h('span', { class: 'text-gray-500 dark:text-gray-400' }, props.label),
    h('span', { class: valueClass + sizeClass }, props.value ?? '-'),
  ])
}
MetricRow.props = ['label', 'value', 'ok', 'small']

const ProgressBar = (props) => {
  const pct = Math.min(props.percent ?? 0, 100)
  const barColor = pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-yellow-500' : 'bg-green-500'
  return h('div', { class: 'w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5' }, [
    h('div', {
      class: `${barColor} h-1.5 rounded-full transition-all duration-500`,
      style: { width: `${pct}%` },
    }),
  ])
}
ProgressBar.props = ['percent']

// ── Links ────────────────────────────────────────

const links = computed(() => [
  {
    label: 'Swagger UI',
    description: t('admin.systemPage.linkSwagger'),
    url: '/api/docs',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    bgClass: 'bg-green-100 dark:bg-green-900/30',
    iconClass: 'text-green-600 dark:text-green-400',
  },
  {
    label: 'ReDoc',
    description: t('admin.systemPage.linkRedoc'),
    url: '/api/redoc',
    icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
    bgClass: 'bg-blue-100 dark:bg-blue-900/30',
    iconClass: 'text-blue-600 dark:text-blue-400',
  },
  {
    label: t('admin.systemPage.linkDocsLabel'),
    description: t('admin.systemPage.linkDocs'),
    url: '/docs/',
    icon: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
    bgClass: 'bg-purple-100 dark:bg-purple-900/30',
    iconClass: 'text-purple-600 dark:text-purple-400',
  },
  {
    label: 'Health Check',
    description: t('admin.systemPage.linkHealth'),
    url: '/api/health',
    icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    bgClass: 'bg-red-100 dark:bg-red-900/30',
    iconClass: 'text-red-600 dark:text-red-400',
  },
  {
    label: 'pgAdmin',
    description: t('admin.systemPage.linkPgAdmin'),
    url: 'http://localhost:5050',
    icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
    bgClass: 'bg-yellow-100 dark:bg-yellow-900/30',
    iconClass: 'text-yellow-600 dark:text-yellow-400',
  },
  {
    label: 'Redis Insight',
    description: t('admin.systemPage.linkRedis'),
    url: 'http://localhost:8001',
    icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
    bgClass: 'bg-orange-100 dark:bg-orange-900/30',
    iconClass: 'text-orange-600 dark:text-orange-400',
  },
])

// ── Chart colors ─────────────────────────────────

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899',
  '#06b6d4', '#84cc16', '#f97316', '#6366f1',
]

// ── Data loading ─────────────────────────────────

async function loadStatus() {
  statusLoading.value = true
  statusError.value = null
  try {
    const { data } = await api.get('/admin/system/status')
    status.value = data
  } catch (e) {
    statusError.value = e.response?.data?.detail || e.message
  } finally {
    statusLoading.value = false
  }
}

async function loadDockerStats() {
  try {
    const { data } = await api.get('/admin/system/docker-stats')
    if (data.latest) {
      dockerLatest.value = data.latest
    }
    if (data.containers?.length) {
      dockerContainers.value = data.containers
    }
  } catch (e) {
    dockerError.value = e.response?.data?.detail || e.message
  }
}

async function loadDockerHistory() {
  if (!dockerContainers.value.length) return

  dockerLoading.value = true
  try {
    const promises = dockerContainers.value.map(async (name) => {
      const { data } = await api.get(`/admin/system/docker-stats/${encodeURIComponent(name)}`, {
        params: { count: chartPeriod.value },
      })
      return { name, points: data.points }
    })
    const results = await Promise.all(promises)
    const hist = {}
    for (const r of results) {
      hist[r.name] = r.points
    }
    dockerHistory.value = hist

    await nextTick()
    renderCharts()
  } catch (e) {
    dockerError.value = e.response?.data?.detail || e.message
  } finally {
    dockerLoading.value = false
  }
}

async function loadAll() {
  await Promise.all([loadStatus(), loadDockerStats()])
  if (dockerContainers.value.length) {
    await loadDockerHistory()
  }
  lastUpdated.value = formatDateTime(new Date().toISOString())
}

// ── Charts ───────────────────────────────────────

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

function renderCharts() {
  const dark = isDarkMode()
  const gridColor = dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
  const textColor = dark ? '#9ca3af' : '#6b7280'

  const containers = dockerContainers.value
  const history = dockerHistory.value

  // Build time labels from first container with data
  let timeLabels = []
  for (const name of containers) {
    if (history[name]?.length) {
      timeLabels = history[name].map(p => {
        const d = new Date(p.ts * 1000)
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      })
      break
    }
  }

  if (!timeLabels.length) return

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        labels: { color: textColor, usePointStyle: true, pointStyle: 'circle', padding: 16, font: { size: 11 } },
      },
    },
    scales: {
      x: {
        ticks: { color: textColor, maxTicksLimit: 8, font: { size: 10 } },
        grid: { color: gridColor },
      },
      y: {
        ticks: { color: textColor, font: { size: 10 } },
        grid: { color: gridColor },
        beginAtZero: true,
      },
    },
  }

  // CPU Chart
  const cpuDatasets = containers.map((name, i) => ({
    label: shortName(name),
    data: (history[name] || []).map(p => p.cpu),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: COLORS[i % COLORS.length] + '20',
    borderWidth: 1.5,
    pointRadius: 0,
    tension: 0.3,
    fill: false,
  }))

  if (cpuChart) cpuChart.destroy()
  if (cpuChartRef.value) {
    cpuChart = new Chart(cpuChartRef.value, {
      type: 'line',
      data: { labels: timeLabels, datasets: cpuDatasets },
      options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, title: { display: true, text: '%', color: textColor } } } },
    })
  }

  // Memory Chart
  const memDatasets = containers.map((name, i) => ({
    label: shortName(name),
    data: (history[name] || []).map(p => +(p.mem_used / 1024 / 1024).toFixed(1)),
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: COLORS[i % COLORS.length] + '20',
    borderWidth: 1.5,
    pointRadius: 0,
    tension: 0.3,
    fill: false,
  }))

  if (memChart) memChart.destroy()
  if (memChartRef.value) {
    memChart = new Chart(memChartRef.value, {
      type: 'line',
      data: { labels: timeLabels, datasets: memDatasets },
      options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, title: { display: true, text: 'MB', color: textColor } } } },
    })
  }
}

// ── Helpers ───────────────────────────────────────

function getContainerStatus(name) {
  return dockerLatest.value?.containers?.[name]?.status || 'unknown'
}
function getContainerCpu(name) {
  return dockerLatest.value?.containers?.[name]?.cpu_percent || 0
}
function getContainerMem(name) {
  return dockerLatest.value?.containers?.[name]?.memory_used || 0
}

function shortName(name) {
  // "aibek-backend-1" → "backend"
  return name.replace(/^aibek-/, '').replace(/-\d+$/, '')
}

function cpuColor(pct) {
  if (pct > 80) return 'text-red-600 dark:text-red-400'
  if (pct > 50) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
}

function formatBytes(b) {
  if (!b) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let val = b
  while (val >= 1024 && i < units.length - 1) { val /= 1024; i++ }
  return `${val.toFixed(1)} ${units[i]}`
}

function formatUptime(seconds) {
  if (!seconds && seconds !== 0) return '-'
  const d = Math.floor(seconds / 86400)
  const hrs = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  const parts = []
  if (d > 0) parts.push(`${d}d`)
  if (hrs > 0) parts.push(`${hrs}h`)
  if (m > 0) parts.push(`${m}m`)
  parts.push(`${s}s`)
  return parts.join(' ')
}

function formatTimestamp(ts) {
  if (!ts) return '-'
  return formatDateTime(ts)
}

function shortenPgVersion(version) {
  if (!version) return '-'
  const match = version.match(/PostgreSQL ([\d.]+)/)
  return match ? `PostgreSQL ${match[1]}` : version.substring(0, 40)
}

function formatNumber(n) {
  if (n === undefined || n === null) return '-'
  return n.toLocaleString()
}

// ── Lifecycle ────────────────────────────────────

onMounted(async () => {
  await loadAll()
  // Auto-refresh every 10 seconds
  refreshTimer = setInterval(async () => {
    await loadDockerStats()
    await loadDockerHistory()
    lastUpdated.value = formatDateTime(new Date().toISOString())
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (cpuChart) cpuChart.destroy()
  if (memChart) memChart.destroy()
})
</script>
