<template>
  <SectionCard title="LED Matrix">
    <div class="dashboard-led-matrix-container">
      <button class="btn" style="margin-bottom:1rem;" @click="testLedMatrix">Test LED Matrix</button>
      <select v-model="selectedAnimation" @change="setAnimation" class="dropdown" style="margin-bottom:1rem;">
        <option v-for="anim in animations" :key="anim.value" :value="anim.value">
          {{ anim.label }}
        </option>
      </select>
      <button class="btn" style="margin-left:1rem; margin-bottom:1rem; background:#f87171; color:white;" @click="stopAnimation">Stop Animation</button>
      <div
        class="led-matrix-custom"
        :style="{ width: (ledMatrix[0]?.length || 8) * 34 + 'px', height: (ledMatrix.length || 4) * 34 + 'px' }"
      >
        <template v-if="ledMatrix && ledMatrix.length">
          <div
            v-for="(row, y) in ledMatrix"
            :key="y"
            class="led-row-custom"
          >
            <div
              v-for="(pixel, x) in row"
              :key="x"
              class="led-pixel-custom"
              :style="{
                background: `radial-gradient(circle at 60% 35%, rgba(${pixel[0]},${pixel[1]},${pixel[2]},1) 70%, rgba(255,255,255,0.2) 100%)`,
                border: `2px solid rgba(${pixel[0]},${pixel[1]},${pixel[2]},0.6)`
              }"
            />
          </div>
        </template>
        <template v-else>
          <div
            v-for="i in 32"
            :key="i"
            class="led-pixel rounded-full border border-gray-200 bg-gray-200 opacity-60"
            style="width:26px; height:26px; display:inline-block;"
          />
        </template>
      </div>
      <div v-if="!ledMatrix || ledMatrix.length === 0" class="label-muted" style="margin-top:1rem;">No LED data</div>
      <div v-if="robot.ledAnimationState.currentAnimation" class="label-muted" style="margin-top:1rem;">
        Animation: <b>{{ robot.ledAnimationState.currentAnimation }}</b>
        <span v-if="robot.ledAnimationState.loop">(Looping)</span>
      </div>
      <pre class="mono" style="margin-top:1rem; background:#f3f4f6; padding:0.75rem; border-radius:6px; max-width:100%; overflow-x:auto; color:#333; font-size:0.9rem;">{{ JSON.stringify(ledMatrix, null, 2) }}</pre>
      <div v-if="ledMatrix && ledMatrix[0] && ledMatrix[0][0]" class="mono" style="margin-top:1rem; background:#fef3c7; padding:0.5rem; border-radius:6px; font-size:0.85rem; color:#a16207;">
        <span>First pixel RGB: {{ ledMatrix[0][0] }}</span>
        <span v-if="debugColor" style="margin-left:1em;">Computed CSS color: <span :style="{background: debugColor, color: '#fff', padding: '0 8px', borderRadius: '4px'}">{{ debugColor }}</span></span>
      </div>
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import SectionCard from './SectionCard.vue'
import { useRobotState } from '@/stores/robotState'
import { ref } from 'vue'
import { api } from '../services/api'
const robot = useRobotState()
import { onMounted, watch } from 'vue'
const ledMatrix = ref<any[][]>([])
import { computed, watchEffect } from 'vue'

const debugColor = computed(() => {
  if (ledMatrix.value && ledMatrix.value[0] && ledMatrix.value[0][0]) {
    const px = ledMatrix.value[0][0]
    return `rgb(${px[0]},${px[1]},${px[2]})`
  }
  return ''
})

watchEffect(() => {
  // Log buffer to browser console for debug
  // eslint-disable-next-line no-console
  console.log('[LedMatrix.vue] ledMatrix:', JSON.stringify(ledMatrix.value))
})

// Sync ledMatrix from backend robot state
onMounted(() => {
  // Initial set
  if (robot.ledMatrix) ledMatrix.value = robot.ledMatrix
})
watch(() => robot.$state, (state) => {
  if (state.ledMatrix) ledMatrix.value = state.ledMatrix
}, { deep: true })

function testLedMatrix() {
  api.sendCommand({ type: 'test_led' });
}
const animations = [
  { value: 'rainbow', label: 'Rainbow' },
  { value: 'rainbow_blinky', label: 'Rainbow Blinky' },
  { value: 'random_blinky', label: 'Random Blinky' },
  { value: 'random_sparkles', label: 'Random Sparkles' },
  { value: 'snow', label: 'Snow' },
]
const selectedAnimation = ref(animations[0].value)

function setAnimation() {
  api.sendCommand({ type: 'set_led_animation', animation: selectedAnimation.value, loop: true })
}
function stopAnimation() {
  api.sendCommand({ type: 'stop_led_animation' })
}

</script>

<style scoped>
.led-matrix-custom {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border-radius: 18px;
  background: #181825;
  box-shadow: 0 6px 32px 0 rgba(0,0,0,0.18), 0 1.5px 8px 0 rgba(0,0,0,0.13);
  border: 2.5px solid #3b0764;
}
.led-row-custom {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  margin-bottom: 6px;
}
.led-pixel-custom {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin: 7px;
  background: #222;
  box-shadow: 0 1.5px 6px 0 rgba(0,0,0,0.32), 0 0 0 2.5px #111 inset;
  transition: background 0.18s, box-shadow 0.18s, border-color 0.18s;
  border: 2px solid #222;
}
</style>
