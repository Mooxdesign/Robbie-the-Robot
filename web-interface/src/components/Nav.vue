<template>
  <nav class="nav-root">
    <router-link
      to="/"
      class="nav-link"
      active-class="nav-link-active"
      exact
    >
      Dashboard
    </router-link>
    <span class="nav-separator">|</span>
    <router-link
      to="/visualization"
      class="nav-link"
      active-class="nav-link-active"
    >
      Camera / 3D Model
    </router-link>
  </nav>
</template>

<script setup lang="ts">
// No script needed for static nav
</script>

<style scoped>
.nav-root {
}
.nav-link {
  text-decoration: none;
  color: #222;
  font-size: 1.1rem;
  font-weight: 500;
  margin-right: 1rem;
}
.nav-link-active {
  color: #2563eb;
}
.nav-separator {
  margin: 0 0.5rem;
  color: #666;
}
</style>
