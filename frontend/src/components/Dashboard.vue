<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <SecurityMatrix />
    
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-textMain">Overview</h2>
      <button @click="scan" :disabled="scanning" class="btn btn-secondary flex items-center gap-2" aria-label="Trigger manual scan">
        <svg v-if="scanning" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
        {{ scanning ? 'Scanning...' : 'Scan Now' }}
      </button>
    </div>

    <!-- Metrics -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" v-if="stats">
      <div class="panel p-5 flex flex-col justify-between">
        <div class="text-sm font-medium text-textMuted uppercase tracking-wider mb-2" id="metric-total">Total Processed</div>
        <div class="text-4xl font-bold text-textMain" aria-labelledby="metric-total">{{ stats.total_processed || 0 }}</div>
      </div>
      <div class="panel p-5 flex flex-col justify-between">
        <div class="text-sm font-medium text-textMuted uppercase tracking-wider mb-2" id="metric-auto">Automated</div>
        <div class="text-4xl font-bold text-textMain" aria-labelledby="metric-auto">{{ (stats.total_processed || 0) - (stats.needs_review || 0) }}</div>
      </div>
      <div class="panel p-5 flex flex-col justify-between border-warning/30">
        <div class="text-sm font-medium text-warning uppercase tracking-wider mb-2" id="metric-review">Review Required</div>
        <div class="text-4xl font-bold text-textMain" aria-labelledby="metric-review">{{ stats.needs_review || 0 }}</div>
      </div>
      <div class="panel p-5 flex flex-col justify-between border-success/30">
        <div class="text-sm font-medium text-success uppercase tracking-wider mb-2" id="metric-rate">Success Rate</div>
        <div class="text-4xl font-bold text-textMain" aria-labelledby="metric-rate">{{ successRate }}%</div>
      </div>
    </div>
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
       <!-- Skeletons -->
       <div class="panel p-5 h-32 animate-pulse bg-surfaceElevated" v-for="i in 4" :key="i"></div>
    </div>
    
    <div class="mt-8 panel p-6">
      <h3 class="text-base font-semibold mb-4 text-textMain">Recent Activity</h3>
      <div v-if="!emails && loading" class="space-y-4">
        <div class="h-12 bg-surfaceElevated animate-pulse rounded" v-for="i in 3" :key="i"></div>
      </div>
      <div v-else-if="emails && emails.length === 0" class="text-center text-textMuted py-8">No recent activity.</div>
      <div v-else class="space-y-4">
        <div v-for="email in (emails || []).slice(0, 5)" :key="email.message_id" class="flex items-start gap-4 text-sm">
          <div class="w-12 font-mono text-textMuted pt-1 shrink-0">{{ formatTime(email.updated_at) }}</div>
          <div class="flex-1 panel-elevated p-3">
             <div class="flex justify-between">
                <span class="font-medium text-textMain truncate max-w-[200px] sm:max-w-xs">{{ email.subject || '(no subject)' }}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase bg-surface text-textMuted">{{ email.category }}</span>
             </div>
             <div class="text-textMuted mt-1">{{ email.actions || 'Processed' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed } from 'vue'
import SecurityMatrix from './SecurityMatrix.vue'

const stats = ref(null)
const emails = ref(null)
const loading = ref(true)
const scanning = ref(false)

const successRate = computed(() => {
  if (!stats.value || !stats.value.total_processed) return 100
  const total = stats.value.total_processed
  const success = total - (stats.value.failed || 0)
  return Math.round((success / total) * 100)
})

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const [stRes, emRes] = await Promise.all([
      fetch('/api/dashboard'),
      fetch('/api/emails')
    ])
    if (stRes.ok) stats.value = await stRes.json()
    if (emRes.ok) {
       emails.value = await emRes.json()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const scan = async () => {
  scanning.value = true
  try {
    const res = await fetch('/api/scan', { method: 'POST' })
    if (res.ok) await fetchData()
  } finally {
    scanning.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
