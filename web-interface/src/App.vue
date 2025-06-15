<template>
  <div class="app-root">
    <Header />
    <main class="main-content">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

<script setup lang="ts">
import Header from './components/Header.vue';
import Footer from './components/Footer.vue';
</script>

<style>
.app-root {
  min-height: 100vh;
  background: #f4f6fa;
  display: flex;
  flex-direction: column;
}
.main-content {
  flex: 1;
  padding: 2.5rem 0;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>