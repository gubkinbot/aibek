<template>
  <div class="space-y-6">

    <!-- ═══ Станции ═══ -->
    <section v-if="canAdmin" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('modules.compressor.settings.stationsTitle') }}</h2>
        <button @click="openStationForm()" class="btn-primary text-sm">{{ t('modules.compressor.settings.addStation') }}</button>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200/30 dark:border-white/[0.08]">
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.stationName') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.stationCode') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.opcUrl') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.tagsCount') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.active') }}</th>
              <th class="py-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in store.stations" :key="s.id" class="border-b border-gray-100/20 dark:border-white/[0.04]">
              <td class="py-3 pr-4 text-gray-900 dark:text-white font-medium">{{ s.name }}</td>
              <td class="py-3 pr-4 text-gray-500 dark:text-gray-400 font-mono text-xs">{{ s.code }}</td>
              <td class="py-3 pr-4 text-gray-500 dark:text-gray-400 text-xs truncate max-w-[200px]">{{ s.opc_url }}</td>
              <td class="py-3 pr-4 text-gray-500 dark:text-gray-400">{{ s.tags_count }}</td>
              <td class="py-3 pr-4">
                <span :class="s.is_active ? 'text-green-500' : 'text-red-500'" class="text-xs font-medium">
                  {{ s.is_active ? 'ON' : 'OFF' }}
                </span>
              </td>
              <td class="py-3 text-right space-x-2">
                <button @click="doGenerateCert(s)" class="text-xs text-orange-500 hover:text-orange-600">{{ t('modules.compressor.settings.generateCert') }}</button>
                <button v-if="s.opc_cert_path" @click="doDownloadCert(s)" class="text-xs text-green-500 hover:text-green-600">{{ t('modules.compressor.settings.downloadCert') }}</button>
                <button @click="openStationForm(s)" class="text-xs text-blue-500 hover:text-blue-600">{{ t('admin.edit') }}</button>
                <button @click="confirmDeleteStation(s)" class="text-xs text-red-500 hover:text-red-600">{{ t('admin.delete') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ═══ Диагностика станции ═══ -->
    <section v-if="canManage && selectedCode" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('modules.compressor.settings.diagnosticsTitle') }}</h2>
        <button @click="refreshDiagnostics" class="btn-secondary text-sm flex items-center gap-1" :disabled="diagLoading">
          <svg class="w-4 h-4" :class="{ 'animate-spin': diagLoading }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          {{ t('admin.systemPage.refresh') }}
        </button>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <!-- OPC Collector -->
        <div class="p-3 rounded-lg bg-gray-100/60 dark:bg-gray-700/30 border border-gray-200/30 dark:border-white/[0.06]">
          <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">OPC Collector</div>
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full" :class="diagStatus.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></span>
            <span class="text-sm font-medium" :class="diagStatus.connected ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ diagStatus.connected ? t('modules.compressor.connected') : t('modules.compressor.disconnected') }}
            </span>
          </div>
        </div>

        <!-- Certificate -->
        <div class="p-3 rounded-lg bg-gray-100/60 dark:bg-gray-700/30 border border-gray-200/30 dark:border-white/[0.06]">
          <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">{{ t('modules.compressor.settings.generateCert') }}</div>
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full" :class="currentStationObj?.opc_cert_path ? 'bg-green-500' : 'bg-yellow-500'"></span>
            <span class="text-sm font-medium" :class="currentStationObj?.opc_cert_path ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'">
              {{ currentStationObj?.opc_cert_path ? t('modules.compressor.settings.certReady') : t('modules.compressor.settings.certMissing') }}
            </span>
          </div>
        </div>

        <!-- Tags configured -->
        <div class="p-3 rounded-lg bg-gray-100/60 dark:bg-gray-700/30 border border-gray-200/30 dark:border-white/[0.06]">
          <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">{{ t('modules.compressor.tagsCount') }}</div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            {{ store.tags.length }} {{ t('modules.compressor.settings.tagsConfigured') }}
          </div>
        </div>

        <!-- Last data -->
        <div class="p-3 rounded-lg bg-gray-100/60 dark:bg-gray-700/30 border border-gray-200/30 dark:border-white/[0.06]">
          <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">{{ t('modules.compressor.lastUpdate') }}</div>
          <div class="text-sm font-medium text-gray-900 dark:text-white">
            {{ diagStatus.last_seen ? formatTime(diagStatus.last_seen) : '—' }}
          </div>
        </div>

        <!-- Error -->
        <div v-if="diagStatus.error" class="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
          <div class="text-xs text-red-500 dark:text-red-400 mb-1">{{ t('modules.compressor.settings.lastError') }}</div>
          <div class="text-xs font-mono text-red-600 dark:text-red-400 truncate" :title="diagStatus.error">
            {{ diagStatus.error }}
          </div>
        </div>
      </div>

      <!-- Checklist hints -->
      <div v-if="diagHints.length" class="mt-4 space-y-1.5">
        <div v-for="(hint, i) in diagHints" :key="i" class="flex items-start gap-2 text-xs">
          <span class="mt-0.5 w-4 h-4 rounded-full flex items-center justify-center shrink-0" :class="hint.type === 'ok' ? 'bg-green-500/20 text-green-600' : hint.type === 'warn' ? 'bg-yellow-500/20 text-yellow-600' : 'bg-red-500/20 text-red-600'">
            <svg v-if="hint.type === 'ok'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
            <svg v-else class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01" /></svg>
          </span>
          <span :class="hint.type === 'ok' ? 'text-gray-500 dark:text-gray-400' : hint.type === 'warn' ? 'text-yellow-700 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'">{{ hint.text }}</span>
        </div>
      </div>
    </section>

    <!-- ═══ Теги ═══ -->
    <section v-if="canManage && selectedCode" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('modules.compressor.settings.tagsTitle') }}</h2>
        <div class="flex gap-2">
          <button @click="doDownloadTagsTemplate" class="btn-secondary text-sm flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            {{ t('modules.compressor.settings.downloadTemplate') }}
          </button>
          <label class="btn-secondary text-sm cursor-pointer">
            {{ t('modules.compressor.settings.importExcel') }}
            <input type="file" accept=".xlsx" class="hidden" @change="handleImportTags" />
          </label>
          <button @click="openTagForm()" class="btn-primary text-sm">{{ t('modules.compressor.settings.addTag') }}</button>
        </div>
      </div>

      <!-- Import result -->
      <div v-if="importResult" class="mb-4 p-3 rounded-lg bg-blue-500/10 text-sm text-blue-700 dark:text-blue-300">
        {{ t('modules.compressor.importResult') }}:
        {{ t('modules.compressor.created') }}: {{ importResult.created }},
        {{ t('modules.compressor.skipped') }}: {{ importResult.skipped }}
        <span v-if="importResult.errors?.length">, {{ t('modules.compressor.errors') }}: {{ importResult.errors.length }}</span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200/30 dark:border-white/[0.08]">
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.tagName') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.opcPath') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.unit') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.category') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.validMin') }}</th>
              <th class="py-2 pr-4">{{ t('modules.compressor.settings.validMax') }}</th>
              <th class="py-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tag in store.tags" :key="tag.id" class="border-b border-gray-100/20 dark:border-white/[0.04]">
              <td class="py-2 pr-4 text-gray-900 dark:text-white">{{ tag.name }}</td>
              <td class="py-2 pr-4 text-gray-500 dark:text-gray-400 font-mono text-xs">{{ tag.opc_path }}</td>
              <td class="py-2 pr-4 text-gray-500 dark:text-gray-400">{{ tag.unit || '—' }}</td>
              <td class="py-2 pr-4 text-gray-500 dark:text-gray-400">{{ tag.category || '—' }}</td>
              <td class="py-2 pr-4 text-gray-500 dark:text-gray-400">{{ tag.valid_min ?? '—' }}</td>
              <td class="py-2 pr-4 text-gray-500 dark:text-gray-400">{{ tag.valid_max ?? '—' }}</td>
              <td class="py-2 text-right space-x-2">
                <button @click="openTagForm(tag)" class="text-xs text-blue-500 hover:text-blue-600">{{ t('admin.edit') }}</button>
                <button @click="doDeleteTag(tag)" class="text-xs text-red-500 hover:text-red-600">{{ t('admin.delete') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="store.tags.length === 0" class="text-center text-gray-400 py-4 text-sm">{{ t('modules.compressor.noData') }}</p>
      </div>
    </section>

    <!-- ═══ Вычисляемые теги ═══ -->
    <section v-if="canManage && selectedCode" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('modules.compressor.settings.computedTitle') }}</h2>
        <button @click="openComputedForm()" class="btn-primary text-sm">{{ t('modules.compressor.settings.addComputed') }}</button>
      </div>

      <div v-for="ct in store.computedTags" :key="ct.id" class="flex items-center justify-between py-2 border-b border-gray-100/20 dark:border-white/[0.04]">
        <div>
          <span class="text-gray-900 dark:text-white text-sm font-medium">{{ ct.name }}</span>
          <span class="ml-2 text-xs text-gray-400 font-mono">{{ ct.compute_type }}</span>
          <span v-if="ct.category" class="ml-2 text-xs text-gray-400">{{ ct.category }}</span>
        </div>
        <div class="space-x-2">
          <button @click="openComputedForm(ct)" class="text-xs text-blue-500 hover:text-blue-600">{{ t('admin.edit') }}</button>
          <button @click="doDeleteComputed(ct)" class="text-xs text-red-500 hover:text-red-600">{{ t('admin.delete') }}</button>
        </div>
      </div>
      <p v-if="store.computedTags.length === 0" class="text-center text-gray-400 py-4 text-sm">{{ t('modules.compressor.noData') }}</p>
    </section>

    <!-- ═══ Правила аварий ═══ -->
    <section v-if="canManage && selectedCode" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('modules.compressor.settings.alarmRulesTitle') }}</h2>
        <button @click="openAlarmRuleForm()" class="btn-primary text-sm">{{ t('modules.compressor.settings.addAlarmRule') }}</button>
      </div>

      <div v-for="rule in store.alarmRules" :key="rule.id" class="flex items-center justify-between py-2 border-b border-gray-100/20 dark:border-white/[0.04]">
        <div class="flex items-center gap-3">
          <span :class="severityDot(rule.severity)"></span>
          <span class="text-gray-900 dark:text-white text-sm">{{ rule.name }}</span>
          <span class="text-xs text-gray-400 font-mono">{{ rule.condition }} {{ rule.threshold }}</span>
        </div>
        <div class="space-x-2">
          <button @click="openAlarmRuleForm(rule)" class="text-xs text-blue-500 hover:text-blue-600">{{ t('admin.edit') }}</button>
          <button @click="doDeleteAlarmRule(rule)" class="text-xs text-red-500 hover:text-red-600">{{ t('admin.delete') }}</button>
        </div>
      </div>
      <p v-if="store.alarmRules.length === 0" class="text-center text-gray-400 py-4 text-sm">{{ t('modules.compressor.noData') }}</p>
    </section>

    <!-- ═══ Правила аномалий ═══ -->
    <section v-if="canManage && selectedCode" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('modules.compressor.settings.anomalyRulesTitle') }}</h2>
        <button @click="openAnomalyRuleForm()" class="btn-primary text-sm">{{ t('modules.compressor.settings.addAnomalyRule') }}</button>
      </div>

      <div v-for="rule in store.anomalyRules" :key="rule.id" class="flex items-center justify-between py-2 border-b border-gray-100/20 dark:border-white/[0.04]">
        <div class="flex items-center gap-3">
          <span :class="severityDot(rule.severity)"></span>
          <span class="text-gray-900 dark:text-white text-sm">{{ rule.name }}</span>
          <span class="text-xs text-gray-400 font-mono">{{ rule.detector_type }}</span>
        </div>
        <div class="space-x-2">
          <button @click="openAnomalyRuleForm(rule)" class="text-xs text-blue-500 hover:text-blue-600">{{ t('admin.edit') }}</button>
          <button @click="doDeleteAnomalyRule(rule)" class="text-xs text-red-500 hover:text-red-600">{{ t('admin.delete') }}</button>
        </div>
      </div>
      <p v-if="store.anomalyRules.length === 0" class="text-center text-gray-400 py-4 text-sm">{{ t('modules.compressor.noData') }}</p>
    </section>

    <!-- ═══ Импорт истории ═══ -->
    <section v-if="canManage && selectedCode" class="glass-card p-6">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('modules.compressor.importHistory') }}</h2>
        <div class="flex gap-2">
          <button @click="doDownloadHistoryTemplate" class="btn-secondary text-sm flex items-center gap-1">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            {{ t('modules.compressor.settings.downloadTemplate') }}
          </button>
          <label class="btn-secondary text-sm cursor-pointer">
            {{ importingHistory ? t('modules.compressor.settings.importing') : t('modules.compressor.settings.importExcel') }}
            <input type="file" accept=".xlsx" class="hidden" @change="handleImportHistory" :disabled="importingHistory" />
          </label>
        </div>
      </div>

      <div v-if="historyImportResult" class="mt-3 p-3 rounded-lg bg-blue-500/10 text-sm text-blue-700 dark:text-blue-300">
        {{ t('modules.compressor.importResult') }}:
        {{ t('modules.compressor.imported') }}: {{ historyImportResult.imported }},
        {{ t('modules.compressor.skipped') }}: {{ historyImportResult.skipped }}
        <span v-if="historyImportResult.errors?.length">, {{ t('modules.compressor.errors') }}: {{ historyImportResult.errors.length }}</span>
      </div>
    </section>

    <!-- ═══ Модальное окно: Станция ═══ -->
    <Teleport to="body">
      <div v-if="showStationModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showStationModal = false">
        <div class="glass-card p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {{ stationForm.id ? t('modules.compressor.settings.editStation') : t('modules.compressor.settings.addStation') }}
          </h3>
          <form @submit.prevent="saveStation" class="space-y-3">
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.stationName') }}</label>
              <input v-model="stationForm.name" :placeholder="t('modules.compressor.settings.stationNamePlaceholder')" class="form-input" required />
            </div>
            <div v-if="!stationForm.id">
              <label class="form-label">{{ t('modules.compressor.settings.stationCode') }}</label>
              <input v-model="stationForm.code" :placeholder="t('modules.compressor.settings.stationCodePlaceholder')" class="form-input font-mono" required pattern="^[a-z0-9_-]+$" />
            </div>
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.opcUrl') }}</label>
              <input v-model="stationForm.opc_url" :placeholder="t('modules.compressor.settings.opcUrlPlaceholder')" class="form-input font-mono" required />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.securityPolicy') }}</label>
                <select v-model="stationForm.opc_security_policy" class="form-input">
                  <option value="None">None</option>
                  <option value="Basic128Rsa15">Basic128Rsa15</option>
                  <option value="Basic256">Basic256</option>
                  <option value="Basic256Sha256">Basic256Sha256</option>
                </select>
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.securityMode') }}</label>
                <select v-model="stationForm.opc_security_mode" class="form-input">
                  <option value="None">None</option>
                  <option value="Sign">Sign</option>
                  <option value="SignAndEncrypt">SignAndEncrypt</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.pollingInterval') }}</label>
                <input v-model.number="stationForm.polling_interval" type="number" min="10" class="form-input" />
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.realtimeInterval') }}</label>
                <input v-model.number="stationForm.realtime_interval" type="number" min="1" class="form-input" />
              </div>
            </div>
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.description') }}</label>
              <textarea v-model="stationForm.description" class="form-input" rows="2"></textarea>
            </div>
            <label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input v-model="stationForm.is_active" type="checkbox" class="rounded" />
              {{ t('modules.compressor.settings.active') }}
            </label>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" @click="showStationModal = false" class="btn-secondary text-sm">{{ t('modules.compressor.settings.cancel') }}</button>
              <button type="submit" :disabled="saving" class="btn-primary text-sm">{{ saving ? t('modules.compressor.settings.saving') : t('modules.compressor.settings.save') }}</button>
            </div>
            <p v-if="formError" class="text-red-500 text-sm">{{ formError }}</p>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Модальное окно: Тег ═══ -->
    <Teleport to="body">
      <div v-if="showTagModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showTagModal = false">
        <div class="glass-card p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {{ tagForm.id ? t('modules.compressor.settings.editTag') : t('modules.compressor.settings.addTag') }}
          </h3>
          <form @submit.prevent="saveTag" class="space-y-3">
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.opcPath') }}</label>
              <input v-model="tagForm.opc_path" :placeholder="t('modules.compressor.settings.opcPathPlaceholder')" class="form-input font-mono" required />
            </div>
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.tagName') }}</label>
              <input v-model="tagForm.name" :placeholder="t('modules.compressor.settings.tagNamePlaceholder')" class="form-input" required />
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.unit') }}</label>
                <input v-model="tagForm.unit" :placeholder="t('modules.compressor.settings.unitPlaceholder')" class="form-input" />
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.category') }}</label>
                <input v-model="tagForm.category" class="form-input" />
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.dataType') }}</label>
                <input v-model="tagForm.data_type" class="form-input" placeholder="Float" />
              </div>
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.validMin') }}</label>
                <input v-model.number="tagForm.valid_min" type="number" step="any" class="form-input" />
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.validMax') }}</label>
                <input v-model.number="tagForm.valid_max" type="number" step="any" class="form-input" />
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.staleTimeout') }}</label>
                <input v-model.number="tagForm.stale_timeout" type="number" class="form-input" />
              </div>
            </div>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" @click="showTagModal = false" class="btn-secondary text-sm">{{ t('modules.compressor.settings.cancel') }}</button>
              <button type="submit" :disabled="saving" class="btn-primary text-sm">{{ saving ? t('modules.compressor.settings.saving') : t('modules.compressor.settings.save') }}</button>
            </div>
            <p v-if="formError" class="text-red-500 text-sm">{{ formError }}</p>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Модальное окно: Вычисляемый тег ═══ -->
    <Teleport to="body">
      <div v-if="showComputedModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showComputedModal = false">
        <div class="glass-card p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">{{ t('modules.compressor.settings.computedTitle') }}</h3>
          <form @submit.prevent="saveComputed" class="space-y-3">
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.tagName') }}</label>
              <input v-model="computedForm.name" class="form-input" required />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.computeType') }}</label>
                <select v-model="computedForm.compute_type" class="form-input" required>
                  <option value="status_map">status_map</option>
                  <option value="formula">formula</option>
                </select>
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.category') }}</label>
                <input v-model="computedForm.category" class="form-input" />
              </div>
            </div>
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.config') }}</label>
              <textarea v-model="computedForm.configJson" class="form-input font-mono text-xs" rows="8" required></textarea>
            </div>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" @click="showComputedModal = false" class="btn-secondary text-sm">{{ t('modules.compressor.settings.cancel') }}</button>
              <button type="submit" :disabled="saving" class="btn-primary text-sm">{{ saving ? t('modules.compressor.settings.saving') : t('modules.compressor.settings.save') }}</button>
            </div>
            <p v-if="formError" class="text-red-500 text-sm">{{ formError }}</p>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Модальное окно: Правило аварии ═══ -->
    <Teleport to="body">
      <div v-if="showAlarmRuleModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showAlarmRuleModal = false">
        <div class="glass-card p-6 w-full max-w-md mx-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">{{ t('modules.compressor.settings.alarmRulesTitle') }}</h3>
          <form @submit.prevent="saveAlarmRule" class="space-y-3">
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.tagName') }}</label>
              <input v-model="alarmRuleForm.name" class="form-input" required />
            </div>
            <div v-if="!alarmRuleForm.id">
              <label class="form-label">{{ t('modules.compressor.settings.selectTag') }}</label>
              <select v-model="alarmRuleForm.tag_id" class="form-input" required>
                <option value="">—</option>
                <option v-for="tag in store.tags" :key="tag.id" :value="tag.id">{{ tag.name }} ({{ tag.opc_path }})</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.condition') }}</label>
                <select v-model="alarmRuleForm.condition" class="form-input" required>
                  <option value="gt">&gt; (gt)</option>
                  <option value="lt">&lt; (lt)</option>
                  <option value="gte">&ge; (gte)</option>
                  <option value="lte">&le; (lte)</option>
                </select>
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.threshold') }}</label>
                <input v-model.number="alarmRuleForm.threshold" type="number" step="any" class="form-input" required />
              </div>
            </div>
            <div>
              <label class="form-label">{{ t('modules.compressor.severity.info') }}</label>
              <select v-model="alarmRuleForm.severity" class="form-input" required>
                <option value="info">info</option>
                <option value="warning">warning</option>
                <option value="critical">critical</option>
              </select>
            </div>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" @click="showAlarmRuleModal = false" class="btn-secondary text-sm">{{ t('modules.compressor.settings.cancel') }}</button>
              <button type="submit" :disabled="saving" class="btn-primary text-sm">{{ saving ? t('modules.compressor.settings.saving') : t('modules.compressor.settings.save') }}</button>
            </div>
            <p v-if="formError" class="text-red-500 text-sm">{{ formError }}</p>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Модальное окно: Правило аномалии ═══ -->
    <Teleport to="body">
      <div v-if="showAnomalyRuleModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showAnomalyRuleModal = false">
        <div class="glass-card p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">{{ t('modules.compressor.settings.anomalyRulesTitle') }}</h3>
          <form @submit.prevent="saveAnomalyRule" class="space-y-3">
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.tagName') }}</label>
              <input v-model="anomalyRuleForm.name" class="form-input" required />
            </div>
            <div v-if="!anomalyRuleForm.id">
              <label class="form-label">{{ t('modules.compressor.settings.selectTag') }}</label>
              <select v-model="anomalyRuleForm.tag_id" class="form-input" required>
                <option value="">—</option>
                <option v-for="tag in store.tags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="form-label">{{ t('modules.compressor.settings.detectorType') }}</label>
                <select v-model="anomalyRuleForm.detector_type" class="form-input" required>
                  <option value="trend">trend</option>
                  <option value="volatility">volatility</option>
                  <option value="stabilization">stabilization</option>
                  <option value="spike">spike</option>
                </select>
              </div>
              <div>
                <label class="form-label">{{ t('modules.compressor.severity.info') }}</label>
                <select v-model="anomalyRuleForm.severity" class="form-input" required>
                  <option value="info">info</option>
                  <option value="warning">warning</option>
                  <option value="critical">critical</option>
                </select>
              </div>
            </div>
            <div>
              <label class="form-label">{{ t('modules.compressor.settings.config') }}</label>
              <textarea v-model="anomalyRuleForm.configJson" class="form-input font-mono text-xs" rows="5" required></textarea>
            </div>
            <div class="flex justify-end gap-2 pt-2">
              <button type="button" @click="showAnomalyRuleModal = false" class="btn-secondary text-sm">{{ t('modules.compressor.settings.cancel') }}</button>
              <button type="submit" :disabled="saving" class="btn-primary text-sm">{{ saving ? t('modules.compressor.settings.saving') : t('modules.compressor.settings.save') }}</button>
            </div>
            <p v-if="formError" class="text-red-500 text-sm">{{ formError }}</p>
          </form>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../../stores/auth'
