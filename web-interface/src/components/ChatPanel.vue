<template>
  <div class="mb-6">
    <div class="chat-history">
      <div v-for="(msg, idx) in chatMessages" :key="idx" :class="msg.sender === 'user' ? 'chat-row user-row' : 'chat-row robot-row'">
        <span :class="msg.sender === 'user' ? 'chat-bubble user' : 'chat-bubble robot'">{{ msg.text }}</span>
      </div>
    </div>
    <form class="chat-form" @submit.prevent="submitChat">
      <input
        v-model="chatInput"
        type="text"
        placeholder="Type message for Robbie..."
        class="chat-input"
        autocomplete="off"
      />
      <button type="submit" class="chat-send-btn">Send</button>
    </form>
  </div>
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
  // Optimistic UI: show the user's message instantly
  robot.chatMessages.push({ sender: 'user', text: chatInput.value });
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
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1rem;
}
.chat-send-btn {
  padding: 0.5rem 1.2rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.chat-send-btn:hover {
  background: #174bb5;
}
.chat-history {
  margin-bottom: 1rem;
  max-height: 24rem;
  overflow-y: auto;
  padding-right: 0.5rem;
  min-height: 4rem;
}
.chat-row {
  display: flex;
  margin-bottom: 0.6rem;
}
.user-row {
  justify-content: flex-end;
}
.robot-row {
  justify-content: flex-start;
}
.chat-bubble {
  border-radius: 14px;
  padding: 0.7rem 1.1rem;
  max-width: 75%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  font-size: 1rem;
  word-break: break-word;
  margin-bottom: 0.2rem;
}
.user {
  background: #2563eb;
  color: #fff;
  margin-left: auto;
}
.robot {
  background: #e5e7eb;
  color: #222;
  margin-right: auto;
}
</style>
