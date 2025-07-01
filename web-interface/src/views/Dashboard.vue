<template>
  <SectionCard title="Status">
    <RobotStatus />
  </SectionCard>

  <SectionCard title="Robot Configuration">
    <div class="dashboard-config-grid">
      <ConfigGeneral />
      <ConfigSensors />
    </div>
  </SectionCard>

  <SectionCard title="LED Matrix">
    <LedMatrix />
  </SectionCard>

  <SectionCard title="Audio">
    <StereoMixDevice />
    <AudioLevels />
  </SectionCard>

  <SectionCard title="Chat">
    <ChatPanel />
  </SectionCard>

  <SectionCard title="Debug Console">
    <DebugConsole />
  </SectionCard>
</template>

<script setup lang="ts">
import SectionCard from '../components/SectionCard.vue';
import ConfigGeneral from '../components/ConfigGeneral.vue';
import ConfigSensors from '../components/ConfigSensors.vue';
import RobotStatus from '../components/RobotStatus.vue';
import RobotControl from '../components/RobotControl.vue';
import AudioLevels from '../components/AudioLevels.vue';
import StereoMixDevice from '../components/StereoMixDevice.vue';
import LedMatrix from '../components/LedMatrix.vue';
import ChatPanel from '../components/ChatPanel.vue';
import DebugConsole from '../components/DebugConsole.vue';
import { onMounted } from 'vue'
import { api } from '../services/api'
import { useRobotState } from '@/stores/robotState'

const robot = useRobotState()

// Listen for backend websocket state updates and update Pinia store
onMounted(() => {
  api.registerStateListener((state) => {
    robot.updateFromBackend(state)
  })
})

</script>

<style scoped>
.dashboard-status-grid,
.dashboard-config-grid,
.dashboard-control-grid,
.dashboard-visualization-grid,
.debug-panel-grid {
  display: grid;
  gap: 1.5rem;
}
.dashboard-status-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  margin-bottom: 2rem;
}
.dashboard-config-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}
.dashboard-control-grid,
.dashboard-visualization-grid,
.debug-panel-grid {
  grid-template-columns: 1fr 1fr;
}
@media (max-width: 900px) {
  .dashboard-config-grid,
  .dashboard-control-grid,
  .dashboard-visualization-grid,
  .debug-panel-grid {
    grid-template-columns: 1fr;
  }
}
.dashboard-title {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  color: #222;
}

</style>
