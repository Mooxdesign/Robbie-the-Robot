<template>
  <SectionCard title="Chat">
    <div class="mb-6">
      <div class="chat-history">
        <div v-for="(msg, idx) in chatMessages" :key="idx" :class="['flex mb-2', msg.sender === 'user' ? 'justify-end' : 'justify-start']">
          <span :class="['chat-bubble', msg.sender]">{{ msg.text }}</span>
        </div>
      </div>
      <form @submit.prevent="submitChat">
        <input
          v-model="chatInput"
          type="text"
          placeholder="Type message for Robbie..."
          class="input chat-input"
          autocomplete="off"
        />
        <button type="submit" class="btn">Send</button>
      </form>
    </div>
  </SectionCard>
</template>

<script setup lang="ts">
import SectionCard from './SectionCard.vue'
import { ref, computed } from 'vue'
import { api } from '../services/api'
import { useRobotState } from '@/stores/robotState'
const robot = useRobotState()
const chatInput = ref("");

function submitChat() {
  if (!chatInput.value.trim()) return;
  // Optionally emit event for logging
  // emit('user-message', chatInput.value)
  api.sendChat(chatInput.value);
  chatInput.value = "";
}

const chatMessages = computed(() => robot.chatMessages)
</script>

<style scoped>
.chat-form {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0;
}
.chat-input {
  flex: 1;
  margin-right: 0.5rem;
}
.chat-form {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0;
}
.chat-input {
  flex: 1;
  margin-right: 0.5rem;
}
.chat-card {
  margin-bottom: 2rem;
}
.chat-history {
  margin-bottom: 1rem;
  max-height: 16rem;
  overflow-y: auto;
  padding-right: 0.5rem;
}
.chat-bubble {
  border-radius: 12px;
  padding: 0.7rem 1.1rem;
  max-width: 75%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  font-size: 1rem;
  margin-bottom: 0.4rem;
  word-break: break-word;
}
.chat-bubble.user {
  background: #2563eb;
  color: #fff;
  margin-left: auto;
}
.chat-bubble.robot {
  background: #e5e7eb;
  color: #222;
  margin-right: auto;
}
</style>
