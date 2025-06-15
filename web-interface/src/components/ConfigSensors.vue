<template>
  <div>
    <h3 class="section-card-title">Sensor Configuration</h3>
    <div class="mb-2">
      <label class="label-muted">Sensor Update Rate (Hz)</label>
      <input type="number"
             :value="robot.sensorUpdateRate"
             @input="robot.setSensorUpdateRate(Number($event.target.value))"
             class="input" />
    </div>
    <div>
      <label class="label-muted">Sensor Threshold</label>
      <input type="number"
             :value="robot.sensorThreshold"
             @input="robot.setSensorThreshold(Number($event.target.value))"
             class="input" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRobotState } from '@/stores/robotState'
const robot = useRobotState()
</script>
