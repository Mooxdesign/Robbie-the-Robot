<template>
  <div class="space-y-10 p-8 bg-gray-50 min-h-screen">
    <!-- HEADER -->
    <header class="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
      <h1 class="text-3xl font-extrabold text-gray-900 mb-4 md:mb-0">Robbie the Robot Dashboard</h1>
      <nav class="flex space-x-4 text-lg font-medium">
        <span class="text-blue-600">Dashboard</span>
        <span class="text-gray-400">|</span>
        <span class="text-blue-600">Control</span>
        <span class="text-gray-400">|</span>
        <span class="text-blue-600">Configuration</span>
        <span class="text-gray-400">|</span>
        <span class="text-blue-600">Visualization</span>
        <span class="text-gray-400">|</span>
        <span class="text-blue-600">Debug</span>
      </nav>
    </header>

    <!-- STATUS SECTION -->
    <section>
      <h2 class="text-2xl font-bold mb-4">Status</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        <!-- Connection Status -->
        <div class="bg-white shadow rounded-lg p-6 flex items-center">
          <div :class="['h-4 w-4 rounded-full mr-4', isConnected ? 'bg-green-400' : 'bg-red-400']"></div>
          <div>
            <div class="text-sm text-gray-500">Status</div>
            <div class="text-xl font-semibold text-gray-900">{{ isConnected ? 'Connected' : 'Disconnected' }}</div>
          </div>
        </div>
        <!-- Battery -->
        <div class="bg-white shadow rounded-lg p-6">
          <div class="text-sm text-gray-500">Battery</div>
          <div class="text-xl font-semibold text-gray-900">{{ batteryLevel }}%</div>
        </div>
        <!-- Temperature -->
        <div class="bg-white shadow rounded-lg p-6">
          <div class="text-sm text-gray-500">Temperature</div>
          <div class="text-xl font-semibold text-gray-900">{{ temperature }}°C</div>
        </div>
      </div>
      <!-- Recent Activity -->
      <div class="bg-white shadow rounded-lg p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-2">Recent Activity</h3>
        <ul class="divide-y divide-gray-100">
          <li v-for="activity in recentActivity" :key="activity.id" class="py-2 flex items-center justify-between">
            <span class="text-gray-700">{{ activity.message }}</span>
            <span class="text-xs text-gray-400">{{ activity.time }}</span>
          </li>
        </ul>
      </div>
    </section>

    <!-- CONFIGURATION SECTION -->
    <section>
      <h2 class="text-2xl font-bold mb-4">Robot Configuration</h2>
      <div class="bg-white shadow rounded-lg p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- General Settings -->
        <div>
          <h3 class="font-semibold text-gray-800 mb-2">General Settings</h3>
          <div class="mb-2">
            <label class="block text-sm text-gray-500">Robot Name</label>
            <input type="text" v-model="robotName" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
          <div>
            <label class="block text-sm text-gray-500">Maximum Speed (mm/s)</label>
            <input type="number" v-model="maxSpeed" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
        </div>
        <!-- Sensor Config -->
        <div>
          <h3 class="font-semibold text-gray-800 mb-2">Sensor Configuration</h3>
          <div class="mb-2">
            <label class="block text-sm text-gray-500">Sensor Update Rate (Hz)</label>
            <input type="number" v-model="sensorUpdateRate" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
          <div>
            <label class="block text-sm text-gray-500">Sensor Threshold</label>
            <input type="number" v-model="sensorThreshold" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
        </div>
        <!-- Motor Config -->
        <div>
          <h3 class="font-semibold text-gray-800 mb-2">Motor Configuration</h3>
          <div class="mb-2">
            <label class="block text-sm text-gray-500">PID P Value</label>
            <input type="number" v-model="pidP" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
          <div class="mb-2">
            <label class="block text-sm text-gray-500">PID I Value</label>
            <input type="number" v-model="pidI" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
          <div>
            <label class="block text-sm text-gray-500">PID D Value</label>
            <input type="number" v-model="pidD" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
        </div>
      </div>
      <div class="flex justify-end mt-4">
        <button class="px-5 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 transition">Save Configuration</button>
      </div>
    </section>

    <!-- CONTROL SECTION -->
    <section>
      <h2 class="text-2xl font-bold mb-4">Robot Control</h2>
      <div class="bg-white shadow rounded-lg p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Movement Control -->
        <div>
          <h3 class="font-semibold text-gray-800 mb-2">Movement Control</h3>
          <div class="flex justify-center space-x-4">
            <button class="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-xl font-bold">↑</button>
          </div>
          <div class="flex justify-center space-x-4 mt-2">
            <button class="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-xl font-bold">←</button>
            <button class="w-12 h-12 bg-gray-400 rounded flex items-center justify-center text-xl font-bold">■</button>
            <button class="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-xl font-bold">→</button>
          </div>
          <div class="flex justify-center mt-2">
            <button class="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-xl font-bold">↓</button>
          </div>
        </div>
        <!-- Speed Control -->
        <div>
          <h3 class="font-semibold text-gray-800 mb-2">Speed Control</h3>
          <div class="flex items-center space-x-4">
            <input type="range" min="0" max="100" v-model="speed" class="w-full" />
            <span class="text-lg font-semibold">Speed: {{ speed }}%</span>
          </div>
        </div>
      </div>
    </section>

    <!-- VISUALIZATION SECTION -->
    <section>
      <h2 class="text-2xl font-bold mb-4">Robot Visualization</h2>
      <div class="bg-white shadow rounded-lg p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 3D View Placeholder -->
        <div>
          <h3 class="font-semibold text-gray-800 mb-2">3D View</h3>
          <div class="h-40 bg-gray-200 rounded flex items-center justify-center text-gray-400">3D View Placeholder</div>
          <div class="flex space-x-4 mt-2">
            <div>
              <label class="block text-sm text-gray-500">Camera Angle</label>
              <input type="number" v-model="cameraAngle" class="mt-1 block w-24 border-gray-300 rounded-md shadow-sm" />
            </div>
            <div>
              <label class="block text-sm text-gray-500">Camera Height</label>
              <input type="number" v-model="cameraHeight" class="mt-1 block w-24 border-gray-300 rounded-md shadow-sm" />
            </div>
          </div>
        </div>
        <!-- Real-Time Audio & Transcription -->
        <div>
          <h3 class="font-semibold text-gray-800 mb-2">Audio Input Level</h3>
          <div class="flex items-center space-x-3 mb-4">
            <div class="w-48 h-6 bg-gray-200 rounded-full overflow-hidden relative">
              <div :style="{ width: audioLevelPercent + '%', background: audioLevelColor }" class="h-full transition-all duration-200" />
            </div>
            <span class="text-lg font-mono" :style="{ color: audioLevelColor }">{{ audioLevelDb.toFixed(1) }} dB</span>
          </div>
          <h3 class="font-semibold text-gray-800 mb-2 mt-6">Last Transcription</h3>
          <div class="bg-yellow-100 border-l-4 border-yellow-400 text-yellow-800 p-4 rounded shadow text-lg font-bold min-h-[3rem] flex items-center child-friendly-transcription">
            <span v-if="lastTranscription">{{ lastTranscription }}</span>
            <span v-else class="italic text-gray-400">Say something to Robbie...</span>
          </div>
        </div>
      </div>
    </section>

    <!-- DEBUG SECTION -->
    <section>
      <h2 class="text-2xl font-bold mb-4">Debug Console</h2>
      <div class="bg-white shadow rounded-lg p-6 mb-6">
        <div class="flex justify-between mb-2">
          <span class="font-semibold">System Logs</span>
          <div class="space-x-2">
            <button class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300" @click="clearLogs">Clear</button>
            <button class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300" @click="autoScroll = !autoScroll">Auto-scroll</button>
          </div>
        </div>
        <div class="h-32 overflow-y-auto bg-gray-100 rounded p-2 mb-4" ref="logContainer">
          <div v-for="(log, idx) in logs" :key="idx" class="text-xs text-gray-700">{{ log }}</div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <span class="font-semibold">Sensor Debug</span>
            <div class="space-y-2 mt-2">
              <div v-for="sensor in sensors" :key="sensor.label" class="flex items-center justify-between">
                <span>{{ sensor.label }}: <span class="font-mono">{{ sensor.value }}</span></span>
                <button class="px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 ml-2" @click="calibrate(sensor.label)">Calibrate</button>
              </div>
            </div>
          </div>
          <div>
            <span class="font-semibold">System Tests</span>
            <div class="space-y-2 mt-2">
              <div v-for="test in systemTests" :key="test.label" class="flex items-center justify-between">
                <span>{{ test.label }}</span>
                <span class="text-sm font-mono">{{ test.status }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { api } from '../services/api'

// Status Section
const isConnected = ref(true)
const batteryLevel = ref(85)
const temperature = ref(25.6)
const recentActivity = ref([
  { id: 1, message: 'System started', time: '2 minutes ago' },
  { id: 2, message: 'Sensors calibrated', time: '5 minutes ago' }
])

// Configuration Section
const robotName = ref('Robbie')
const maxSpeed = ref(500)
const sensorUpdateRate = ref(60)
const sensorThreshold = ref(100)
const pidP = ref(1)
const pidI = ref(0.1)
const pidD = ref(0.05)

// Control Section
const speed = ref(50)

// Visualization Section
const cameraAngle = ref(0)
const cameraHeight = ref(0)
const position = ref({ x: 0, y: 0, z: 0 })
const rotationAngle = ref(0)

// Audio & Transcription State
const audioLevelDb = ref(-100)
const lastTranscription = ref('')

// Map dB range [-100, 0] to [0, 100] percent
const audioLevelPercent = computed(() => {
  let percent = (audioLevelDb.value + 100)
  if (percent < 0) percent = 0
  if (percent > 100) percent = 100
  return percent
})

// Color for VU meter (green/yellow/red)
const audioLevelColor = computed(() => {
  if (audioLevelDb.value > -20) return '#ef4444' // red
  if (audioLevelDb.value > -50) return '#f59e42' // yellow
  return '#22c55e' // green
})

// Debug Section
const logs = ref([
  '[19:20:43.897] Sample debug message',
  '[19:20:45.899] Sample debug message'
])
const autoScroll = ref(true)
const logContainer = ref<HTMLElement | null>(null)

onMounted(() => {
  if (autoScroll.value && logContainer.value) {
    nextTick(() => {
      logContainer.value!.scrollTop = logContainer.value!.scrollHeight
    })
  }
  api.registerAudioLevelListener((db: number) => {
    audioLevelDb.value = db
  })
  api.registerTranscriptionListener((text: string) => {
    lastTranscription.value = text
  })
})

function clearLogs() {
  logs.value = []
}

const sensors = ref([
  { label: 'Front Distance', value: '25.4 cm' },
  { label: 'Rear Distance', value: '30.2 cm' },
  { label: 'Left Distance', value: '15.7 cm' },
  { label: 'Right Distance', value: '18.9 cm' },
  { label: 'Battery Voltage', value: '11.8V' },
  { label: 'Motor Temperature', value: '35.2°C' }
])
function calibrate(label: string) {
  // Placeholder for sensor calibration logic
  alert(`Calibrating ${label}`)
}

const systemTests = ref([
  { label: 'Motor System Test', status: 'Not Run' },
  { label: 'Sensor System Test', status: 'Not Run' },
  { label: 'Communication Test', status: 'Not Run' },
  { label: 'Battery System Test', status: 'Not Run' }
])
</script>

<style scoped>
.audio-vu {
  transition: width 0.2s ease;
}
.child-friendly-transcription {
  font-size: 1.35rem;
  letter-spacing: 0.02em;
  min-height: 2.5rem;
}
input[type="range"]::-webkit-slider-thumb {
  background: #2563eb;
}
input[type="range"]::-moz-range-thumb {
  background: #2563eb;
}
input[type="range"]::-ms-thumb {
  background: #2563eb;
}
</style>
