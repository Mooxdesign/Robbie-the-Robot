<template>
  <SectionCard title="Debug Console">
    <div style="min-height:180px;">
      <div ref="logContainer" class="debug-log-container" style="height:120px; overflow:auto; background:#f7f7f7; border-radius:6px; padding:0.75rem; font-size:0.97rem;">
        <div v-for="(log, idx) in logs" :key="idx">{{ log }}</div>
      </div>
      <div class="flex justify-end mt-2">
        <button class="btn" @click="clearLogs">Clear Logs</button>
      </div>
      <div class="mt-4">
        <h4 class="section-card-title">System Tests</h4>
        <div v-for="(test, idx) in systemTests" :key="idx" class="flex items-center space-x-4 mb-2">
          <span>{{ test.label }}</span>
          <span class="mono">{{ test.status }}</span>
        </div>
      </div>
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import SectionCard from './SectionCard.vue'
import { ref, watch, nextTick, onMounted } from 'vue'
const logs = ref([
  '[19:20:43.897] Sample debug message',
  '[19:20:45.899] Sample debug message'
])
const logContainer = ref(null)
const autoScroll = ref(true)

// Auto-scroll when logs change
watch(logs, () => {
  if (autoScroll.value && logContainer.value) {
    nextTick(() => {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    });
  }
});
const systemTests = ref([
  { label: 'Motor System Test', status: 'Not Yet Implemented' },
  { label: 'Sensor System Test', status: 'Not Yet Implemented' },
  { label: 'Communication Test', status: 'Not Yet Implemented' },
  { label: 'Battery System Test', status: 'Not Yet Implemented' }
])
function clearLogs() {
  logs.value = []
}
</script>

<style scoped>
.debug-card {
  margin-bottom: 2rem;
}
.debug-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.7rem;
}
.debug-btn-group {
  display: flex;
  gap: 0.5rem;
}
.debug-log-box {
  height: 8rem;
  overflow-y: auto;
  background: #f3f4f6;
  border-radius: 6px;
  padding: 0.7rem;
  margin-bottom: 1rem;
}
.debug-log-entry {
  font-size: 0.89rem;
  color: #444;
  margin-bottom: 0.2rem;
}
.debug-panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.2rem;
}
.debug-label {
  font-weight: 600;
  color: #374151;
}
.debug-sensor-list, .debug-test-list {
  margin-top: 0.5rem;
}
.debug-sensor-row, .debug-test-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
</style>
