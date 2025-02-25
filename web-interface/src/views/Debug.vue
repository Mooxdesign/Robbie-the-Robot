<template>
  <div class="space-y-6">
    <h2 class="text-2xl font-bold text-gray-900">Debug Console</h2>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Log Console -->
      <div class="bg-white shadow sm:rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <div class="flex justify-between items-center">
            <h3 class="text-lg leading-6 font-medium text-gray-900">System Logs</h3>
            <div class="space-x-3">
              <button
                @click="clearLogs"
                class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                Clear
              </button>
              <button
                @click="toggleAutoScroll"
                :class="[
                  autoScroll
                    ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
                    : 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500'
                ]"
                class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2"
              >
                Auto-scroll
              </button>
            </div>
          </div>
          <div class="mt-5">
            <div
              ref="logContainer"
              class="bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm"
            >
              <div
                v-for="(log, index) in logs"
                :key="index"
                :class="{
                  'text-red-400': log.level === 'error',
                  'text-yellow-400': log.level === 'warn',
                  'text-blue-400': log.level === 'info',
                  'text-gray-400': log.level === 'debug'
                }"
              >
                <span class="text-gray-500">[{{ log.timestamp }}]</span>
                <span class="ml-2">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Debug Controls -->
      <div class="space-y-6">
        <!-- Sensor Debug -->
        <div class="bg-white shadow sm:rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900">Sensor Debug</h3>
            <div class="mt-5 space-y-4">
              <div v-for="(sensor, name) in sensors" :key="name">
                <label :for="name" class="block text-sm font-medium text-gray-700">
                  {{ name }}
                </label>
                <div class="mt-1 flex items-center space-x-4">
                  <span class="text-sm text-gray-500">{{ sensor.value }}</span>
                  <button
                    @click="calibrateSensor(name)"
                    class="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Calibrate
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- System Tests -->
        <div class="bg-white shadow sm:rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900">System Tests</h3>
            <div class="mt-5 space-y-4">
              <button
                v-for="test in systemTests"
                :key="test.name"
                @click="runTest(test.name)"
                class="w-full inline-flex items-center justify-between px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                {{ test.name }}
                <span
                  :class="{
                    'bg-green-100 text-green-800': test.status === 'passed',
                    'bg-red-100 text-red-800': test.status === 'failed',
                    'bg-yellow-100 text-yellow-800': test.status === 'running',
                    'bg-gray-100 text-gray-800': !test.status
                  }"
                  class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                >
                  {{ test.status || 'Not Run' }}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const logContainer = ref(null)
const autoScroll = ref(true)
const logs = ref([])
const sensors = ref({
  'Front Distance': { value: '25.4 cm' },
  'Rear Distance': { value: '30.2 cm' },
  'Left Distance': { value: '15.7 cm' },
  'Right Distance': { value: '18.9 cm' },
  'Battery Voltage': { value: '11.8V' },
  'Motor Temperature': { value: '35.2°C' }
})

const systemTests = ref([
  { name: 'Motor System Test', status: '' },
  { name: 'Sensor System Test', status: '' },
  { name: 'Communication Test', status: '' },
  { name: 'Battery System Test', status: '' }
])

// Simulated log messages for demonstration
let logInterval
onMounted(() => {
  logInterval = setInterval(() => {
    const levels = ['debug', 'info', 'warn', 'error']
    const level = levels[Math.floor(Math.random() * levels.length)]
    addLog(`Sample ${level} message`, level)
  }, 2000)
})

onUnmounted(() => {
  clearInterval(logInterval)
})

function addLog(message, level = 'info') {
  const timestamp = new Date().toISOString().split('T')[1].slice(0, -1)
  logs.value.push({ message, level, timestamp })
  
  if (autoScroll.value && logContainer.value) {
    setTimeout(() => {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }, 0)
  }
}

function clearLogs() {
  logs.value = []
}

function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
}

function calibrateSensor(sensorName) {
  // TODO: Implement actual sensor calibration
  addLog(`Calibrating ${sensorName}...`, 'info')
}

async function runTest(testName) {
  const test = systemTests.value.find(t => t.name === testName)
  test.status = 'running'
  addLog(`Running ${testName}...`, 'info')

  // Simulate test running
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  // Randomly pass or fail for demonstration
  test.status = Math.random() > 0.5 ? 'passed' : 'failed'
  addLog(`${testName} ${test.status}`, test.status === 'passed' ? 'info' : 'error')
}
</script>
