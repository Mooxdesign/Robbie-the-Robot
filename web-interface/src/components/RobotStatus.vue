<template>
  <div class="status-root">
    <div class="status-header">
      <span class="status-label">Status:</span>
      <span :class="['status-indicator', isConnected ? robotState.toLowerCase() : 'disconnected']"></span>
      <span class="status-state mono">{{ isConnected ? robotState : 'Disconnected' }}</span>
      <button @click="wakeRobot" class="btn status-wake-btn">Wake Robot</button>
    </div>
    <div class="status-info">
      <div class="status-item">
        <span class="status-label">Battery</span>
        <span class="status-value mono">{{ batteryLevel }}%</span>
      </div>
      <div class="status-item">
        <span class="status-label">Temperature</span>
        <span class="status-value mono">{{ temperature }}°C</span>
      </div>

      <ul class="dashboard-list">
        <li v-for="activity in recentActivity" :key="activity.id" class="dashboard-list-item">
          <span>{{ activity.message }}</span>
          <span class="label-muted" style="font-size:0.85rem;">{{ activity.time }}</span>
        </li>
      </ul>
      <!--<pre>{{ allState }}</pre>-->

    </div>
  </div>
</template>

<script setup lang="ts">
import { useRobotState } from '@/stores/robotState'
import { computed } from 'vue'

const robot = useRobotState()

const isConnected = computed(() => robot.isConnected)
const robotState = computed(() => robot.robotState)
const batteryLevel = computed(() => robot.batteryLevel)
const temperature = computed(() => robot.temperature)
const recentActivity = computed(() => robot.recentActivity)
const allState = computed(() => JSON.stringify(robot, null, 2))
function wakeRobot() {
  robot.wakeRobot()
}
</script>

<style scoped>
.status-root {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 0.5px 1.5px rgba(0,0,0,0.05);
  padding: 1.4rem 1.7rem 1.2rem 1.7rem;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.status-header {
  display: flex;
  align-items: center;
  gap: 1.1rem;
  font-size: 1.15rem;
  font-weight: 600;
}
.status-label {
  color: #555;
  font-size: 1.05rem;
  font-weight: 500;
}
.status-indicator {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 10px;
  background: #bbb;
}
.status-indicator.listening {
  background: #22c55e;
}
.status-indicator.standby {
  background: #ef4444;
}
.status-indicator.disconnected {
  background: #666666;
}
.status-indicator.speaking {
  background: #2563eb
}
.status-state {
  color: #2563eb;
  font-size: 1.08rem;
  margin-right: 1.2rem;
}
.status-info {
  display: flex;
  gap: 2.5rem;
}
.status-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.status-value {
  font-size: 1.1rem;
  color: #222;
  font-weight: 500;
}
.status-wake-btn {
  margin-left: auto;
  font-size: 0.98rem;
  padding: 0.4em 1.1em;
}
@media (max-width: 700px) {
  .status-root {
    padding: 1rem;
  }
  .status-info {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
