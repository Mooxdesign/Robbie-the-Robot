<template>
  <div class="card">
    <template v-if="title">
      <h3 class="section-card-title">{{ title }}</h3>
    </template>
    <slot />
  </div>
</template>

<script setup lang="ts">

defineProps({
  title: {
    type: String,
    default: ''
  }
})
</script>


