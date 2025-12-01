<template>
  <div>
    <h3 class="section-card-title">Sensor Configuration</h3>
    <div class="mb-2">
      <label class="label-muted">Sensor Update Rate (Hz)</label>
      <input type="number"
             :value="configState.sensors?.update_rate ?? 0"
             @input="e => updateConfigField(['sensors', 'update_rate'], e)"
             class="input" />
    </div>
    <div>
      <label class="label-muted">Sensor Threshold</label>
      <input type="number"
             :value="configState.sensors?.threshold ?? 0"
             @input="e => updateConfigField(['sensors', 'threshold'], e)"
             class="input" />
    </div>
    <div class="mt-3">
      <label class="label-muted">Joystick Deadzone</label>
      <input type="number"
             step="0.01"
             min="0"
             max="1"
             :value="configState.joystick?.deadzone ?? 0"
             @input="e => updateConfigField(['joystick', 'deadzone'], e)"
             class="input" />
    </div>
    <div class="mt-2">
      <label class="label-muted">Joystick Smoothing</label>
      <input type="number"
             step="0.01"
             min="0"
             max="1"
             :value="configState.joystick?.smoothing ?? 0"
             @input="e => updateConfigField(['joystick', 'smoothing'], e)"
             class="input" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRobotState } from '@/stores/robotState'
import { api } from '../services/api'
import { setNestedValue } from '../utils/configUtils'

const robot = useRobotState()
const configState = computed(() => robot.config || {})

async function updateConfigField(path: string[], event: Event) {
  const target = event.target as HTMLInputElement | null
  if (!target) return
  const raw = target.type === 'checkbox' ? target.checked : target.value
  const value = target.type === 'number' ? Number(raw) : raw
  
  try {
    await api.setConfigValue(path, value)
    const current = robot.config || {}
    robot.config = setNestedValue(current, path, value)
  } catch (error) {
    console.error('Failed to update config:', error)
    // Optionally: revert UI or show error message
  }
}
</script>
