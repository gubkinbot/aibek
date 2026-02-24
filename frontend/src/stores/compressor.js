import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useCompressorStore = defineStore('compressor', () => {
  const stations = ref([])
  const currentStation = ref(null)
  const tags = ref([])
  const computedTags = ref([])
  const realtimeData = ref(null)
  const stationStatus = ref(null)
  const alarmRules = ref([])
  const anomalyRules = ref([])
  const alarms = ref({ items: [], total: 0, page: 1, per_page: 50, pages: 1 })
  const anomalies = ref({ items: [], total: 0, page: 1, per_page: 50, pages: 1 })
  const loading = ref(false)

  const BASE = '/modules/compressor'

  // ── Станции ──────────────────────────────────────────────

  async function fetchStations() {
    loading.value = true
    try {
      const { data } = await api.get(`${BASE}/stations`)
      stations.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchStation(code) {
    const { data } = await api.get(`${BASE}/stations/${code}`)
    currentStation.value = data
    return data
  }

  async function createStation(body) {
    const { data } = await api.post(`${BASE}/stations`, body)
    stations.value.push(data)
    return data
  }

  async function updateStation(code, body) {
    const { data } = await api.patch(`${BASE}/stations/${code}`, body)
    const idx = stations.value.findIndex(s => s.code === code)
    if (idx !== -1) stations.value[idx] = data
    if (currentStation.value?.code === code) currentStation.value = data
    return data
  }

  async function deleteStation(code) {
    await api.delete(`${BASE}/stations/${code}`)
    stations.value = stations.value.filter(s => s.code !== code)
    if (currentStation.value?.code === code) currentStation.value = null
  }

  async function generateCert(code) {
    const { data } = await api.post(`${BASE}/stations/${code}/generate-cert`)
    return data
  }

  async function downloadCert(code) {
    const { data } = await api.get(`${BASE}/stations/${code}/download-cert`, { responseType: 'blob' })
    return data
  }

  async function fetchStationStatus(code) {
    const { data } = await api.get(`${BASE}/stations/${code}/status`)
    stationStatus.value = data
    return data
  }

  // ── Теги ─────────────────────────────────────────────────

  async function fetchTags(code) {
    const { data } = await api.get(`${BASE}/stations/${code}/tags`)
    tags.value = data
    return data
  }

  async function createTag(code, body) {
    const { data } = await api.post(`${BASE}/stations/${code}/tags`, body)
    tags.value.push(data)
    return data
  }

  async function importTagsExcel(code, file) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(`${BASE}/stations/${code}/tags/import-excel`, form)
    return data
  }

  async function downloadTagsTemplate() {
    const { data } = await api.get(`${BASE}/tags/template-excel`, { responseType: 'blob' })
    return data
  }

  async function importHistoryExcel(code, file) {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post(`${BASE}/stations/${code}/history/import-excel`, form)
    return data
  }

  async function downloadHistoryTemplate() {
    const { data } = await api.get(`${BASE}/history/template-excel`, { responseType: 'blob' })
    return data
  }

  async function updateTag(tagId, body) {
    const { data } = await api.patch(`${BASE}/tags/${tagId}`, body)
    const idx = tags.value.findIndex(t => t.id === tagId)
    if (idx !== -1) tags.value[idx] = data
    return data
  }

  async function deleteTag(tagId) {
    await api.delete(`${BASE}/tags/${tagId}`)
    tags.value = tags.value.filter(t => t.id !== tagId)
  }

  // ── Вычисляемые теги ─────────────────────────────────────

  async function fetchComputedTags(code) {
    const { data } = await api.get(`${BASE}/stations/${code}/computed-tags`)
    computedTags.value = data
    return data
  }

  async function createComputedTag(code, body) {
    const { data } = await api.post(`${BASE}/stations/${code}/computed-tags`, body)
    computedTags.value.push(data)
    return data
  }

  async function updateComputedTag(ctId, body) {
    const { data } = await api.patch(`${BASE}/computed-tags/${ctId}`, body)
    const idx = computedTags.value.findIndex(c => c.id === ctId)
    if (idx !== -1) computedTags.value[idx] = data
    return data
  }

  async function deleteComputedTag(ctId) {
    await api.delete(`${BASE}/computed-tags/${ctId}`)
    computedTags.value = computedTags.value.filter(c => c.id !== ctId)
  }

  // ── Данные ───────────────────────────────────────────────

  async function fetchRealtime(code) {
    const { data } = await api.get(`${BASE}/stations/${code}/realtime`)
    realtimeData.value = data
    return data
  }

  async function fetchHistory(code, params) {
    const { data } = await api.get(`${BASE}/stations/${code}/history`, { params })
    return data
  }

  // ── Аварии ───────────────────────────────────────────────

  async function fetchAlarmRules(code) {
    const { data } = await api.get(`${BASE}/stations/${code}/alarm-rules`)
    alarmRules.value = data
    return data
  }

  async function createAlarmRule(code, body) {
    const { data } = await api.post(`${BASE}/stations/${code}/alarm-rules`, body)
    alarmRules.value.push(data)
    return data
  }

  async function updateAlarmRule(ruleId, body) {
    const { data } = await api.patch(`${BASE}/alarm-rules/${ruleId}`, body)
    const idx = alarmRules.value.findIndex(r => r.id === ruleId)
    if (idx !== -1) alarmRules.value[idx] = data
    return data
  }

  async function deleteAlarmRule(ruleId) {
    await api.delete(`${BASE}/alarm-rules/${ruleId}`)
    alarmRules.value = alarmRules.value.filter(r => r.id !== ruleId)
  }

  async function fetchAlarms(code, params = {}) {
    const { data } = await api.get(`${BASE}/stations/${code}/alarms`, { params })
    alarms.value = data
    return data
  }

  async function acknowledgeAlarm(time, stationId) {
    await api.post(`${BASE}/alarms/acknowledge`, null, { params: { time, station_id: stationId } })
  }

  // ── Аномалии ─────────────────────────────────────────────

  async function fetchAnomalyRules(code) {
    const { data } = await api.get(`${BASE}/stations/${code}/anomaly-rules`)
    anomalyRules.value = data
    return data
  }

  async function createAnomalyRule(code, body) {
    const { data } = await api.post(`${BASE}/stations/${code}/anomaly-rules`, body)
    anomalyRules.value.push(data)
    return data
  }

  async function updateAnomalyRule(ruleId, body) {
    const { data } = await api.patch(`${BASE}/anomaly-rules/${ruleId}`, body)
    const idx = anomalyRules.value.findIndex(r => r.id === ruleId)
    if (idx !== -1) anomalyRules.value[idx] = data
    return data
  }

  async function deleteAnomalyRule(ruleId) {
    await api.delete(`${BASE}/anomaly-rules/${ruleId}`)
    anomalyRules.value = anomalyRules.value.filter(r => r.id !== ruleId)
  }

  async function fetchAnomalies(code, params = {}) {
    const { data } = await api.get(`${BASE}/stations/${code}/anomalies`, { params })
    anomalies.value = data
    return data
  }

  async function acknowledgeAnomaly(time, stationId) {
    await api.post(`${BASE}/anomalies/acknowledge`, null, { params: { time, station_id: stationId } })
  }

  // ── Обновление из WebSocket ──────────────────────────────

  function handleWsMessage(msg) {
    if (msg.type === 'realtime') {
      realtimeData.value = msg
    } else if (msg.type === 'alarm') {
      alarms.value.items.unshift(msg)
      alarms.value.total++
    } else if (msg.type === 'anomaly') {
      anomalies.value.items.unshift(msg)
      anomalies.value.total++
    }
  }

  return {
    stations, currentStation, tags, computedTags, realtimeData,
    stationStatus, alarmRules, anomalyRules, alarms, anomalies, loading,
    fetchStations, fetchStation, createStation, updateStation, deleteStation,
    generateCert, downloadCert,
    fetchStationStatus, fetchTags, createTag,
    importTagsExcel, downloadTagsTemplate,
    importHistoryExcel, downloadHistoryTemplate,
    updateTag, deleteTag, fetchComputedTags, createComputedTag, updateComputedTag,
    deleteComputedTag, fetchRealtime, fetchHistory, fetchAlarmRules, createAlarmRule,
    updateAlarmRule, deleteAlarmRule, fetchAlarms, acknowledgeAlarm,
    fetchAnomalyRules, createAnomalyRule, updateAnomalyRule, deleteAnomalyRule,
    fetchAnomalies, acknowledgeAnomaly, handleWsMessage,
  }
})
