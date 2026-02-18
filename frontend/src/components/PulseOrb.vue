<template>
  <canvas ref="canvasRef" class="w-full h-full block" />
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  state: { type: Number, default: 0 },
  intensity: { type: Number, default: 1 },
  dark: { type: Boolean, default: true },
  pulseMode: { type: Number, default: 0 } // 0=off, 1=low, 2=med, 3=high
})

const canvasRef = ref(null)

// ─── GLSL Shaders ────────────────────────────────────────────
const VERT_SRC = `
attribute vec2 a_pos;
void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }
`

const FRAG_SRC = `
precision highp float;

uniform vec2  u_res;
uniform float u_time;
uniform vec2  u_mouse;
uniform vec2  u_mouse_stir;
uniform vec3  u_c0, u_c1, u_c2, u_c3;
uniform float u_pulse;
uniform vec3  u_bg;

vec3 mod289(vec3 x){ return x - floor(x*(1.0/289.0))*289.0; }
vec4 mod289(vec4 x){ return x - floor(x*(1.0/289.0))*289.0; }
vec4 permute(vec4 x){ return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314*r; }

float snoise(vec3 v){
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g, l.zxy);
    vec3 i2 = max(g, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0*floor(p*ns.z*ns.z);
    vec4 x_ = floor(j*ns.z);
    vec4 y_ = floor(j - 7.0*x_);
    vec4 x2_ = x_*ns.x + ns.yyyy;
    vec4 y2_ = y_*ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x2_) - abs(y2_);
    vec4 b0 = vec4(x2_.xy, y2_.xy);
    vec4 b1 = vec4(x2_.zw, y2_.zw);
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)), 0.0);
    m = m*m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
}

float fbm(vec3 p, int oct){
    float v = 0.0, a = 0.5;
    mat3 rot = mat3(0.8,-0.6,0.0, 0.6,0.8,0.0, 0.0,0.0,1.0);
    for(int i=0; i<6; i++){
        if(i >= oct) break;
        v += a * snoise(p);
        p = rot * p * 2.0 + 100.0;
        a *= 0.5;
    }
    return v;
}

void main(){
    vec2 uv = (gl_FragCoord.xy * 2.0 - u_res) / min(u_res.x, u_res.y);
    float t = u_time;

    vec2 uvShape = uv * vec2(0.7, 1.0);
    float d = length(uvShape);

    /* Early discard with smooth fade to avoid visible boundary */
    if(d > 1.3){
        gl_FragColor = vec4(u_bg, 1.0);
        return;
    }
    float glowFade = smoothstep(1.3, 0.9, d);

    float inOrb = smoothstep(0.95, 0.55, d);

    float p = u_pulse;
    float p2 = p * p;

    float warpScale = 2.2 + p * 1.0;
    float w1x = fbm(vec3(uv * warpScale, t * 0.04), 2);
    float w1y = fbm(vec3(uv * warpScale + 5.2, t * 0.04 + 3.7), 2);
    vec2 warp1 = vec2(w1x, w1y) * (1.0 + p * 0.8);

    float mDist = length(uv - u_mouse);
    warp1 += (u_mouse - uv) * 0.04 * exp(-mDist * mDist * 6.0) * inOrb;

    float breath = 0.02 * sin(t * 0.15) + 0.01 * sin(t * 0.1);
    float pulse_expand = p2 * 0.28;
    float radius = 0.7 + breath + pulse_expand;
    float edgeNoise = fbm(vec3(uv * 3.0 + warp1 * 0.5, t * 0.05), 2) * (0.12 + p * 0.18);
    float mask = smoothstep(radius + 0.22, radius - 0.08, d + edgeNoise);

    float sDist = length(uv - u_mouse_stir);
    float mProx = exp(-sDist * sDist * 1.8);
    vec2 mStir = (u_mouse_stir - uv) * mProx * 0.9 * inOrb;

    float n1 = fbm(vec3(uv * 3.0 + warp1 * (0.6 + p * 0.5) + mStir, t * 0.03), 3);
    float n2 = fbm(vec3(uv * 4.0 - warp1 * (0.5 + p * 0.4) + mStir * 0.85, t * 0.025 + 50.0), 2);
    float n3 = fbm(vec3(uv * 2.0 + warp1 * 0.3 + mStir * 0.7, t * 0.04 + 80.0), 2);

    float voiceBright = 1.0 + p * 0.5;
    vec3 baseCol = (u_c0 + u_c1 + u_c2 + u_c3) * (0.19 * voiceBright);
    vec3 col = baseCol;
    col = mix(col, u_c0 * 0.7 * voiceBright, smoothstep(-0.3, 0.4, n1) * 0.3);
    col = mix(col, u_c1 * 0.7 * voiceBright, smoothstep(-0.2, 0.5, n2) * 0.25);
    col = mix(col, u_c2 * 0.7 * voiceBright, smoothstep(0.0, 0.5, n1 + n2 * 0.5) * 0.2);

    float depth = 0.65 + 0.35 * smoothstep(-0.3, 0.3, n3);
    col *= depth;

    float core = exp(-d * d * (3.0 - p * 1.5)) * (0.14 + p2 * 0.55);
    col += mix(u_c0, vec3(1.0), 0.25 + p * 0.25) * core;

    float filament = abs(fbm(vec3(uv * 5.0 + warp1 * 0.8 + mStir * 0.5, t * 0.04), 2));
    filament = smoothstep(0.04 + p * 0.02, 0.0, filament) * (0.08 + p * 0.35);
    col += (u_c1 * 0.4 + vec3(0.08 + p * 0.12)) * filament * smoothstep(0.6 + p * 0.2, 0.0, d);

    float mHigh = exp(-mDist * mDist * 8.0) * 0.02 * mask;
    col += mix(u_c0, vec3(1.0), 0.4) * mHigh;

    /* Glow */
    float glow = exp(-d * (2.0 - p * 0.8)) * (0.035 + p2 * 0.12);
    vec3 glowTint = u_c0 * (0.5 + p * 0.4);
    float glowStr = min(glow * 5.0, 1.0) * glowFade;
    vec3 bgWithGlow = mix(u_bg, glowTint, glowStr);

    /* Compose: orb where mask is high, glowing background elsewhere */
    vec3 final_col = mix(bgWithGlow, col, mask);

    gl_FragColor = vec4(final_col, 1.0);
}
`

