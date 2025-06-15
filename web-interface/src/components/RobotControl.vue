<template>
  <SectionCard title="Robot Control">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Movement Control -->
      <div>
        <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">Movement Control</h3>
        <div class="flex justify-center space-x-4">
          <button class="control-btn">↑</button>
        </div>
        <div class="flex justify-center space-x-4 mt-2">
          <button class="control-btn">←</button>
          <button class="control-btn stop">■</button>
          <button class="control-btn">→</button>
        </div>
        <div class="flex justify-center mt-2">
          <button class="control-btn">↓</button>
        </div>
      </div>
      <!-- Speed Control -->
      <div>
        <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">Speed Control</h3>
        <div class="flex items-center space-x-4">
          <input type="range" min="0" max="100" v-model="speed" class="input" />
          <span class="mono">Speed: {{ speed }}%</span>
        </div>
      </div>
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import SectionCard from './SectionCard.vue'
import { ref } from 'vue'
// TODO: Replace v-model with Pinia store or emit events to backend
const speed = ref(50)
</script>

<style scoped>
.control-btn {
  width: 48px;
  height: 48px;
  background: #e5e7eb;
  border: none;
  border-radius: 8px;
  font-size: 1.45rem;
  font-weight: bold;
  margin: 0 0.15rem;
  cursor: pointer;
  transition: background 0.18s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.control-btn:hover {
  background: #d1d5db;
}
.control-btn.stop {
  background: #9ca3af;
  color: #fff;
}
</style>
