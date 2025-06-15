<template>
  <SectionCard title="LED Matrix">
    <div class="dashboard-led-matrix-container">
      <button class="btn" style="margin-bottom:1rem;" @click="testLedMatrix">Test LED Matrix</button>
      <div class="led-matrix" :style="{ width: ledMatrix[0]?.length * 22 + 'px', height: ledMatrix.length * 22 + 'px' }">
        <div v-for="(row, y) in ledMatrix" :key="y" class="led-row">
          <div v-for="(pixel, x) in row" :key="x"
            class="led-pixel"
            :style="{ background: `rgb(${pixel[0]},${pixel[1]},${pixel[2]})` }"
          />
        </div>
      </div>
      <div v-if="!ledMatrix || ledMatrix.length === 0" class="label-muted" style="margin-top:1rem;">No LED data</div>
      <pre class="mono" style="margin-top:1rem; background:#f3f4f6; padding:0.75rem; border-radius:6px; max-width:100%; overflow-x:auto; color:#333; font-size:0.9rem;">{{ JSON.stringify(ledMatrix, null, 2) }}</pre>
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import SectionCard from './SectionCard.vue'
import { useRobotState } from '@/stores/robotState'
import { ref } from 'vue'
import { api } from '../services/api'
const robot = useRobotState()
const ledMatrix = ref([])

function testLedMatrix() {
  api.sendCommand({ type: 'test_led' });
}
</script>
