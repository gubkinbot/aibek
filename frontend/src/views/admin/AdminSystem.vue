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

    <!-- Virtual Server -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('admin.systemPage.virtualServer') }}</h2>
          <span v-if="status?.backend" class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium"
            :class="status.backend.status === 'ok' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'">
            <span class="w-1.5 h-1.5 rounded-full" :class="status.backend.status === 'ok' ? 'bg-green-500' : 'bg-red-500'" />
            {{ status.backend.status === 'ok' ? 'Online' : 'Offline' }}
          </span>
        </div>
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

      <div v-else-if="status?.backend">
        <!-- Uptime & Server time -->
        <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-500 dark:text-gray-400 mb-5">
          <span>{{ t('admin.systemPage.uptime') }}: <span class="text-gray-900 dark:text-white font-medium">{{ formatUptime(status.backend.uptime_seconds) }}</span></span>
          <span>{{ t('admin.systemPage.serverTime') }}: <span class="text-gray-900 dark:text-white font-medium">{{ formatTimestamp(status.backend.timestamp) }}</span></span>
        </div>

        <!-- CPU / Memory / Disk cards with sparklines -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- CPU -->
          <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-900 dark:text-white">CPU</span>
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                :class="status.backend.cpu_percent > 80
                  ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  : status.backend.cpu_percent > 50
                    ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                    : 'bg-blue-50 text-blue-700 dark:bg-blue-900/25 dark:text-blue-400'">
                {{ status.backend.cpu_percent ?? '-' }}%
              </span>
            </div>
            <div class="flex-1 min-h-[4rem]">
              <canvas ref="serverCpuRef" />
            </div>
          </div>
          <!-- Memory -->
          <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-900 dark:text-white">{{ t('admin.systemPage.memory') }}</span>
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-violet-50 text-violet-700 dark:bg-violet-900/25 dark:text-violet-400">
                {{ status.backend.memory_used_fmt }} / {{ status.backend.memory_total_fmt }}
              </span>
            </div>
            <div class="flex-1 min-h-[4rem]">
              <canvas ref="serverMemRef" />
            </div>
          </div>
          <!-- Disk -->
          <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-900 dark:text-white">{{ t('admin.systemPage.disk') }}</span>
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                {{ status.backend.disk_used_fmt }} / {{ status.backend.disk_total_fmt }}
              </span>
            </div>
            <div class="flex-1 min-h-[4rem]">
              <canvas ref="serverDiskRef" />
            </div>
          </div>
        </div>

        <!-- Process memory footer -->
        <div class="mt-3 text-xs text-gray-400 dark:text-gray-500">
          {{ t('admin.systemPage.processMemory') }} (FastAPI): {{ status.backend.process_memory_fmt }}
        </div>
      </div>
    </div>

    <!-- Services -->
    <div v-if="status" class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- PostgreSQL -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
        <div class="flex items-center gap-2 mb-4">
          <span class="w-2.5 h-2.5 rounded-full" :class="status.database?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'" />
          <h3 class="font-semibold text-gray-900 dark:text-white">PostgreSQL</h3>
          <span class="text-xs text-gray-400 dark:text-gray-500 ml-auto">{{ shortenPgVersion(status.database?.version) }}</span>
        </div>
        <div v-if="status.database?.error" class="text-red-500 text-sm">{{ status.database.error }}</div>
        <div v-else class="space-y-3 text-sm">
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
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
        <div class="flex items-center gap-2 mb-4">
          <span class="w-2.5 h-2.5 rounded-full" :class="status.redis?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'" />
          <h3 class="font-semibold text-gray-900 dark:text-white">Redis</h3>
          <span class="text-xs text-gray-400 dark:text-gray-500 ml-auto">v{{ status.redis?.version }}</span>
        </div>
        <div v-if="status.redis?.error" class="text-red-500 text-sm">{{ status.redis.error }}</div>
        <div v-else class="space-y-3 text-sm">
          <MetricRow :label="t('admin.systemPage.memory')" :value="status.redis?.memory_used_fmt" />
          <MetricRow :label="t('admin.systemPage.keys')" :value="status.redis?.keys_count" />
          <MetricRow :label="t('admin.systemPage.clients')" :value="status.redis?.connected_clients" />
          <MetricRow :label="t('admin.systemPage.commands')" :value="formatNumber(status.redis?.total_commands)" />
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
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="(name, idx) in dockerContainers"
            :key="name"
            class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col"
          >
            <div class="flex items-center justify-between mb-3">
              <!-- Name -->
              <div class="flex items-center gap-2 min-w-0">
                <span class="w-2 h-2 rounded-full shrink-0" :class="getContainerStatus(name) === 'running' ? 'bg-green-500' : 'bg-gray-400'" />
                <span class="font-medium text-gray-900 dark:text-white truncate">{{ shortName(name) }}</span>
              </div>
              <!-- Badges (colors match sparkline lines) -->
              <div class="flex items-center gap-1.5 shrink-0">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900/25 dark:text-blue-400">
                  {{ getContainerCpu(name).toFixed(1) }}% cpu
                </span>
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-violet-50 text-violet-700 dark:bg-violet-900/25 dark:text-violet-400">
                  {{ formatBytes(getContainerMem(name)) }}
                </span>
              </div>
            </div>

            <!-- Sparkline (CPU + Memory) -->
            <div class="flex-1 min-h-[5rem]">
              <canvas :ref="el => setSparkRef(el, idx)" />
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
import { ref, computed, onMounted, onUnmounted, h, nextTick } from 'vue'
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