import { useCompressorStore } from '../../stores/compressor'

const props = defineProps({
  selectedCode: { type: String, default: '' },
})

const { t } = useI18n()
const auth = useAuthStore()
const store = useCompressorStore()

const canAdmin = computed(() => auth.hasPermission('compressor.admin') || auth.isSuperAdmin)
const canManage = computed(() => auth.hasPermission('compressor.manage') || auth.isSuperAdmin)

const saving = ref(false)
const formError = ref('')
const importResult = ref(null)
const historyImportResult = ref(null)
const importingHistory = ref(false)

// ── Диагностика ─────────────────────────────────────────

const diagLoading = ref(false)
const diagStatus = ref({ connected: false, last_seen: null, error: null, tags_count: 0 })

const currentStationObj = computed(() =>
  store.stations.find(s => s.code === props.selectedCode) || null
)

const diagHints = computed(() => {
  const hints = []
  const s = currentStationObj.value
  if (!s) return hints

  // 1. Station active?
  if (s.is_active) {
    hints.push({ type: 'ok', text: t('modules.compressor.settings.diagStationActive') })
  } else {
    hints.push({ type: 'warn', text: t('modules.compressor.settings.diagStationInactive') })
  }

  // 2. Certificate?
  if (s.opc_cert_path) {
    hints.push({ type: 'ok', text: t('modules.compressor.settings.diagCertOk') })
  } else if (s.opc_security_policy !== 'None') {
    hints.push({ type: 'warn', text: t('modules.compressor.settings.diagCertNeeded') })
  }

  // 3. Tags configured?
  if (store.tags.length > 0) {
    hints.push({ type: 'ok', text: t('modules.compressor.settings.diagTagsOk', { count: store.tags.length }) })
  } else {
    hints.push({ type: 'error', text: t('modules.compressor.settings.diagTagsEmpty') })
  }

  // 4. Collector status
  if (diagStatus.value.connected) {
    hints.push({ type: 'ok', text: t('modules.compressor.settings.diagCollectorOk') })
  } else {
    hints.push({ type: 'warn', text: t('modules.compressor.settings.diagCollectorOff') })
  }

  return hints
})

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

