<template>
  <div>
    <h3 class="section-card-title" style="font-size:1.1rem; margin-bottom:0.5rem;">General Settings</h3>
    <div class="mb-2">
      <label class="label-muted">Robot Name</label>
      <input type="text"
             :value="robot.robotName"
             @input="robot.setRobotName($event.target.value)"
             class="input" />
    </div>
    <div>
      <label class="label-muted">Maximum Speed (mm/s)</label>
      <input type="number"
             :value="robot.maxSpeed"
             @input="robot.setMaxSpeed(Number($event.target.value))"
             class="input" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRobotState } from '@/stores/robotState'
const robot = useRobotState()
</script>
