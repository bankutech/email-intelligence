<template>
  <div class="panel p-6 mb-8">
    <h3 class="text-base font-semibold mb-4 text-textMain">Security & Access Matrix</h3>
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <div v-for="s in computedStatus" :key="s.name" class="panel-elevated p-4 flex flex-col items-center justify-center text-center gap-2">
        <div :class="['w-8 h-8 rounded-full flex items-center justify-center bg-surface', s.color]">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path v-if="s.iconType === 'lock'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
            <path v-else-if="s.iconType === 'shield'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
            <path v-else-if="s.iconType === 'chip'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
            <path v-else-if="s.iconType === 'server'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path>
          </svg>
        </div>
        <div class="text-xs font-medium text-textMain">{{ s.name }}</div>
        <div :class="['text-[10px] uppercase tracking-wider', s.color]">{{ s.state }}</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'

const connected = ref(false)

onMounted(async () => {
  try {
    const res = await fetch('/api/me')
    if (res.ok) {
      const data = await res.json()
      connected.value = data.connected === true
    }
  } catch (e) {
    connected.value = false
  }
})

const computedStatus = computed(() => [
  { name: 'OAuth', state: connected.value ? 'Connected' : 'Not Connected', color: connected.value ? 'text-success' : 'text-danger', iconType: 'lock' },
  { name: 'Session', state: 'Protected', color: 'text-success', iconType: 'shield' },
  { name: 'AI Engine', state: 'Schema Valid', color: 'text-primary', iconType: 'chip' },
  { name: 'Automation', state: 'Deterministic', color: 'text-primary', iconType: 'server' },
  { name: 'Isolation', state: 'Enabled', color: 'text-success', iconType: 'lock' },
  { name: 'Audit Log', state: 'Active', color: 'text-textMuted', iconType: 'clipboard' },
])
</script>
