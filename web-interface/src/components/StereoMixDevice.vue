<template>
  <div class="stereo-mix-device">
    <div class="device-list">
      <label>Available Stereo Mix Devices:</label>
      <ul>
        <li v-for="(device, idx) in devices" :key="device[0]">
          <span :class="{'active': device[0] === currentDevice}" >
            {{ device[1] }} (index: {{ device[0] }})
          </span>
        </li>
      </ul>
    </div>
    <button @click="cycleDevice" :disabled="devices.length === 0">Cycle Stereo Mix Device</button>
    <div v-if="selectedDevice">
      <strong>Selected:</strong> {{ selectedDevice[1] }} (index: {{ selectedDevice[0] }})
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const devices = ref<Array<[number, string]>>([])
const selectedDevice = ref<[number, string] | null>(null)
const currentDevice = ref<number | null>(null)

async function fetchDevices() {
  const res = await axios.get('/api/audio/stereo_mix_devices')
  devices.value = res.data.devices
  // Try to infer selected device
  if (selectedDevice.value) {
    currentDevice.value = selectedDevice.value[0]
  } else if (devices.value.length > 0) {
    currentDevice.value = devices.value[0][0]
  }
}

async function cycleDevice() {
  const res = await axios.post('/api/audio/cycle_stereo_mix')
  if (res.data.selected_device) {
    selectedDevice.value = res.data.selected_device
    currentDevice.value = selectedDevice.value[0]
  }
  await fetchDevices()
}

onMounted(async () => {
  await fetchDevices()
})
</script>

<style scoped>
.stereo-mix-device {
  margin-bottom: 1rem;
}
.device-list ul {
  list-style: none;
  padding: 0;
}
.device-list li .active {
  font-weight: bold;
  color: #42b983;
}
button {
  margin-top: 0.5rem;
}
</style>
