<template>
  <SectionCard title="Motors">
    <div class="grid">
      <div>
        <div class="row"><span class="label">Enabled</span><span class="val">{{ motor.enabled ? 'Yes' : 'No' }}</span></div>
        <div class="row"><span class="label">Mode</span><span class="val">{{ motor.mode }}</span></div>
        <div class="row"><span class="label">Target L/R</span><span class="val mono">{{ fmt(motor.target_left) }} / {{ fmt(motor.target_right) }}</span></div>
        <div class="row"><span class="label">Speed L/R</span><span class="val mono">{{ fmt(motor.left_speed) }} / {{ fmt(motor.right_speed) }}</span></div>
      </div>
      <div class="car">
        <CarGraphic
          :fl="motor.left_speed"
          :rl="motor.left_speed"
          :fr="motor.right_speed"
          :rr="motor.right_speed"
          :width="320"
          :height="190"
        />
      </div>
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import SectionCard from './SectionCard.vue'
import CarGraphic from './CarGraphic.vue'
import { computed } from 'vue'
import { useRobotState } from '@/stores/robotState'

const store = useRobotState()
const motor = computed(() => store.motor || { enabled:false, mode:'arcade', target_left:0, target_right:0, left_speed:0, right_speed:0 })

function fmt(v: any) {
  const n = Number(v)
  if (Number.isNaN(n)) return '-'
  return n.toFixed(2)
}
</script>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; align-items: center; }
.row { display: flex; justify-content: space-between; margin: 4px 0; }
.label { color: #374151; font-weight: 600; }
.val { color: #111827; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.car { display: flex; justify-content: center; }
@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
