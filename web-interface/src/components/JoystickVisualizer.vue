<template>
  <div class="status">
    <span class="pill" :class="isConnected ? 'ok' : 'off'">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
  </div>

  <div class="debug-controls">
    <div class="control">
      <label><input type="checkbox" v-model="invertLeftY" /> Invert Left Y</label>
    </div>
    <div class="control">
      <label><input type="checkbox" v-model="invertRightY" /> Invert Right Y</label>
    </div>
    <div class="control">
      <label><input type="checkbox" v-model="swapSticks" /> Swap Sticks</label>
    </div>
    <div class="control">
      <label><input type="checkbox" v-model="showRaw" /> Show raw JSON</label>
    </div>
  </div>

  <div class="graphic-wrap">
    <JoystickGraphic :axes="procAxes" :buttons="buttons" :connected="isConnected" />
  </div>

  <div class="joystick-grid">
    <div>
      <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">Left Stick</h3>
      <div class="stick">
        <div class="stick-dot" :style="leftStickStyle"></div>
      </div>
      <div class="axis-readout">
        <span class="mono">X: {{ fmt(procAxes[0]) }}</span>
        <span class="mono">Y: {{ fmt(procAxes[1]) }}</span>
      </div>
    </div>
    <div>
      <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">Right Stick</h3>
      <div class="stick">
        <div class="stick-dot" :style="rightStickStyle"></div>
      </div>
      <div class="axis-readout">
        <span class="mono">X: {{ fmt(procAxes[2]) }}</span>
        <span class="mono">Y: {{ fmt(procAxes[3]) }}</span>
      </div>
    </div>
    <div>
      <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">Triggers</h3>
      <div class="triggers">
        <div class="trigger">
          <div class="trigger-bar" :style="{ height: triggerPercent(procAxes[4]) }"></div>
          <span class="mono">LT: {{ fmt(procAxes[4]) }}</span>
        </div>
        <div class="trigger">
          <div class="trigger-bar" :style="{ height: triggerPercent(procAxes[5]) }"></div>
          <span class="mono">RT: {{ fmt(procAxes[5]) }}</span>
        </div>
      </div>
    </div>
    <div>
      <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">Buttons</h3>
      <div class="buttons">
        <div v-for="(pressed, i) in buttons" :key="i" class="btn" :class="{ on: pressed }" :title="`Index ${i}`">
          {{ buttonLabel(i) }}
        </div>
      </div>
    </div>
  </div>

  <div v-if="showRaw" class="raw">
    <pre>{{ rawJson }}</pre>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRobotState } from '@/stores/robotState'
import JoystickGraphic from './JoystickGraphic.vue'

const robot = useRobotState()

const axes = computed<number[]>(() => Array.isArray(robot.joystick?.axes) ? (robot.joystick.axes as number[]) : [])
const buttons = computed<boolean[]>(() => Array.isArray(robot.joystick?.buttons) ? (robot.joystick.buttons as boolean[]) : [])

const isConnected = computed<boolean>(() => {
  const a = axes.value?.length ?? 0
  const b = buttons.value?.length ?? 0
  return (a > 0) || (b > 0)
})

const invertLeftY = ref(false)
const invertRightY = ref(false)
const swapSticks = ref(false)
const showRaw = ref(false)

function clamp(v: number) { return Math.max(-1, Math.min(1, v ?? 0)) }
function fmt(v?: number) { return (v ?? 0).toFixed(2) }

const useWindowsMapping = (() => {
  try {
    const p = (navigator as any)?.platform || ''
    const ua = (navigator as any)?.userAgent || ''
    return /Win/i.test(p) || /Windows/i.test(ua)
  } catch { return false }
})()

const procAxes = computed<number[]>(() => {
  const raw = axes.value || []
  let mapped: number[]
  if (useWindowsMapping) {
    // Your device indices from REPL: LS(0,1), RS(2,3), LT(4), RT(5)
    mapped = [raw[0] ?? 0, raw[1] ?? 0, raw[2] ?? 0, raw[3] ?? 0, raw[4] ?? 0, raw[5] ?? 0]
  } else {
    mapped = [raw[0] ?? 0, raw[1] ?? 0, raw[2] ?? 0, raw[3] ?? 0, raw[4] ?? 0, raw[5] ?? 0]
  }
  const a = mapped.map(v => clamp(v ?? 0))
  // Invert Y
  a[1] = (invertLeftY.value ? -a[1] : a[1])
  a[3] = (invertRightY.value ? -a[3] : a[3])
  // Swap sticks (0,1) with (2,3)
  if (swapSticks.value) {
    const l0 = a[0], l1 = a[1]
    a[0] = a[2]; a[1] = a[3]
    a[2] = l0;  a[3] = l1
  }
  return a
})

const leftStickStyle = computed(() => {
  const x = procAxes.value[0] ?? 0
  const y = procAxes.value[1] ?? 0
  return { transform: `translate(${x * 40}px, ${y * 40}px)` }
})
const rightStickStyle = computed(() => {
  const x = procAxes.value[2] ?? 0
  const y = procAxes.value[3] ?? 0
  return { transform: `translate(${x * 40}px, ${y * 40}px)` }
})

function triggerPercent(v?: number) {
  const n = clamp(v ?? 0)
  const p = Math.round(((n + 1) / 2) * 100)
  return `${p}%`
}

const xBoxLabels = [
  'A','B','X','Y',
  'LB','RB',
  'LT','RT',
  'View','Menu',
  'LS','RS',
  'Up','Down','Left','Right',
  'Xbox'
]

function buttonLabel(i: number) {
  return xBoxLabels[i] ?? `${i}`
}

const rawJson = computed(() => {
  return JSON.stringify((robot as any).joystick ?? { axes: [], buttons: [] }, null, 2)
})
</script>
    
<style scoped>
.status { display:flex; justify-content:flex-end; margin-bottom: 0.5rem; }
.pill { padding: 2px 10px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; }
.pill.ok { background:#dcfce7; color:#065f46; }
.pill.off { background:#fee2e2; color:#7f1d1d; }
.debug-controls { display:flex; flex-wrap: wrap; gap: 1rem; align-items: center; margin-bottom: 0.5rem; }
.debug-controls .control { display:flex; gap: 0.5rem; align-items: center; }
.graphic-wrap { margin-bottom: 1rem; }
.joystick-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.stick {
  width: 120px;
  height: 120px;
  border-radius: 10px;
  background: #f3f4f6;
  position: relative;
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.stick::before,
.stick::after {
  content: '';
  position: absolute;
  background: #e5e7eb;
}
.stick::before { width: 1px; height: 100%; }
.stick::after { height: 1px; width: 100%; }
.stick-dot {
  width: 20px;
  height: 20px;
  background: #3b82f6;
  border-radius: 9999px;
  transition: transform 60ms linear;
}
.axis-readout { margin-top: 0.5rem; display: flex; gap: 0.75rem; }
.triggers { display: flex; gap: 1rem; }
.trigger { width: 48px; height: 120px; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 8px; position: relative; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; padding-bottom: 6px; }
.trigger-bar { position: absolute; bottom: 0; left: 0; right: 0; background: #10b981; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }
.buttons { display: flex; flex-wrap: wrap; gap: 6px; }
.btn { height: 32px; border-radius: 6px; background: #e5e7eb; display: flex; align-items: center; justify-content: center; font-weight: 600; color: #374151; }
.btn.on { background: #22c55e; color: white; }
.raw { margin-top: 0.5rem; }
</style>