const sparkRefs = ref([])
let sparklineCharts = []

function setSparkRef(el, idx) {
  sparkRefs.value[idx] = el
}

// Server sparklines
const serverCpuRef = ref(null)
const serverMemRef = ref(null)
const serverDiskRef = ref(null)
const serverHistory = ref([])
let serverSparklines = []

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
])

// ── Chart colors ─────────────────────────────────

const CPU_COLOR = '#3b82f6'  // blue-500
const MEM_COLOR = '#8b5cf6'  // violet-500
const DISK_COLOR = '#6b7280' // gray-500

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
    renderSparklines()
  } catch (e) {
    dockerError.value = e.response?.data?.detail || e.message
  } finally {
    dockerLoading.value = false
  }
}

async function loadServerHistory() {
  try {
    const { data } = await api.get('/admin/system/server-stats', {
      params: { count: chartPeriod.value },
    })
    serverHistory.value = data.points || []
    await nextTick()
    renderServerSparklines()
  } catch {
    // server history is supplementary, don't block UI
  }
}

async function loadAll() {
  await Promise.all([loadStatus(), loadDockerStats()])
  await Promise.all([
    loadServerHistory(),
    dockerContainers.value.length ? loadDockerHistory() : Promise.resolve(),
  ])
  lastUpdated.value = formatDateTime(new Date().toISOString())
}

// ── Sparklines ──────────────────────────────────

function formatTsLabel(label) {
  if (!label) return ''
  const d = new Date(+label * 1000)
  return d.toLocaleString([], { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function renderSparklines() {
  const containers = dockerContainers.value
  const history = dockerHistory.value

  sparklineCharts.forEach(c => c?.destroy())
  sparklineCharts = []

  containers.forEach((name, idx) => {
    const canvas = sparkRefs.value[idx]
    if (!canvas) return

    const points = history[name] || []
    if (!points.length) return

    const timestamps = points.map(p => p.ts)
    const cpuData = points.map(p => p.cpu)
    const memData = points.map(p => +(p.mem_used / 1024 / 1024).toFixed(1))

    const chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: timestamps,
        datasets: [
          {
            data: cpuData,
            borderColor: CPU_COLOR,
            backgroundColor: CPU_COLOR + '18',
            borderWidth: 1.5,
            pointRadius: 0,
            tension: 0.4,
            fill: true,
            yAxisID: 'yCpu',
          },
          {
            data: memData,
            borderColor: MEM_COLOR,
            backgroundColor: MEM_COLOR + '20',
            borderWidth: 1,
            pointRadius: 0,
            tension: 0.4,
            fill: true,
            borderDash: [3, 2],
            yAxisID: 'yMem',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 200 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            backgroundColor: 'rgba(17,24,39,0.9)',
            titleFont: { size: 10, weight: 'normal' },
            titleColor: '#9ca3af',
            bodyFont: { size: 11 },
            padding: 8,
            cornerRadius: 6,
            displayColors: true,
            boxWidth: 8,
            boxHeight: 8,
            boxPadding: 3,
            callbacks: {
              title: (items) => formatTsLabel(items[0]?.label),
              label: (ctx) => {
                if (ctx.datasetIndex === 0) return ` ${ctx.parsed.y.toFixed(1)}% cpu`
                return ` ${ctx.parsed.y.toFixed(1)} MB mem`
              },
            },
          },
        },
        scales: {
          x: { display: false },
          yCpu: { display: false, beginAtZero: true },
          yMem: { display: false, beginAtZero: true, position: 'right' },
        },
      },
    })
    sparklineCharts.push(chart)
  })
}

function renderServerSparklines() {
  serverSparklines.forEach(c => c?.destroy())
  serverSparklines = []

  const points = serverHistory.value
  if (!points.length) return

  const labels = points.map(p => p.ts)
  const sparkOpts = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 200 },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(17,24,39,0.9)',
        titleFont: { size: 10, weight: 'normal' },
        titleColor: '#9ca3af',
        bodyFont: { size: 11 },
        padding: 8,
        cornerRadius: 6,
        displayColors: false,
      },
    },
    scales: {
      x: { display: false },
      y: { display: false, beginAtZero: true },
    },
  }

  const configs = [
    { ref: serverCpuRef, data: points.map(p => p.cpu), color: CPU_COLOR, unit: '%' },
    { ref: serverMemRef, data: points.map(p => p.mem_pct), color: MEM_COLOR, unit: '%' },
    { ref: serverDiskRef, data: points.map(p => p.disk_pct), color: DISK_COLOR, unit: '%' },
  ]

  for (const cfg of configs) {
    if (!cfg.ref.value) continue
    const chart = new Chart(cfg.ref.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          data: cfg.data,
          borderColor: cfg.color,
          backgroundColor: cfg.color + '18',
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        ...sparkOpts,
        plugins: {
          ...sparkOpts.plugins,
          tooltip: {
            ...sparkOpts.plugins.tooltip,
            callbacks: {
              title: (items) => formatTsLabel(items[0]?.label),
              label: (ctx) => `${ctx.parsed.y.toFixed(1)}${cfg.unit}`,
            },
          },
        },
      },
    })
    serverSparklines.push(chart)
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
    await Promise.all([loadStatus(), loadDockerStats()])
    await Promise.all([loadServerHistory(), loadDockerHistory()])
    lastUpdated.value = formatDateTime(new Date().toISOString())
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  sparklineCharts.forEach(c => c?.destroy())
  serverSparklines.forEach(c => c?.destroy())
})
</script>
