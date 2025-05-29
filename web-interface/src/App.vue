<template>
  <div class="min-h-screen bg-gray-100">

    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-gray-900">Robbie the Robot</h1>
            </div>

          </div>
        </div>
      </div>
    </nav>

    <div class="py-6">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <UnifiedDashboard />
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import UnifiedDashboard from './views/UnifiedDashboard.vue'
</script>