// ─── Theme definitions ───────────────────────────────────────
const states = [
  { colors: [[0.10,0.78,0.52],[0.06,0.72,0.48],[0.14,0.82,0.45],[0.08,0.75,0.50]], sp: 1.2 },
  { colors: [[0.10,0.52,0.88],[0.06,0.45,0.82],[0.14,0.58,0.90],[0.08,0.50,0.85]], sp: 1.8 },
  { colors: [[0.92,0.62,0.08],[0.85,0.55,0.04],[0.95,0.68,0.12],[0.88,0.58,0.06]], sp: 3.0 },
  { colors: [[0.90,0.12,0.16],[0.82,0.08,0.20],[0.85,0.18,0.14],[0.88,0.10,0.18]], sp: 4.5 },
  { colors: [[0.55,0.22,0.88],[0.48,0.16,0.82],[0.60,0.28,0.90],[0.52,0.20,0.85]], sp: 2.0 }
]
const intensitySpeeds = [1.8, 3.0, 5.0]

const BG_DARK  = [0.008, 0.008, 0.016]
const BG_LIGHT = [1.0, 1.0, 1.0]

// ─── WebGL state ─────────────────────────────────────────────
let gl = null
let program = null
let uRes, uTime, uMouse, uMouseStir, uC0, uC1, uC2, uC3, uPulse, uBg
let shaderTime = 0
let lastFrame = 0
let animationId = null

const mouseCur = [0, 0]
const mouseTgt = [0, 0]
const mouseStir = [0, 0]

