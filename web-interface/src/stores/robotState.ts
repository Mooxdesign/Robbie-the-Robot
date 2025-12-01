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
  // Full config object loaded from /api/config (mirrors config.yaml)
  const config = ref<any>({})

  // LED animation state
  const ledAnimationState = ref({})

  // LED matrix state
  const ledMatrix = ref<any[][]>([])
  const joystick = ref<any>({ axes: [], buttons: [] })
  const motor = ref<any>({
    enabled: false,
    mode: 'arcade',
    target_left: 0,
    target_right: 0,
    left_speed: 0,
    right_speed: 0,
    left_arm_position: 0,
    right_arm_position: 0,
    head_pan: 0,
    head_tilt: 0,
  })

  function wakeRobot() {
    api.sendCommand({ type: 'wake' })
  }

  // --- Chat message history ---
  const chatMessages = ref([])

  // This is the ONLY place state is mutated:
  function updateFromBackend(state: any) {
    // Defensive: update only if present in state
    if (state.is_connected !== undefined) isConnected.value = state.is_connected
    if (state.robot_state !== undefined) robotState.value = state.robot_state
    if (state.battery_level !== undefined) batteryLevel.value = state.battery_level
    if (state.temperature !== undefined) temperature.value = state.temperature
    if (state.recent_activity !== undefined) recentActivity.value = state.recent_activity
    if (state.input_audio_level_db !== undefined) inputAudioLevelDb.value = state.input_audio_level_db
    if (state.output_audio_level_db !== undefined) outputAudioLevelDb.value = state.output_audio_level_db;
    if (state.led_animation !== undefined) ledAnimationState.value = state.led_animation;
    if (state.led_matrix !== undefined) ledMatrix.value = state.led_matrix;
    if (state.joystick !== undefined) joystick.value = state.joystick;
    if (state.motor !== undefined) motor.value = state.motor;
    // NEW: Update chatMessages if present
    if (Array.isArray(state.chat_history)) {
      chatMessages.value = state.chat_history.slice()
    }
    // ...add other fields as needed
  }

  async function loadConfigFromBackend() {
    try {
      const loaded: any = await api.getConfig()
      config.value = loaded || {}
    } catch (e) {
      console.error('Failed to load config from backend:', e)
    }
  }

  return {
    // State
    isConnected, robotState, batteryLevel, temperature, recentActivity,
    inputAudioLevelDb, outputAudioLevelDb,
    config,
    chatMessages,
    ledAnimationState,
    ledMatrix,
    joystick,
    motor,
    // Actions
    wakeRobot,
    updateFromBackend, loadConfigFromBackend
  }
})