<template>
  <div class="space-y-6">
    <h2 class="text-2xl font-bold text-gray-900">Robot Configuration</h2>

    <div class="bg-white shadow sm:rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <form @submit.prevent="saveConfig">
          <!-- General Settings -->
          <div class="space-y-6">
            <div>
              <h3 class="text-lg leading-6 font-medium text-gray-900">General Settings</h3>
              <div class="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                <div class="sm:col-span-3">
                  <label for="robotName" class="block text-sm font-medium text-gray-700">Robot Name</label>
                  <div class="mt-1">
                    <input
                      type="text"
                      id="robotName"
                      v-model="config.robotName"
                      class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    >
                  </div>
                </div>

                <div class="sm:col-span-3">
                  <label for="maxSpeed" class="block text-sm font-medium text-gray-700">Maximum Speed (mm/s)</label>
                  <div class="mt-1">
                    <input
                      type="number"
                      id="maxSpeed"
                      v-model="config.maxSpeed"
                      class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- Sensor Configuration -->
            <div>
              <h3 class="text-lg leading-6 font-medium text-gray-900">Sensor Configuration</h3>
              <div class="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                <div class="sm:col-span-3">
                  <label for="sensorUpdateRate" class="block text-sm font-medium text-gray-700">Sensor Update Rate (Hz)</label>
                  <div class="mt-1">
                    <input
                      type="number"
                      id="sensorUpdateRate"
                      v-model="config.sensorUpdateRate"
                      class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    >
                  </div>
                </div>

                <div class="sm:col-span-3">
                  <label for="sensorThreshold" class="block text-sm font-medium text-gray-700">Sensor Threshold</label>
                  <div class="mt-1">
                    <input
                      type="number"
                      id="sensorThreshold"
                      v-model="config.sensorThreshold"
                      class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- Motor Configuration -->
            <div>
              <h3 class="text-lg leading-6 font-medium text-gray-900">Motor Configuration</h3>
              <div class="mt-6 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                <div class="sm:col-span-3">
                  <label for="motorPID_P" class="block text-sm font-medium text-gray-700">PID P Value</label>
                  <div class="mt-1">
                    <input
                      type="number"
                      id="motorPID_P"
                      v-model="config.motorPID.P"
                      step="0.1"
                      class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    >
                  </div>
                </div>

                <div class="sm:col-span-3">
                  <label for="motorPID_I" class="block text-sm font-medium text-gray-700">PID I Value</label>
                  <div class="mt-1">
                    <input
                      type="number"
                      id="motorPID_I"
                      v-model="config.motorPID.I"
                      step="0.1"
                      class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    >
                  </div>
                </div>

                <div class="sm:col-span-3">
                  <label for="motorPID_D" class="block text-sm font-medium text-gray-700">PID D Value</label>
                  <div class="mt-1">
                    <input
                      type="number"
                      id="motorPID_D"
                      v-model="config.motorPID.D"
                      step="0.1"
                      class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-6">
            <button
              type="submit"
              class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Save Configuration
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const config = ref({
  robotName: 'Robbie',
  maxSpeed: 500,
  sensorUpdateRate: 60,
  sensorThreshold: 100,
  motorPID: {
    P: 1.0,
    I: 0.1,
    D: 0.05
  }
})

async function saveConfig() {
  try {
    // TODO: Implement configuration saving
    console.log('Saving configuration:', config.value)
    // await api.saveConfig(config.value)
  } catch (error) {
    console.error('Failed to save configuration:', error)
  }
}
</script>
