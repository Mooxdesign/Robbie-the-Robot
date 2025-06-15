<template>
  <footer class="dashboard-footer">
    <div class="footer-inner">
      <span class="footer-copyright">
        © {{ new Date().getFullYear() }} Robbie the Robot — All rights reserved until the robots revolt 🤖
      </span>
      <a
        class="footer-link"
        href="https://github.com/Mooxdesign/Robbie-the-Robot"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Robbie the Robot on GitHub"
      >
        <svg class="footer-github-icon" viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.799 8.205 11.387.6.111.82-.261.82-.577 0-.285-.011-1.04-.017-2.04-3.338.726-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.085 1.84 1.237 1.84 1.237 1.07 1.834 2.807 1.304 3.492.997.108-.775.419-1.305.762-1.605-2.665-.304-5.466-1.332-5.466-5.932 0-1.31.469-2.381 1.236-3.221-.124-.303-.535-1.523.117-3.176 0 0 1.008-.322 3.301 1.23A11.51 11.51 0 0 1 12 6.844c1.022.005 2.051.138 3.014.404 2.291-1.553 3.297-1.23 3.297-1.23.654 1.653.243 2.873.12 3.176.77.84 1.235 1.911 1.235 3.221 0 4.61-2.804 5.625-5.475 5.921.43.371.823 1.102.823 2.222 0 1.604-.015 2.898-.015 3.293 0 .319.216.694.825.576C20.565 21.796 24 17.297 24 12c0-6.63-5.37-12-12-12z"/>
        </svg>
        <span class="footer-link-text">GitHub</span>
      </a>
    </div>
  </footer>
</template>

<script setup lang="ts">
// Pure presentational footer
</script>

<style scoped>
.dashboard-footer {
  margin-top: 3rem;
  padding: 1.2rem 0 1.3rem 0;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  color: #555;
  font-size: 1rem;
  text-align: center;
}
.footer-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}
.footer-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  color: #222;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.15s;
}
.footer-link:hover {
  color: #2563eb;
}
.footer-github-icon {
  vertical-align: middle;
}
.footer-link-text {
  font-size: 1.01em;
}
</style>
