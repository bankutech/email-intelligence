<template>
  <div class="space-y-12 animate-slide-up">

    <div class="flex flex-col lg:flex-row justify-between items-start gap-8">
      <div class="max-w-3xl">
        <h2 class="font-display font-bold text-4xl md:text-5xl leading-tight text-nyalaslate" v-if="stats">
          <span class="text-nyalablue">{{ stats.total_processed || 0 }}</span> emails processed today.
          <br/>
          <span class="text-nyalaslate/70">{{ automatedCount }} filed automatically, 
          <span :class="reviewCount > 0 ? 'text-nyalablue font-semibold' : ''">{{ reviewCount }}</span> need review.</span>
        </h2>
        <h2 v-else class="font-display font-bold text-4xl md:text-5xl leading-tight text-nyalaslate/40 animate-pulse">
          Loading metrics...
        </h2>
      </div>

      <div class="flex flex-col items-start lg:items-end gap-4 shrink-0">
        <button @click="scan(true)" :disabled="isScanLoading || scanning" class="px-6 py-3 rounded-full bg-nyalablue text-nyalawhite font-medium shadow-md shadow-nyalablue/20 hover:bg-nyalablue/90 hover:-translate-y-0.5 transition-all disabled:opacity-50 flex items-center gap-2">
          <svg v-if="isScanLoading || scanning" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          {{ syncStatusText }}
        </button>

        <div class="bg-nyalawhite border border-nyalaslate/10 rounded-2xl p-4 shadow-sm w-64">
          <div class="text-xs font-bold text-nyalaslate/50 uppercase tracking-wider mb-3">System Status</div>
          <div class="space-y-2 text-sm font-medium text-nyalaslate/80">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-success"></span> OAuth Connected
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-success"></span> Rules Active
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-success"></span> Logging Enabled
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Scanner visualization replaced with Nyalazone modern stats cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-nyalawhite border border-nyalaslate/5 rounded-3xl p-8 shadow-sm">
        <h3 class="text-sm font-bold text-nyalaslate/50 uppercase tracking-wider mb-2">Success Rate</h3>
        <p class="font-display font-bold text-4xl text-nyalaslate">{{ successRate }}%</p>
      </div>
      <div class="bg-nyalawhite border border-nyalaslate/5 rounded-3xl p-8 shadow-sm">
        <h3 class="text-sm font-bold text-nyalaslate/50 uppercase tracking-wider mb-2">Automated</h3>
        <p class="font-display font-bold text-4xl text-success">{{ automatedCount }}</p>
      </div>
      <div class="bg-nyalawhite border border-nyalaslate/5 rounded-3xl p-8 shadow-sm">
        <h3 class="text-sm font-bold text-nyalaslate/50 uppercase tracking-wider mb-2">Manual Review</h3>
        <p class="font-display font-bold text-4xl" :class="reviewCount > 0 ? 'text-nyalablue' : 'text-nyalaslate'">{{ reviewCount }}</p>
      </div>
    </div>

    <div class="bg-nyalawhite border border-nyalaslate/5 rounded-3xl p-8 shadow-sm" v-if="emails && emails.length > 0">
      <h3 class="text-sm font-bold text-nyalaslate/50 uppercase tracking-wider mb-6 pb-4 border-b border-nyalaslate/10">Recent Activity</h3>
      <div class="space-y-4">
        <div v-for="email in emails.slice(0,5)" :key="email.message_id" class="flex items-center justify-between gap-4 p-4 rounded-xl hover:bg-nyalaslate/[0.02] transition-colors border border-transparent hover:border-nyalaslate/5">
          <div class="text-xs font-medium text-nyalaslate/40 w-12 shrink-0">{{ formatTime(email.updated_at) }}</div>
          <div class="flex-1 min-w-0">
            <span class="font-display font-semibold text-nyalaslate truncate block">{{ email.subject || '(no subject)' }}</span>
            <span class="text-sm text-nyalaslate/60 truncate block mt-0.5">{{ email.sender_email || 'unknown sender' }}</span>
          </div>
          <span :class="['shrink-0 px-3 py-1 text-xs font-bold rounded-full', categoryClass(email.category)]">
            {{ email.category }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const stats = ref(null)
const emails = ref(null)

const automatedCount = computed(() => !stats.value ? 0 : (stats.value.total_processed || 0) - (stats.value.needs_review || 0))
const reviewCount = computed(() => stats.value?.needs_review || 0)
const successRate = computed(() => {
  if (!stats.value?.total_processed) return 100
  return Math.round(((stats.value.total_processed - (stats.value.failed || 0)) / stats.value.total_processed) * 100)
})

const isScanLoading = ref(false)
const scanning = computed(() => {
  return isScanLoading.value || (stats.value?.sync_status === 'syncing') || (stats.value?.pending || 0) > 0
})

const categoryClass = (cat) => {
  if (!cat) return 'bg-nyalaslate/10 text-nyalaslate'
  const c = cat.toUpperCase()
  if (c === 'SPAM') return 'bg-danger/10 text-danger'
  if (c === 'URGENT') return 'bg-nyalablue/10 text-nyalablue'
  if (c === 'NEWSLETTER') return 'bg-success/10 text-success'
  return 'bg-nyalaslate/10 text-nyalaslate'
}

const syncStatusText = computed(() => {
  if (scanning.value) return 'Syncing Gmail...'
  const st = stats.value?.sync_status
  if (!st) return 'Up to date'
  if (st.startsWith('success_')) {
    const num = parseInt(st.split('_')[1], 10)
    if (num > 0) return `${num} new email${num > 1 ? 's' : ''} synced`
    return 'Up to date'
  }
  if (st === 'error' || st === 'auth_error') return 'Gmail sync needs attention'
  return 'Up to date'
})

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchData = async () => {
  try {
    const [stRes, emRes] = await Promise.all([fetch('/api/dashboard'), fetch('/api/emails')])
    if (stRes.ok) stats.value = await stRes.json()
    if (emRes.ok) emails.value = await emRes.json()
  } catch {}
}

const scan = async (manual = false) => {
  if (isScanLoading.value) return
  isScanLoading.value = true
  try {
    const res = await fetch('/api/scan', { method: 'POST' })
    if (res.ok && manual) {
      setTimeout(fetchData, 3000)
    }
  } finally {
    isScanLoading.value = false
  }
}

let syncInterval
onMounted(async () => {
  await fetchData()
  syncInterval = setInterval(fetchData, 10000)
})

onUnmounted(() => {
  clearInterval(syncInterval)
})
</script>
