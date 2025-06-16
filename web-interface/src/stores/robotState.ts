import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../services/api'

export const useRobotState = defineStore('robotState', () => {
  // State
  const isConnected = ref(true)
  const robotState = ref('STANDBY')
  const batteryLevel = ref(85)
  const temperature = ref(25.6)
  const recentActivity = ref([
    { id: 1, message: 'System started', time: '2 minutes ago' },
    { id: 2, message: 'Sensors calibrated', time: '5 minutes ago' }
  ])
  const inputAudioLevelDb = ref(-100)
  const outputAudioLevelDb = ref(-100)
  // Config fields
  const robotName = ref('Robbie')
  const maxSpeed = ref(500)
  const sensorUpdateRate = ref(60)
  const sensorThreshold = ref(100)
  const pidP = ref(1)
  const pidI = ref(0.1)
  const pidD = ref(0.05)

  // Actions (global functions)
  // UI actions only emit commands, never mutate state directly
  function wakeRobot() {
    api.sendCommand({ type: 'wake' })
    // Do NOT update local state here; backend will emit update
  }
  function setRobotName(name: string) {
    api.sendCommand({ type: 'set_robot_name', value: name })
  }
  function setMaxSpeed(value: number) {
    api.sendCommand({ type: 'set_max_speed', value })
  }
  function setSensorUpdateRate(value: number) {
    api.sendCommand({ type: 'set_sensor_update_rate', value })
  }
  function setSensorThreshold(value: number) {
    api.sendCommand({ type: 'set_sensor_threshold', value })
  }
  function setPidP(value: number) {
    api.sendCommand({ type: 'set_pid_p', value })
  }
  function setPidI(value: number) {
    api.sendCommand({ type: 'set_pid_i', value })
  }
  function setPidD(value: number) {
    api.sendCommand({ type: 'set_pid_d', value })
  }

  // This is the ONLY place state is mutated:
  function updateFromBackend(state: any) {
    // Defensive: update only if present in state
    if (state.robot_name !== undefined) robotName.value = state.robot_name
    if (state.max_speed !== undefined) maxSpeed.value = state.max_speed
    if (state.sensor_update_rate !== undefined) sensorUpdateRate.value = state.sensor_update_rate
    if (state.sensor_threshold !== undefined) sensorThreshold.value = state.sensor_threshold
    if (state.pid_p !== undefined) pidP.value = state.pid_p
    if (state.pid_i !== undefined) pidI.value = state.pid_i
    if (state.pid_d !== undefined) pidD.value = state.pid_d
    if (state.is_connected !== undefined) isConnected.value = state.is_connected
    if (state.robot_state !== undefined) robotState.value = state.robot_state
    if (state.battery_level !== undefined) batteryLevel.value = state.battery_level
    if (state.temperature !== undefined) temperature.value = state.temperature
    if (state.recent_activity !== undefined) recentActivity.value = state.recent_activity
    if (state.input_audio_level_db !== undefined) inputAudioLevelDb.value = state.input_audio_level_db
    if (state.output_audio_level_db !== undefined) outputAudioLevelDb.value = state.output_audio_level_db;
    // ...add other fields as needed
  }

  return {
    // State
    isConnected, robotState, batteryLevel, temperature, recentActivity,
    inputAudioLevelDb, outputAudioLevelDb,
    robotName, maxSpeed, sensorUpdateRate, sensorThreshold, pidP, pidI, pidD,
    // Actions
    wakeRobot, setRobotName, setMaxSpeed, setSensorUpdateRate, setSensorThreshold, setPidP, setPidI, setPidD, updateFromBackend
  }
})