async function refreshDiagnostics() {
  if (!props.selectedCode) return
  diagLoading.value = true
  try {
    const data = await store.fetchStationStatus(props.selectedCode)
    diagStatus.value = data || { connected: false, last_seen: null, error: null, tags_count: 0 }
  } catch {
    diagStatus.value = { connected: false, last_seen: null, error: null, tags_count: 0 }
  } finally {
    diagLoading.value = false
  }
}

// ── Станции ──────────────────────────────────────────────

const showStationModal = ref(false)
const stationForm = ref({})

function openStationForm(station = null) {
  formError.value = ''
  if (station) {
    stationForm.value = { ...station }
  } else {
    stationForm.value = {
      name: '', code: '', opc_url: '',
      opc_security_policy: 'Basic128Rsa15', opc_security_mode: 'Sign',
      polling_interval: 300, realtime_interval: 1,
      is_active: true, description: '',
    }
  }
  showStationModal.value = true
}

async function saveStation() {
  saving.value = true
  formError.value = ''
  try {
    if (stationForm.value.id) {
      const { id, code, created_at, updated_at, tags_count, ...body } = stationForm.value
      await store.updateStation(stationForm.value.code, body)
    } else {
      await store.createStation(stationForm.value)
    }
    showStationModal.value = false
    await store.fetchStations()
  } catch (e) {
    formError.value = e.response?.data?.detail || t('admin.error')
  } finally {
    saving.value = false
  }
}

