<template>
  <div>
    <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">General Settings</h3>
    <div class="mb-2">
      <label class="label-muted">Robot Name</label>
      <input type="text"
             :value="configState.robot?.name ?? ''"
             @input="e => updateConfigField(['robot', 'name'], e)"
             class="input" />
    </div>
    <div>
      <label class="label-muted">Maximum Speed (mm/s)</label>
      <input type="number"
             :value="configState.motor?.dc_motors?.max_speed ?? 0"
             @input="e => updateConfigField(['motor', 'dc_motors', 'max_speed'], e)"
             class="input" />
    </div>
    <div class="mt-3">
      <label class="label-muted">Voice Enabled</label>
      <input type="checkbox"
             :checked="configState.features?.voice_enabled ?? true"
             @change="e => updateConfigField(['features', 'voice_enabled'], e)"
      />
    </div>
    <div class="mt-2">
      <label class="label-muted">Wake Word</label>
      <input type="text"
             :value="configState.voice?.wake_word ?? ''"
             @input="e => updateConfigField(['voice', 'wake_word'], e)"
             class="input" />
    </div>
    <div class="mt-2">
      <label class="label-muted">Speech-to-Text Backend</label>
      <select 
        :value="configState.voice?.backend ?? 'whisper'"
        @change="e => updateConfigField(['voice', 'backend'], e)"
        class="input">
        <option value="whisper">Whisper (local)</option>
        <option value="google">Google Cloud Speech</option>
      </select>
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
  }
}
</script>
