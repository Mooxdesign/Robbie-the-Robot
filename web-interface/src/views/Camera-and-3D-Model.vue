<template>
  <div class="visualization-root">
    <h2 class="visualization-title">Robot Visualization</h2>

    <div class="visualization-grid">
      <!-- 3D Visualization -->
      <div class="visualization-card visualization-3d">
        <div class="visualization-card-inner">
          <h3 class="visualization-section-title">3D View</h3>
          <div class="visualization-section-space">
            <div ref="threeContainer" class="visualization-3d-canvas"></div>
          </div>
        </div>
      </div>

      <!-- Controls and Info -->
      <div class="visualization-root">
        <!-- Camera Controls -->
        <div class="bg-white shadow sm:rounded-lg">
          <div class="visualization-card-inner">
            <h3 class="visualization-section-title">Camera Controls</h3>
            <div class="visualization-section-space space-y-4">
              <div>
                <label for="cameraAngle" class="visualization-label">
                  Camera Angle
                </label>
                <input
                  type="range"
                  id="cameraAngle"
                  v-model="cameraAngle"
                  min="0"
                  max="360"
                  class="visualization-range"
                  @input="updateCamera"
                >
              </div>
              <div>
                <label for="cameraHeight" class="visualization-label">
                  Camera Height
                </label>
                <input
                  type="range"
                  id="cameraHeight"
                  v-model="cameraHeight"
                  min="1"
                  max="10"
                  step="0.1"
                  class="visualization-range"
                  @input="updateCamera"
                >
              </div>
            </div>
          </div>
        </div>

        <!-- Robot State -->
        <div class="bg-white shadow sm:rounded-lg">
          <div class="visualization-card-inner">
            <h3 class="visualization-section-title">Robot State</h3>
            <div class="visualization-section-space space-y-4">
              <div>
                <label class="visualization-label">Position</label>
                <div class="mt-1 visualization-pos-grid">
                  <div>
                    <span class="visualization-label-muted">X:</span>
                    <span class="visualization-label-value">{{ position.x.toFixed(2) }}</span>
                  </div>
                  <div>
                    <span class="visualization-label-muted">Y:</span>
                    <span class="visualization-label-value">{{ position.y.toFixed(2) }}</span>
                  </div>
                  <div>
                    <span class="visualization-label-muted">Z:</span>
                    <span class="visualization-label-value">{{ position.z.toFixed(2) }}</span>
                  </div>
                </div>
              </div>
              <div>
                <label class="visualization-label">Rotation</label>
                <div class="mt-1">
                  <span class="visualization-label-muted">Angle:</span>
                  <span class="visualization-label-value">{{ rotation.toFixed(2) }}°</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

const threeContainer = ref(null)
const cameraAngle = ref(45)
const cameraHeight = ref(5)
const position = ref({ x: 0, y: 0, z: 0 })
const rotation = ref(0)

let scene, camera, renderer, controls, robot

onMounted(() => {
  initThree()
  animate()
})

onUnmounted(() => {
  if (renderer) {
    renderer.dispose()
  }
})

function initThree() {
  // Scene setup
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf3f4f6)

  // Camera setup
  camera = new THREE.PerspectiveCamera(
    75,
    threeContainer.value.clientWidth / threeContainer.value.clientHeight,
    0.1,
    1000
  )
  camera.position.set(5, 5, 5)
  camera.lookAt(0, 0, 0)

  // Renderer setup
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(threeContainer.value.clientWidth, threeContainer.value.clientHeight)
  threeContainer.value.appendChild(renderer.domElement)

  // Controls setup
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6)
  directionalLight.position.set(10, 10, 10)
  scene.add(directionalLight)

  // Grid helper
  const gridHelper = new THREE.GridHelper(10, 10)
  scene.add(gridHelper)

  // Create robot representation
  createRobot()

  // Handle window resize
  window.addEventListener('resize', onWindowResize)
}

function createRobot() {
  const geometry = new THREE.BoxGeometry(1, 0.5, 1.5)
  const material = new THREE.MeshStandardMaterial({ color: 0x3b82f6 })
  robot = new THREE.Mesh(geometry, material)
  scene.add(robot)

  // Add wheels
  const wheelGeometry = new THREE.CylinderGeometry(0.2, 0.2, 0.1, 32)
  const wheelMaterial = new THREE.MeshStandardMaterial({ color: 0x1f2937 })

  const wheels = [
    { x: -0.6, z: 0.5 },
    { x: 0.6, z: 0.5 },
    { x: -0.6, z: -0.5 },
    { x: 0.6, z: -0.5 }
  ]

  wheels.forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial)
    wheel.position.set(pos.x, -0.2, pos.z)
    wheel.rotation.z = Math.PI / 2
    robot.add(wheel)
  })
}

function animate() {
  requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

function updateCamera() {
  const angle = (cameraAngle.value * Math.PI) / 180
  const height = cameraHeight.value
  const radius = 5

  camera.position.x = radius * Math.cos(angle)
  camera.position.z = radius * Math.sin(angle)
  camera.position.y = height
  camera.lookAt(0, 0, 0)
}

function onWindowResize() {
  camera.aspect = threeContainer.value.clientWidth / threeContainer.value.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(threeContainer.value.clientWidth, threeContainer.value.clientHeight)
}

// TODO: Implement real-time position and rotation updates from robot
</script>

<style scoped>
.visualization-root {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}
.visualization-title {
  font-size: 2rem;
  font-weight: 800;
  color: #222;
  margin-bottom: 1.2rem;
}
.visualization-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}
.visualization-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 0.5px 1.5px rgba(0,0,0,0.05);
  overflow: hidden;
}
.visualization-3d {
  grid-column: 1 / span 1;
}
.visualization-card-inner {
  padding: 1.5rem;
}
.visualization-section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #222;
  margin-bottom: 1rem;
}
.visualization-section-space {
  margin-top: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.visualization-3d-canvas {
  width: 100%;
  height: 24rem;
  background: #f3f4f6;
  border-radius: 10px;
  min-height: 300px;
}
.visualization-controls {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.visualization-label {
  font-size: 1rem;
  color: #555;
  font-weight: 500;
  display: block;
  margin-bottom: 0.3rem;
}
.visualization-range {
  width: 100%;
  margin-top: 0.2rem;
}
.visualization-label-muted {
  font-size: 0.9rem;
  color: #888;
}
.visualization-label-value {
  margin-left: 0.4rem;
  font-family: 'Fira Mono', 'Consolas', monospace;
  font-size: 1rem;
}
.visualization-pos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.1rem;
  margin-top: 0.2rem;
}
@media (max-width: 900px) {
  .visualization-grid {
    grid-template-columns: 1fr;
  }
}
</style>
