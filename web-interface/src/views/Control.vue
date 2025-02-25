<template>
  <div class="space-y-6">
    <h2 class="text-2xl font-bold text-gray-900">Robot Control</h2>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Control Pad -->
      <div class="bg-white shadow sm:rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">Movement Control</h3>
          <div class="mt-5">
            <div class="grid grid-cols-3 gap-4 max-w-xs mx-auto">
              <!-- Forward -->
              <button
                @mousedown="startMovement('forward')"
                @mouseup="stopMovement"
                @mouseleave="stopMovement"
                class="col-start-2 bg-gray-100 rounded-lg p-4 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                ↑
              </button>
              <!-- Left -->
              <button
                @mousedown="startMovement('left')"
                @mouseup="stopMovement"
                @mouseleave="stopMovement"
                class="bg-gray-100 rounded-lg p-4 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                ←
              </button>
              <!-- Stop -->
              <button
                @click="emergencyStop"
                class="bg-red-100 rounded-lg p-4 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                ■
              </button>
              <!-- Right -->
              <button
                @mousedown="startMovement('right')"
                @mouseup="stopMovement"
                @mouseleave="stopMovement"
                class="bg-gray-100 rounded-lg p-4 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                →
              </button>
              <!-- Backward -->
              <button
                @mousedown="startMovement('backward')"
                @mouseup="stopMovement"
                @mouseleave="stopMovement"
                class="col-start-2 bg-gray-100 rounded-lg p-4 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                ↓
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Speed Control -->
      <div class="bg-white shadow sm:rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">Speed Control</h3>
          <div class="mt-5">
            <label for="speed" class="block text-sm font-medium text-gray-700">
              Speed: {{ speed }}%
            </label>
            <input
              type="range"
              id="speed"
              v-model="speed"
              min="0"
              max="100"
              class="mt-1 w-full"
              @input="updateSpeed"
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const speed = ref(50)

function startMovement(direction) {
  // TODO: Implement robot movement control
  console.log(`Moving ${direction} at speed ${speed.value}%`)
}

function stopMovement() {
  // TODO: Implement stop movement
  console.log('Stopping movement')
}

function emergencyStop() {
  // TODO: Implement emergency stop
  console.log('Emergency stop activated')
}

function updateSpeed() {
  // TODO: Implement speed update
  console.log(`Speed updated to ${speed.value}%`)
}
</script>
