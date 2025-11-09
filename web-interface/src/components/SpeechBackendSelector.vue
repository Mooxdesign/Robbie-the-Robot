<template>
  <div style="margin-top: 2rem;">
    <label for="stt-backend-select">Speech-to-Text Backend:</label>
    <select id="stt-backend-select" v-model="selectedBackend" @change="onBackendChange">
      <option value="whisper">Whisper (local)</option>
      <option value="google">Google Cloud Speech</option>
    </select>
    <span v-if="backendStatus" style="margin-left:1rem;">Current: {{ backendStatus }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../services/api'

const selectedBackend = ref('whisper')
const backendStatus = ref('')

async function fetchBackendStatus() {
  backendStatus.value = selectedBackend.value
}

async function onBackendChange() {
  try {
    await api.setSpeechBackend(selectedBackend.value)
    backendStatus.value = selectedBackend.value
  } catch (e) {
    backendStatus.value = 'Error!'
  }
}

onMounted(() => {
  fetchBackendStatus()
})
</script>