let curColors = states[0].colors.map(c => [...c])
let tgtColors = states[0].colors.map(c => [...c])
let speedCur = 1.2
let speedTgt = 1.2
let curBg = [...BG_DARK]
let tgtBg = [...BG_DARK]

// ─── Voice pulse state ──────────────────────────────────────
let curPulse = 0
let tgtAmplitude = 0

function simPulse(time) {
  const s1 = Math.sin(time * 1.7) * 0.5 + 0.5
  const s2 = Math.sin(time * 2.9 + 1.3) * 0.5 + 0.5
  const s3 = Math.sin(time * 0.7 + 0.8) * 0.5 + 0.5
  return s1 * 0.5 + s2 * 0.3 + s3 * 0.2
}

// ─── Shader helpers ──────────────────────────────────────────
function compileShader(type, src) {
  const s = gl.createShader(type)
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.error('Shader error:', gl.getShaderInfoLog(s))
    return null
  }
  return s
}

const RENDER_SCALE = 0.65
const FPS_CAP = 30
const FRAME_MIN_DT = 1.0 / FPS_CAP

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const scale = RENDER_SCALE
  const w = Math.round(canvas.clientWidth * scale)
  const h = Math.round(canvas.clientHeight * scale)
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w
    canvas.height = h
    gl.viewport(0, 0, w, h)
  }
}

// ─── Init WebGL ──────────────────────────────────────────────
function initGL() {
  const canvas = canvasRef.value
  gl = canvas.getContext('webgl', { alpha: false, antialias: false, premultipliedAlpha: false })
  if (!gl) return false

  const vs = compileShader(gl.VERTEX_SHADER, VERT_SRC)
  const fs = compileShader(gl.FRAGMENT_SHADER, FRAG_SRC)
  if (!vs || !fs) return false

  program = gl.createProgram()
  gl.attachShader(program, vs)
  gl.attachShader(program, fs)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('Link error:', gl.getProgramInfoLog(program))
    return false
  }
  gl.useProgram(program)

  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW)
  const aPos = gl.getAttribLocation(program, 'a_pos')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  uRes       = gl.getUniformLocation(program, 'u_res')
  uTime      = gl.getUniformLocation(program, 'u_time')
  uMouse     = gl.getUniformLocation(program, 'u_mouse')
  uMouseStir = gl.getUniformLocation(program, 'u_mouse_stir')
  uC0        = gl.getUniformLocation(program, 'u_c0')
  uC1        = gl.getUniformLocation(program, 'u_c1')
  uC2        = gl.getUniformLocation(program, 'u_c2')
  uC3        = gl.getUniformLocation(program, 'u_c3')
  uPulse     = gl.getUniformLocation(program, 'u_pulse')
  uBg        = gl.getUniformLocation(program, 'u_bg')

  resize()
  return true
}

