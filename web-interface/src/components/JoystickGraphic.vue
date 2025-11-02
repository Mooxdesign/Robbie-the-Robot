<template>
  <div class="xbox-wrap" :class="{ disconnected: !connected }">
    <div class="controller">
      <!-- Inline the base SVG so we can query its elements -->
      <div ref="svgHost" class="base-svg" v-html="svgRaw" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, nextTick, watchEffect } from 'vue'
// Import the raw SVG markup so it renders inline
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import svgRaw from '@/assets/xbox-controller.svg?raw'

interface Props {
  axes: number[]
  buttons: boolean[]
  connected?: boolean
}

const props = defineProps<Props>()

function clamp(v: number) { return Math.max(-1, Math.min(1, v ?? 0)) }

const lx = computed(() => clamp(props.axes?.[0] ?? 0))
const ly = computed(() => clamp(props.axes?.[1] ?? 0))
const rx = computed(() => clamp(props.axes?.[2] ?? 0))
const ry = computed(() => clamp(props.axes?.[3] ?? 0))
const ltPct = computed(() => (clamp(props.axes?.[4] ?? -1) + 1) / 2)
const rtPct = computed(() => (clamp(props.axes?.[5] ?? -1) + 1) / 2)

const connected = computed(() => props.connected ?? (props.axes?.length || props.buttons?.length) > 0)

function isOn(i: number) { return !!props.buttons?.[i] }

// Inline SVG host and measured positions
const svgHost = ref<HTMLElement | null>(null)
const abxy = ref<Record<string, { x: number, y: number, r: number }>>({})
const dpad = ref<{ up?: SVGGraphicsElement, down?: SVGGraphicsElement, left?: SVGGraphicsElement, right?: SVGGraphicsElement }>({})
const sysBtns = ref<{ view?: SVGGraphicsElement, menu?: SVGGraphicsElement, xbox?: SVGGraphicsElement }>({})
const bumpers = ref<{ lb?: SVGGraphicsElement, rb?: SVGGraphicsElement }>({})
const sticks = ref<{ ls?: SVGGraphicsElement, rs?: SVGGraphicsElement }>({})
let ltBar: SVGRectElement | null = null
let rtBar: SVGRectElement | null = null
let lsGroup: SVGGElement | null = null
let rsGroup: SVGGElement | null = null

