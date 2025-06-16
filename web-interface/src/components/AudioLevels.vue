<template>
  <div class="audio-levels-root">
    <div class="audio-row">
      <span class="audio-label">Input Level</span>
      <div class="audio-bar-bg">
        <div
          class="audio-bar-fill"
          :style="{ width: inputPercent + '%', background: inputColor }"
        />
      </div>
      <span class="mono audio-db" :style="{ color: inputColor }">{{ inputDb.toFixed(1) }} dB</span>
    </div>
    <div class="audio-row">
      <span class="audio-label">Output Level</span>
      <div class="audio-bar-bg">
        <div
          class="audio-bar-fill"
          :style="{ width: outputPercent + '%', background: outputColor }"
        />
      </div>
      <span class="mono audio-db" :style="{ color: outputColor }">{{ outputDb.toFixed(1) }} dB</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRobotState } from '@/stores/robotState';

const robot = useRobotState();

const inputDb = computed(() => robot.inputAudioLevelDb);
const outputDb = computed(() => robot.outputAudioLevelDb);

const inputPercent = computed(() => {
  let percent = inputDb.value + 100;
  if (percent < 0) percent = 0;
  if (percent > 100) percent = 100;
  return percent;
});
const outputPercent = computed(() => {
  let percent = outputDb.value + 100;
  if (percent < 0) percent = 0;
  if (percent > 100) percent = 100;
  return percent;
});

function getColor(db: number) {
  if (db > -20) return '#ef4444'; // red
  if (db > -50) return '#f59e42'; // yellow
  return '#22c55e'; // green
}
const inputColor = computed(() => getColor(inputDb.value));
const outputColor = computed(() => getColor(outputDb.value));
</script>

<style scoped>
.audio-levels-root {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.audio-row {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}
.audio-label {
  color: #555;
  font-size: 1.02rem;
  font-weight: 500;
  min-width: 90px;
}
.audio-bar-bg {
  background: #e5e7eb;
  border-radius: 8px;
  width: 140px;
  height: 18px;
  overflow: hidden;
  margin-right: 0.8rem;
  box-shadow: 0 1px 2px #0001;
}
.audio-bar-fill {
  height: 100%;
  border-radius: 8px;
  transition: width 0.2s, background 0.2s;
}
.audio-db {
  min-width: 56px;
  text-align: right;
  font-size: 1.03rem;
}
.audio-bar-bg {
  width: 190px;
  height: 22px;
  background: #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}
.audio-bar-fill {
  height: 100%;
  border-radius: 12px 0 0 12px;
  transition: width 0.2s;
}
</style>
