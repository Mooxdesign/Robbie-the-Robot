<template>
  <div class="space-y-6">
    <h2 class="text-2xl font-bold text-gray-900">Robot Visualization</h2>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 3D Visualization -->
      <div class="lg:col-span-2 bg-white shadow sm:rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">3D View</h3>
          <div class="mt-5">
            <div ref="threeContainer" class="w-full h-96 bg-gray-100 rounded-lg"></div>
          </div>
        </div>
      </div>

      <!-- Controls and Info -->
      <div class="space-y-6">
        <!-- Camera Controls -->
        <div class="bg-white shadow sm:rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900">Camera Controls</h3>
            <div class="mt-5 space-y-4">
              <div>
                <label for="cameraAngle" class="block text-sm font-medium text-gray-700">
                  Camera Angle
                </label>
                <input
                  type="range"
                  id="cameraAngle"
                  v-model="cameraAngle"
                  min="0"
                  max="360"
                  class="mt-1 w-full"
                  @input="updateCamera"
                >
              </div>
              <div>
                <label for="cameraHeight" class="block text-sm font-medium text-gray-700">
                  Camera Height
                </label>
                <input
                  type="range"
                  id="cameraHeight"
                  v-model="cameraHeight"
                  min="1"
                  max="10"
                  step="0.1"
                  class="mt-1 w-full"
                  @input="updateCamera"
                >
              </div>
            </div>
          </div>
        </div>

        <!-- Robot State -->
        <div class="bg-white shadow sm:rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900">Robot State</h3>
            <div class="mt-5 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Position</label>
                <div class="mt-1 grid grid-cols-3 gap-4">
                  <div>
                    <span class="text-xs text-gray-500">X:</span>
                    <span class="ml-1">{{ position.x.toFixed(2) }}</span>
                  </div>
                  <div>
                    <span class="text-xs text-gray-500">Y:</span>
                    <span class="ml-1">{{ position.y.toFixed(2) }}</span>
                  </div>
                  <div>
                    <span class="text-xs text-gray-500">Z:</span>
                    <span class="ml-1">{{ position.z.toFixed(2) }}</span>
                  </div>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Rotation</label>
                <div class="mt-1">
                  <span class="text-xs text-gray-500">Angle:</span>
                  <span class="ml-1">{{ rotation.toFixed(2) }}°</span>
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