onMounted(async () => {
  await nextTick()
  const root = svgHost.value?.querySelector('svg') as SVGSVGElement | null
  if (!root) return
  // Known ids from the Wikimedia SVG corresponding to ABXY colors
  const ids = {
    X: 'path4959', // blue
    A: 'path4961', // green
    Y: 'path4967', // yellow
    B: 'path4971'  // red
  } as const
  const res: Record<string, { x: number, y: number, r: number }> = {}
  Object.entries(ids).forEach(([key, id]) => {
    const el = root.getElementById(id) as SVGGraphicsElement | null
    if (!el) return
    const bb = el.getBBox()
    const cx = bb.x + bb.width / 2
    const cy = bb.y + bb.height / 2
    const r = Math.min(bb.width, bb.height) * 0.5 * 0.75
    res[key] = { x: cx, y: cy, r }
  })
  abxy.value = res

  // Reactively toggle visual highlight classes directly on the inline SVG
  const pressToId: Record<number, string> = {
    0: ids.A, // A
    1: ids.B, // B
    2: ids.X, // X
    3: ids.Y  // Y
  }
  watchEffect(() => {
    const btns = props.buttons || []
    Object.entries(pressToId).forEach(([idxStr, svgId]) => {
      const idx = Number(idxStr)
      const el = root.getElementById(svgId)
      if (!el) return
      if (btns[idx]) {
        el.classList.add('svg-active')
      } else {
        el.classList.remove('svg-active')
      }
    })
  })

  // Heuristic: find the 4 D-pad shapes near the central cross area by bbox
  // Expected approximate region from prior manual overlay: expand bounds for safety
  const candidates = Array.from(root.querySelectorAll<SVGGraphicsElement>('path,rect,polygon'))
    .map(el => ({ el, bb: el.getBBox() }))
    .filter(({ bb }) => bb.width > 6 && bb.height > 6 &&
      bb.x + bb.width / 2 > 260 && bb.x + bb.width / 2 < 440 &&
      bb.y + bb.height / 2 > 220 && bb.y + bb.height / 2 < 360)

  // Pick the 4 largest by area (most likely the cross arms)
  candidates.sort((a, b) => (b.bb.width * b.bb.height) - (a.bb.width * a.bb.height))
  const top4 = candidates.slice(0, 4)

  if (top4.length === 4) {
    // Assign by min/max center positions
    const centers = top4
      // Prefer arm-like shapes (horizontal or vertical orientation)
      .filter(c => c.bb.width > c.bb.height * 0.7 || c.bb.height > c.bb.width * 0.7)
      .map(c => ({
      el: c.el,
      cx: c.bb.x + c.bb.width / 2,
      cy: c.bb.y + c.bb.height / 2
    }))
    if (centers.length >= 4) {
      const up = centers.reduce((p, c) => (c.cy < p.cy ? c : p))
      const down = centers.reduce((p, c) => (c.cy > p.cy ? c : p))
      const left = centers.reduce((p, c) => (c.cx < p.cx ? c : p))
      const right = centers.reduce((p, c) => (c.cx > p.cx ? c : p))
      dpad.value = { up: up.el, down: down.el, left: left.el, right: right.el }
    }
  }

  // Toggle classes for D-pad buttons 12..15
  watchEffect(() => {
    const btns = props.buttons || []
    const map: Array<[number, SVGGraphicsElement | undefined]> = [
      [12, dpad.value.up],
      [13, dpad.value.down],
      [14, dpad.value.left],
      [15, dpad.value.right],
    ]
    map.forEach(([idx, el]) => {
      if (!el) return
      if (btns[idx]) el.classList.add('svg-active')
      else el.classList.remove('svg-active')
    })
  })

  // System buttons (View, Xbox, Menu) - find three shapes near top-center
  const centerCandidates = Array.from(root.querySelectorAll<SVGGraphicsElement>('path,rect,circle,ellipse,polygon'))
    .map(el => ({ el, bb: el.getBBox() }))
    .filter(({ bb }) => bb.width > 6 && bb.height > 6 &&
      bb.x + bb.width / 2 > 280 && bb.x + bb.width / 2 < 460 &&
      bb.y + bb.height / 2 > 100 && bb.y + bb.height / 2 < 190)
  // Keep the three smallest (likely the small circles + xbox button)
  centerCandidates.sort((a, b) => (a.bb.width * a.bb.height) - (b.bb.width * b.bb.height))
  const three = centerCandidates.slice(0, 3).map(c => ({
    el: c.el,
    cx: c.bb.x + c.bb.width / 2
  })).sort((a, b) => a.cx - b.cx)
  if (three.length === 3) {
    sysBtns.value = { view: three[0].el, xbox: three[1].el, menu: three[2].el }
  }
  watchEffect(() => {
    const btns = props.buttons || []
    const pairs: Array<[number, SVGGraphicsElement | undefined]> = [
      [8, sysBtns.value.view],
      [9, sysBtns.value.menu],
      [16, sysBtns.value.xbox],
    ]
    pairs.forEach(([idx, el]) => {
      if (!el) return
      if (btns[idx]) el.classList.add('svg-active')
      else el.classList.remove('svg-active')
    })
  })

  // Bumpers LB/RB near top shoulders
  const shoulderLeft = Array.from(root.querySelectorAll<SVGGraphicsElement>('path,rect,polygon'))
    .map(el => ({ el, bb: el.getBBox() }))
    .filter(({ bb }) => bb.width > 30 && bb.height > 10 &&
      bb.x + bb.width / 2 > 100 && bb.x + bb.width / 2 < 300 &&
      bb.y + bb.height / 2 > 80 && bb.y + bb.height / 2 < 190)
    .sort((a, b) => (b.bb.width * b.bb.height) - (a.bb.width * a.bb.height))
  const shoulderRight = Array.from(root.querySelectorAll<SVGGraphicsElement>('path,rect,polygon'))
    .map(el => ({ el, bb: el.getBBox() }))
    .filter(({ bb }) => bb.width > 30 && bb.height > 10 &&
      bb.x + bb.width / 2 > 440 && bb.x + bb.width / 2 < 650 &&
      bb.y + bb.height / 2 > 80 && bb.y + bb.height / 2 < 190)
    .sort((a, b) => (b.bb.width * b.bb.height) - (a.bb.width * a.bb.height))
  bumpers.value = { lb: shoulderLeft[0]?.el, rb: shoulderRight[0]?.el }
  watchEffect(() => {
    const btns = props.buttons || []
    const pairs: Array<[number, SVGGraphicsElement | undefined]> = [
      [4, bumpers.value.lb],
      [5, bumpers.value.rb],
    ]
    pairs.forEach(([idx, el]) => {
      if (!el) return
      if (btns[idx]) el.classList.add('svg-active')
      else el.classList.remove('svg-active')
    })
  })

  // Sticks LS/RS: use exact base ring IDs primarily
  const lsById = root.getElementById('path5106') as SVGGraphicsElement | null
  const rsById = root.getElementById('path5110') as SVGGraphicsElement | null

  const leftStickRegs = lsById ? [{ el: lsById, bb: (lsById as SVGGraphicsElement).getBBox() }] :
    Array.from(root.querySelectorAll<SVGGraphicsElement>('circle,ellipse,path'))
    .map(el => ({ el, bb: el.getBBox() }))
    .filter(({ bb }) => bb.width > 40 && bb.height > 40 &&
      bb.x + bb.width / 2 > 220 && bb.x + bb.width / 2 < 320 &&
      bb.y + bb.height / 2 > 280 && bb.y + bb.height / 2 < 380)
    .sort((a, b) => (b.bb.width * b.bb.height) - (a.bb.width * a.bb.height))
  const rightStickRegs = rsById ? [{ el: rsById, bb: (rsById as SVGGraphicsElement).getBBox() }] :
    Array.from(root.querySelectorAll<SVGGraphicsElement>('circle,ellipse,path'))
    .map(el => ({ el, bb: el.getBBox() }))
    .filter(({ bb }) => bb.width > 40 && bb.height > 40 &&
      bb.x + bb.width / 2 > 470 && bb.x + bb.width / 2 < 570 &&
      bb.y + bb.height / 2 > 280 && bb.y + bb.height / 2 < 400)
    .sort((a, b) => (b.bb.width * b.bb.height) - (a.bb.width * a.bb.height))
  sticks.value = { ls: leftStickRegs[0]?.el, rs: rightStickRegs[0]?.el }

  // Group and move actual SVG stick "cap" paths so the real tops move
  const lsBB = sticks.value.ls?.getBBox()
  const rsBB = sticks.value.rs?.getBBox()
  // Use explicit user-provided IDs for stick caps
  const leftCapIds = ['path4999','path5086','path5090','path5096','path5092','path5094']
  const rightCapIds = ['path5001','path5088','path5098','path5100','path5102','path5104']

  const groupByIds = (ids: string[]): SVGGElement | null => {
    const elements = ids
      .map(id => root.getElementById(id) as SVGGraphicsElement | null)
      .filter(Boolean) as SVGGraphicsElement[]
    if (!elements.length) return null
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    const anchor = elements[0]
    anchor.parentNode?.insertBefore(g, anchor)
    elements.forEach(el => g.appendChild(el))
    return g
  }
  lsGroup = groupByIds(leftCapIds)
  rsGroup = groupByIds(rightCapIds)

  // Fallback to heuristic grouping only if explicit IDs were not found
  if (!lsGroup && lsBB) {
    const els = Array.from(root.querySelectorAll<SVGGraphicsElement>('path,circle,ellipse'))
    const baseCx = lsBB.x + lsBB.width / 2
    const baseCy = lsBB.y + lsBB.height / 2
    const radius = Math.min(lsBB.width, lsBB.height) / 2
    const parts = els
      .map(el => ({ el, bb: el.getBBox() }))
      .filter(({ bb }) => {
        const cx = bb.x + bb.width / 2, cy = bb.y + bb.height / 2
        const dx = cx - baseCx, dy = cy - baseCy
        const dist2 = dx*dx + dy*dy
        const area = bb.width * bb.height
        const baseArea = lsBB.width * lsBB.height
        return dist2 < (radius * 0.45) * (radius * 0.45) && area > baseArea * 0.01 && area < baseArea * 0.5
      })
      .map(x => x.el)
    if (parts.length) {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
      const anchor = parts[0]
      anchor.parentNode?.insertBefore(g, anchor)
      parts.forEach(p => g.appendChild(p))
      lsGroup = g
    }
  }
  if (!rsGroup && rsBB) {
    const els = Array.from(root.querySelectorAll<SVGGraphicsElement>('path,circle,ellipse'))
    const baseCx = rsBB.x + rsBB.width / 2
    const baseCy = rsBB.y + rsBB.height / 2
    const radius = Math.min(rsBB.width, rsBB.height) / 2
    const parts = els
      .map(el => ({ el, bb: el.getBBox() }))
      .filter(({ bb }) => {
        const cx = bb.x + bb.width / 2, cy = bb.y + bb.height / 2
        const dx = cx - baseCx, dy = cy - baseCy
        const dist2 = dx*dx + dy*dy
        const area = bb.width * bb.height
        const baseArea = rsBB.width * rsBB.height
        return dist2 < (radius * 0.45) * (radius * 0.45) && area > baseArea * 0.01 && area < baseArea * 0.5
      })
      .map(x => x.el)
    if (parts.length) {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
      const anchor = parts[0]
      anchor.parentNode?.insertBefore(g, anchor)
      parts.forEach(p => g.appendChild(p))
      rsGroup = g
    }
  }
  watchEffect(() => {
    const btns = props.buttons || []
    const pairs: Array<[number, SVGGraphicsElement | undefined]> = [
      [10, sticks.value.ls],
      [11, sticks.value.rs],
    ]
    pairs.forEach(([idx, el]) => {
      if (!el) return
      if (btns[idx]) el.classList.add('svg-active')
      else el.classList.remove('svg-active')
    })
  })

  // Move actual cap groups with axes (translate around base centers)
  const maxOffset = 22 // pixels
  watchEffect(() => {
    const lxv = Math.max(-1, Math.min(1, props.axes?.[0] ?? 0))
    const lyv = Math.max(-1, Math.min(1, props.axes?.[1] ?? 0))
    const rxv = Math.max(-1, Math.min(1, props.axes?.[2] ?? 0))
    const ryv = Math.max(-1, Math.min(1, props.axes?.[3] ?? 0))
    if (lsGroup && lsBB) {
      const dx = lxv * maxOffset
      const dy = lyv * maxOffset
      lsGroup.setAttribute('transform', `translate(${dx}, ${dy})`)
    }
    if (rsGroup && rsBB) {
      const dx = rxv * maxOffset
      const dy = ryv * maxOffset
      rsGroup.setAttribute('transform', `translate(${dx}, ${dy})`)
    }
  })

  // Create small inner bars for LT/RT triggers inside the top trigger region
  // Coordinates aligned to base SVG viewBox (744.09448 x 500.35999)
  // Left trigger bar
  ltBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
  ltBar.setAttribute('x', '159')
  ltBar.setAttribute('y', '93')
  ltBar.setAttribute('height', '10')
  ltBar.setAttribute('rx', '5')
  ltBar.setAttribute('class', 'trigger-bar')
  ltBar.setAttribute('width', '0')
  root.appendChild(ltBar)
  // Right trigger bar
  rtBar = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
  rtBar.setAttribute('x', '463')
  rtBar.setAttribute('y', '93')
  rtBar.setAttribute('height', '10')
  rtBar.setAttribute('rx', '5')
  rtBar.setAttribute('class', 'trigger-bar')
  rtBar.setAttribute('width', '0')
  root.appendChild(rtBar)

  // Update bar widths reactively from axes 4/5
  watchEffect(() => {
    const l = Math.max(0, Math.min(1, (props.axes?.[4] ?? -1 + 1) / 2))
    const r = Math.max(0, Math.min(1, (props.axes?.[5] ?? -1 + 1) / 2))
    if (ltBar) ltBar.setAttribute('width', String(100 * l))
    if (rtBar) rtBar.setAttribute('width', String(100 * r))
  })
})
</script>

<style scoped>
.xbox-wrap { display: flex; justify-content: center; align-items: center; padding: 8px; }
.controller { position: relative; width: 100%; max-width: 800px; }
.base-svg :global(svg) { width: 100%; height: auto; display: block; }


/* When pressing ABXY, directly tint the base SVG paths */
:deep(.svg-active) {
  filter: drop-shadow(0 0 6px rgba(34,197,94,0.9));
  opacity: 0.9;
}

.trigger-bar { fill: rgba(16,185,129,0.9); stroke: none; }

.disconnected { opacity: 0.6; filter: grayscale(0.3); }
</style>