// ─── Render loop ─────────────────────────────────────────────
function render() {
  animationId = requestAnimationFrame(render)

  const now = performance.now() * 0.001
  const dt = now - lastFrame
  if (dt < FRAME_MIN_DT) return
  lastFrame = now
  const clampedDt = Math.min(dt, 0.1)

  resize()
  shaderTime += clampedDt * speedCur

  // Mouse interpolation
  const mouseLerp = 1.0 - Math.pow(0.08, clampedDt)
  mouseCur[0] += (mouseTgt[0] - mouseCur[0]) * mouseLerp
  mouseCur[1] += (mouseTgt[1] - mouseCur[1]) * mouseLerp

  const stirLerp = 1.0 - Math.pow(0.25, clampedDt)
  mouseStir[0] += (mouseCur[0] - mouseStir[0]) * stirLerp
  mouseStir[1] += (mouseCur[1] - mouseStir[1]) * stirLerp

  // Color/speed/bg interpolation
  const lerpRate = 1.0 - Math.pow(0.02, clampedDt)
  speedCur += (speedTgt - speedCur) * lerpRate
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 3; j++) {
      curColors[i][j] += (tgtColors[i][j] - curColors[i][j]) * lerpRate
    }
  }
  for (let j = 0; j < 3; j++) {
    curBg[j] += (tgtBg[j] - curBg[j]) * lerpRate
  }

  // ─── Voice pulse ────────────────────────────────────────
  const pm = props.pulseMode
  if (pm >= 1 && pm <= 3) {
    const simRanges = [[0.1, 0.3], [0.3, 0.6], [0.5, 0.9]]
    const [lo, hi] = simRanges[pm - 1]
    tgtAmplitude = lo + (hi - lo) * simPulse(now)
  } else {
    tgtAmplitude = 0
  }

  // Smooth curPulse: fast attack, moderate decay (same as pulse.html)
  const pulseLerp = 1.0 - Math.pow(0.0001, clampedDt)
  const pulseDecay = 1.0 - Math.pow(0.15, clampedDt)
  if (tgtAmplitude > curPulse) {
    curPulse += (tgtAmplitude - curPulse) * pulseLerp
  } else {
    curPulse += (tgtAmplitude - curPulse) * pulseDecay
  }

  // Voice modulates animation speed
  if (curPulse > 0.01) {
    speedCur += curPulse * 4.0 * clampedDt
  }

  const canvas = canvasRef.value
  if (!canvas) return
  gl.uniform2f(uRes, canvas.width, canvas.height)
  gl.uniform1f(uTime, shaderTime)
  gl.uniform2f(uMouse, mouseCur[0], mouseCur[1])
  gl.uniform2f(uMouseStir, mouseStir[0], mouseStir[1])
  gl.uniform1f(uPulse, curPulse)
  gl.uniform3fv(uC0, curColors[0])
  gl.uniform3fv(uC1, curColors[1])
  gl.uniform3fv(uC2, curColors[2])
  gl.uniform3fv(uC3, curColors[3])
  gl.uniform3fv(uBg, curBg)

  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
}

// ─── Apply state/intensity/theme ─────────────────────────────
function applyState(idx) {
  const st = states[idx]
  if (!st) return
  tgtColors = st.colors.map(c => [...c])
}

function applyIntensity(lvl) {
  speedTgt = intensitySpeeds[(lvl || 1) - 1]
}

function applyDark(isDark) {
  tgtBg = isDark ? [...BG_DARK] : [...BG_LIGHT]
}

// ─── Watchers ────────────────────────────────────────────────
watch(() => props.state, applyState)
watch(() => props.intensity, applyIntensity)
watch(() => props.dark, applyDark)
// ─── Mouse handlers ─────────────────────────────────────────
function onMouseMove(e) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  const aspect = rect.width / rect.height
  mouseTgt[0] = (px * 2.0 - 1.0) * aspect
  mouseTgt[1] = -(py * 2.0 - 1.0)
}

function onMouseLeave() {
  mouseTgt[0] = 0
  mouseTgt[1] = 0
}

function onVisibilityChange() {
  if (!document.hidden) {
    lastFrame = performance.now() * 0.001
  }
}

// ─── Lifecycle ───────────────────────────────────────────────
onMounted(() => {
  if (!initGL()) return

  // Set initial bg immediately (no transition on first load)
  const initBg = props.dark ? BG_DARK : BG_LIGHT
  curBg = [...initBg]
  tgtBg = [...initBg]

  applyState(props.state)
  applyIntensity(props.intensity)

  const canvas = canvasRef.value
  canvas.addEventListener('mousemove', onMouseMove)
  canvas.addEventListener('mouseleave', onMouseLeave)
  window.addEventListener('resize', resize)
  document.addEventListener('visibilitychange', onVisibilityChange)

  lastFrame = performance.now() * 0.001
  render()
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  animationId = null

  const canvas = canvasRef.value
  if (canvas) {
    canvas.removeEventListener('mousemove', onMouseMove)
    canvas.removeEventListener('mouseleave', onMouseLeave)
  }
  window.removeEventListener('resize', resize)
  document.removeEventListener('visibilitychange', onVisibilityChange)

  if (gl) {
    const ext = gl.getExtension('WEBGL_lose_context')
    if (ext) ext.loseContext()
    gl = null
  }
})
</script>