async function confirmDeleteStation(station) {
  if (!confirm(t('modules.compressor.settings.confirmDeleteStation', { name: station.name }))) return
  try {
    await store.deleteStation(station.code)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

async function doGenerateCert(station) {
  if (!confirm(t('modules.compressor.settings.confirmGenerateCert', { name: station.name }))) return
  try {
    const result = await store.generateCert(station.code)
    await store.fetchStations()
    alert(result.message)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

async function doDownloadCert(station) {
  try {
    const blob = await store.downloadCert(station.code)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${station.code}_client_cert.der`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

function _downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function doDownloadTagsTemplate() {
  try {
    const blob = await store.downloadTagsTemplate()
    _downloadBlob(blob, 'tags_template.xlsx')
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

async function doDownloadHistoryTemplate() {
  try {
    const blob = await store.downloadHistoryTemplate()
    _downloadBlob(blob, 'history_template.xlsx')
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

// ── Теги ─────────────────────────────────────────────────

const showTagModal = ref(false)
const tagForm = ref({})

function openTagForm(tag = null) {
  formError.value = ''
  if (tag) {
    tagForm.value = { ...tag }
  } else {
    tagForm.value = {
      opc_path: '', name: '', unit: '', data_type: '', category: '',
      sort_order: 0, valid_min: null, valid_max: null, stale_timeout: null,
    }
  }
  showTagModal.value = true
}

async function saveTag() {
  saving.value = true
  formError.value = ''
  try {
    if (tagForm.value.id) {
      const { id, station_id, created_at, ...body } = tagForm.value
      await store.updateTag(tagForm.value.id, body)
    } else {
      await store.createTag(props.selectedCode, tagForm.value)
    }
    showTagModal.value = false
    await store.fetchTags(props.selectedCode)
  } catch (e) {
    formError.value = e.response?.data?.detail || t('admin.error')
  } finally {
    saving.value = false
  }
}

async function doDeleteTag(tag) {
  if (!confirm(t('modules.compressor.settings.confirmDelete'))) return
  try {
    await store.deleteTag(tag.id)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

async function handleImportTags(event) {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    importResult.value = await store.importTagsExcel(props.selectedCode, file)
    await store.fetchTags(props.selectedCode)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
  event.target.value = ''
}

// ── Вычисляемые теги ─────────────────────────────────────

const showComputedModal = ref(false)
const computedForm = ref({})

function openComputedForm(ct = null) {
  formError.value = ''
  if (ct) {
    computedForm.value = { ...ct, configJson: JSON.stringify(ct.config, null, 2) }
  } else {
    computedForm.value = {
      name: '', compute_type: 'status_map', category: '',
      configJson: '{\n  "source_tags": [],\n  "rules": [],\n  "default": {"status": "—", "value": 0}\n}',
    }
  }
  showComputedModal.value = true
}

async function saveComputed() {
  saving.value = true
  formError.value = ''
  try {
    const config = JSON.parse(computedForm.value.configJson)
    if (computedForm.value.id) {
      await store.updateComputedTag(computedForm.value.id, {
        name: computedForm.value.name,
        compute_type: computedForm.value.compute_type,
        category: computedForm.value.category,
        config,
      })
    } else {
      await store.createComputedTag(props.selectedCode, {
        name: computedForm.value.name,
        compute_type: computedForm.value.compute_type,
        category: computedForm.value.category,
        config,
      })
    }
    showComputedModal.value = false
    await store.fetchComputedTags(props.selectedCode)
  } catch (e) {
    formError.value = e.response?.data?.detail || e.message || t('admin.error')
  } finally {
    saving.value = false
  }
}

async function doDeleteComputed(ct) {
  if (!confirm(t('modules.compressor.settings.confirmDelete'))) return
  try {
    await store.deleteComputedTag(ct.id)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

// ── Правила аварий ───────────────────────────────────────

const showAlarmRuleModal = ref(false)
const alarmRuleForm = ref({})

function openAlarmRuleForm(rule = null) {
  formError.value = ''
  if (rule) {
    alarmRuleForm.value = { ...rule }
  } else {
    alarmRuleForm.value = { name: '', tag_id: '', condition: 'gt', threshold: 0, severity: 'warning' }
  }
  showAlarmRuleModal.value = true
}

async function saveAlarmRule() {
  saving.value = true
  formError.value = ''
  try {
    if (alarmRuleForm.value.id) {
      const { id, tag_id, created_at, ...body } = alarmRuleForm.value
      await store.updateAlarmRule(alarmRuleForm.value.id, body)
    } else {
      await store.createAlarmRule(props.selectedCode, alarmRuleForm.value)
    }
    showAlarmRuleModal.value = false
    await store.fetchAlarmRules(props.selectedCode)
  } catch (e) {
    formError.value = e.response?.data?.detail || t('admin.error')
  } finally {
    saving.value = false
  }
}

async function doDeleteAlarmRule(rule) {
  if (!confirm(t('modules.compressor.settings.confirmDelete'))) return
  try {
    await store.deleteAlarmRule(rule.id)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

// ── Правила аномалий ─────────────────────────────────────

const showAnomalyRuleModal = ref(false)
const anomalyRuleForm = ref({})

const defaultAnomalyConfigs = {
  trend: '{"window_minutes": 15, "slope_threshold": 0.5, "min_r_squared": 0.7}',
  volatility: '{"window_minutes": 10, "baseline_minutes": 60, "std_multiplier": 3.0}',
  stabilization: '{"window_minutes": 10, "baseline_minutes": 60, "std_ratio_threshold": 0.1}',
  spike: '{"window_minutes": 5, "sigma_threshold": 4.0}',
}

function openAnomalyRuleForm(rule = null) {
  formError.value = ''
  if (rule) {
    anomalyRuleForm.value = { ...rule, configJson: JSON.stringify(rule.config, null, 2) }
  } else {
    anomalyRuleForm.value = {
      name: '', tag_id: '', detector_type: 'trend', severity: 'warning',
      configJson: defaultAnomalyConfigs.trend,
    }
  }
  showAnomalyRuleModal.value = true
}

// Update default config when detector type changes
watch(() => anomalyRuleForm.value.detector_type, (type) => {
  if (!anomalyRuleForm.value.id && type && defaultAnomalyConfigs[type]) {
    anomalyRuleForm.value.configJson = defaultAnomalyConfigs[type]
  }
})

async function saveAnomalyRule() {
  saving.value = true
  formError.value = ''
  try {
    const config = JSON.parse(anomalyRuleForm.value.configJson)
    if (anomalyRuleForm.value.id) {
      await store.updateAnomalyRule(anomalyRuleForm.value.id, {
        name: anomalyRuleForm.value.name,
        detector_type: anomalyRuleForm.value.detector_type,
        severity: anomalyRuleForm.value.severity,
        config,
      })
    } else {
      await store.createAnomalyRule(props.selectedCode, {
        name: anomalyRuleForm.value.name,
        tag_id: anomalyRuleForm.value.tag_id,
        detector_type: anomalyRuleForm.value.detector_type,
        severity: anomalyRuleForm.value.severity,
        config,
      })
    }
    showAnomalyRuleModal.value = false
    await store.fetchAnomalyRules(props.selectedCode)
  } catch (e) {
    formError.value = e.response?.data?.detail || e.message || t('admin.error')
  } finally {
    saving.value = false
  }
}

async function doDeleteAnomalyRule(rule) {
  if (!confirm(t('modules.compressor.settings.confirmDelete'))) return
  try {
    await store.deleteAnomalyRule(rule.id)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  }
}

// ── Импорт истории ───────────────────────────────────────

async function handleImportHistory(event) {
  const file = event.target.files?.[0]
  if (!file) return
  importingHistory.value = true
  try {
    historyImportResult.value = await store.importHistoryExcel(props.selectedCode, file)
  } catch (e) {
    alert(e.response?.data?.detail || t('admin.error'))
  } finally {
    importingHistory.value = false
  }
  event.target.value = ''
}

// ── Загрузка данных при смене станции ────────────────────

watch(() => props.selectedCode, async (code) => {
  if (!code) return
  importResult.value = null
  historyImportResult.value = null
  diagStatus.value = { connected: false, last_seen: null, error: null, tags_count: 0 }
  await Promise.all([
    store.fetchTags(code),
    store.fetchComputedTags(code),
    store.fetchAlarmRules(code),
    store.fetchAnomalyRules(code),
    refreshDiagnostics(),
  ])
}, { immediate: true })

// ── Helpers ──────────────────────────────────────────────

function severityDot(s) {
  return [
    'w-2 h-2 rounded-full inline-block',
    s === 'critical' ? 'bg-red-500' : s === 'warning' ? 'bg-yellow-500' : 'bg-blue-500',
  ]
}
</script>

<style scoped>
.glass-card {
  @apply bg-white/60 dark:bg-gray-800/60 backdrop-blur-xl backdrop-saturate-[1.8] rounded-lg shadow-lg border border-gray-200/30 dark:border-white/[0.08];
}
.form-label {
  @apply block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1;
}
.form-input {
  @apply w-full px-3 py-2 rounded-lg bg-white/80 dark:bg-gray-900/60 border border-gray-200/50 dark:border-white/[0.1] text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50;
}
.btn-primary {
  @apply px-4 py-2 rounded-lg bg-orange-500 text-white font-medium hover:bg-orange-600 transition-colors disabled:opacity-50;
}
.btn-secondary {
  @apply px-4 py-2 rounded-lg bg-gray-200/60 dark:bg-gray-700/60 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-300/60 dark:hover:bg-gray-600/60 transition-colors;
}
</style>
