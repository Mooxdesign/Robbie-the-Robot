<template>
  <nav class="header-root">
    <div class="header-inner">
      <div class="header-row">
        <div class="header-logo-row">
          <!-- Optional logo slot -->
          <slot name="logo"></slot>
          <h1 class="header-title">Robbie the Robot Dashboard</h1>
        </div>
        <div class="header-nav">
          <Nav />
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import Nav from './Nav.vue';
// No script logic needed for static header
</script>

<style scoped>
.header-root {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
}
.header-logo-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.header-nav {
  display: flex;
  align-items: center;
}
.header-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #222;
  margin-left: 0.5rem;
  letter-spacing: 0.01em;
}
</style>
