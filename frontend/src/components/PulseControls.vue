<template>
  <div :class="['pulse-controls', { dark: dark }]">
    <div class="pulse-ctrl-group">
      <div class="pulse-ctrl-label">{{ t('pulse.status') }}</div>
      <button
        v-for="(label, idx) in stateLabels"
        :key="idx"
        :class="['pulse-ctrl-btn', { active: state === idx }]"
        :style="state === idx ? activeStyle(idx) : {}"
        @click="$emit('update:state', idx)"
      >
        {{ label }}
      </button>
    </div>
    <div class="pulse-ctrl-group">
      <div class="pulse-ctrl-label">{{ t('pulse.intensity') }}</div>
      <button
        v-for="lvl in [1, 2, 3]"
        :key="lvl"
        :class="['pulse-ctrl-btn', { active: intensity === lvl }]"
        :style="intensity === lvl ? activeStyle(state) : {}"
        @click="$emit('update:intensity', lvl)"
      >
        {{ lvl }}
      </button>
    </div>
    <div class="pulse-ctrl-group">
      <div class="pulse-ctrl-label">{{ t('pulse.voice') }}</div>
      <button
        :class="['pulse-ctrl-btn', { active: pulseMode === 0 }]"
        :style="pulseMode === 0 ? activeStyle(state) : {}"
        @click="$emit('update:pulseMode', 0)"
      >
        {{ t('pulse.voiceOff') }}
      </button>
      <button
        v-for="lvl in [1, 2, 3]"
        :key="'sim' + lvl"
        :class="['pulse-ctrl-btn', { active: pulseMode === lvl }]"
        :style="pulseMode === lvl ? activeStyle(state) : {}"
        @click="$emit('update:pulseMode', lvl)"
      >
        {{ t('pulse.sim') }} {{ lvl }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

defineProps({
  state: { type: Number, default: 0 },
  intensity: { type: Number, default: 1 },
  dark: { type: Boolean, default: true },
  pulseMode: { type: Number, default: 0 }
})
defineEmits(['update:state', 'update:intensity', 'update:pulseMode'])

const stateLabels = ['норма', 'уведомление', 'предупреждение', 'высокая важность', 'экспертиза']

const stateStyles = [
  { '--ctrl-c': 'rgb(30,190,125)',  '--ctrl-bg': 'rgba(30,190,125,0.12)',  '--ctrl-glow': 'rgba(30,190,125,0.15)' },
  { '--ctrl-c': 'rgb(30,120,210)',  '--ctrl-bg': 'rgba(30,120,210,0.12)',  '--ctrl-glow': 'rgba(30,120,210,0.15)' },
  { '--ctrl-c': 'rgb(220,140,20)',  '--ctrl-bg': 'rgba(220,140,20,0.12)',  '--ctrl-glow': 'rgba(220,140,20,0.15)' },
  { '--ctrl-c': 'rgb(210,40,40)',   '--ctrl-bg': 'rgba(210,40,40,0.12)',   '--ctrl-glow': 'rgba(210,40,40,0.15)' },
  { '--ctrl-c': 'rgb(130,50,210)',  '--ctrl-bg': 'rgba(130,50,210,0.12)',  '--ctrl-glow': 'rgba(130,50,210,0.15)' }
]

function activeStyle(stateIdx) {
  return stateStyles[stateIdx] || stateStyles[0]
}
</script>

<style scoped>
.pulse-controls {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 160px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-end;
  padding-right: 24px;
  gap: 20px;
  opacity: 0;
  transition: opacity 0.4s ease;
}
.pulse-controls:hover {
  opacity: 1;
}
.pulse-ctrl-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}
.pulse-ctrl-label {
  font-family: system-ui, sans-serif;
  font-size: 0.45rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-bottom: 2px;
}
.pulse-ctrl-btn {
  display: block;
  width: 100%;
  padding: 5px 12px;
  border-radius: 6px;
  font-family: system-ui, sans-serif;
  font-size: 0.55rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.35s ease;
  text-align: right;
  white-space: nowrap;
}
.pulse-ctrl-btn.active {
  border-color: var(--ctrl-c, rgba(255,255,255,0.15));
  background: var(--ctrl-bg, rgba(255,255,255,0.06));
  color: var(--ctrl-c, rgba(255,255,255,0.7));
  box-shadow: 0 0 12px var(--ctrl-glow, rgba(255,255,255,0.05));
}

/* ─── Dark theme (on dark orb background) ─── */
.pulse-controls.dark .pulse-ctrl-label {
  color: rgba(255,255,255,0.15);
}
.pulse-controls.dark .pulse-ctrl-btn {
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.03);
  color: rgba(255,255,255,0.3);
}
.pulse-controls.dark .pulse-ctrl-btn:hover {
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.5);
}

/* ─── Light theme (on light orb background) ─── */
.pulse-controls:not(.dark) .pulse-ctrl-label {
  color: rgba(0,0,0,0.2);
}
.pulse-controls:not(.dark) .pulse-ctrl-btn {
  border: 1px solid rgba(0,0,0,0.08);
  background: rgba(0,0,0,0.03);
  color: rgba(0,0,0,0.35);
}
.pulse-controls:not(.dark) .pulse-ctrl-btn:hover {
  background: rgba(0,0,0,0.06);
  color: rgba(0,0,0,0.6);
}
</style>
