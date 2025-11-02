<template>
  <svg :width="width" :height="height" viewBox="0 0 240 140">
    <defs>
      <linearGradient :id="`wheelGradFL`" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" :stop-color="wheelColor(fl)" />
        <stop offset="100%" stop-color="#ddd" />
      </linearGradient>
      <linearGradient :id="`wheelGradFR`" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" :stop-color="wheelColor(fr)" />
        <stop offset="100%" stop-color="#ddd" />
      </linearGradient>
      <linearGradient :id="`wheelGradRL`" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" :stop-color="wheelColor(rl)" />
        <stop offset="100%" stop-color="#ddd" />
      </linearGradient>
      <linearGradient :id="`wheelGradRR`" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" :stop-color="wheelColor(rr)" />
        <stop offset="100%" stop-color="#ddd" />
      </linearGradient>
    </defs>

    <rect x="30" y="20" rx="12" ry="12" width="180" height="100" fill="#f3f4f6" stroke="#cbd5e1" />

    <g :transform="`translate(30,20)`">
      <g :transform="`translate(0,0)`">
        <rect :fill="`url(#wheelGradFL)`" :opacity="opacity(fl)" x="-18" y="-10" width="16" height="36" stroke="#6b7280" rx="4" />
        <text x="-22" y="30" font-size="10" fill="#4b5563">FL</text>
      </g>
      <g :transform="`translate(180,0)`">
        <rect :fill="`url(#wheelGradFR)`" :opacity="opacity(fr)" x="2" y="-10" width="16" height="36" stroke="#6b7280" rx="4" />
        <text x="22" y="30" font-size="10" fill="#4b5563">FR</text>
      </g>
      <g :transform="`translate(0,64)`">
        <rect :fill="`url(#wheelGradRL)`" :opacity="opacity(rl)" x="-18" y="-10" width="16" height="36" stroke="#6b7280" rx="4" />
        <text x="-22" y="30" font-size="10" fill="#4b5563">RL</text>
      </g>
      <g :transform="`translate(180,64)`">
        <rect :fill="`url(#wheelGradRR)`" :opacity="opacity(rr)" x="2" y="-10" width="16" height="36" stroke="#6b7280" rx="4" />
        <text x="22" y="30" font-size="10" fill="#4b5563">RR</text>
      </g>

      <g transform="translate(40,30)">
        <rect x="0" y="0" width="100" height="16" rx="8" fill="#e5e7eb" />
        <rect :x="barX(fwd)" y="0" :width="Math.abs(fwd)*50" height="16" rx="8" :fill="fwd>=0 ? '#22c55e' : '#ef4444'" />
        <text x="0" y="-4" font-size="10" fill="#4b5563">Forward</text>
      </g>
      <g transform="translate(40,60)">
        <rect x="0" y="0" width="100" height="16" rx="8" fill="#e5e7eb" />
        <rect :x="barX(turn)" y="0" :width="Math.abs(turn)*50" height="16" rx="8" :fill="turn>=0 ? '#3b82f6' : '#f59e0b'" />
        <text x="0" y="-4" font-size="10" fill="#4b5563">Turn</text>
      </g>
    </g>
  </svg>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  fl: { type: Number, default: 0 },
  fr: { type: Number, default: 0 },
  rl: { type: Number, default: 0 },
  rr: { type: Number, default: 0 },
  width: { type: Number, default: 300 },
  height: { type: Number, default: 180 }
})
const clamp01 = (v) => Math.max(0, Math.min(1, v))
const clamp11 = (v) => Math.max(-1, Math.min(1, v))
const mag = (v) => Math.min(1, Math.abs(v))
const wheelColor = (v) => (v >= 0 ? '#22c55e' : '#ef4444')
const opacity = (v) => 0.25 + 0.75 * mag(v)
// Center the bar at 50; positive grows to the right, negative to the left
const barX = (v) => (v >= 0 ? 50 : 50 - Math.abs(v)*50)
// Forward is the mean of all wheel speeds, clamped to [-1,1]
const fwd = computed(() => clamp11((props.fl + props.fr + props.rl + props.rr) / 4))
// Turn is (leftAvg - rightAvg) normalized to [-1,1]
const leftAvg = computed(() => (props.fl + props.rl) / 2)
const rightAvg = computed(() => (props.fr + props.rr) / 2)
const turn = computed(() => clamp11((leftAvg.value - rightAvg.value) / 2))
</script>
