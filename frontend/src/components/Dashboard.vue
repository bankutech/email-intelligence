<template>
  <div class="space-y-10">

    <div class="flex flex-col xl:flex-row justify-between items-start gap-8 border-b-2 border-ink pb-8">
      <div class="max-w-4xl relative">
        <h2 class="font-serif text-5xl md:text-7xl leading-tight text-ink" v-if="stats">
          <strong>{{ stats.total_processed || 0 }}</strong> emails read today.
          <strong>{{ automatedCount }}</strong> filed automatically.
          <span class="relative inline-block">
            <strong :class="reviewCount > 0 ? 'text-vermilion' : ''">{{ reviewCount }}</strong>
            <svg v-if="reviewCount > 0" class="absolute -inset-3 w-[calc(100%+24px)] h-[calc(100%+24px)] pointer-events-none" viewBox="0 0 100 60" preserveAspectRatio="none">
              <ellipse cx="50" cy="30" rx="48" ry="26" fill="none" stroke="#FF4B1F" stroke-width="4" stroke-dasharray="260" stroke-dashoffset="260" class="circle-draw"/>
            </svg>
          </span> waiting for you.
        </h2>
        <h2 v-else class="font-serif text-5xl md:text-7xl leading-tight text-ink/40 animate-pulse">
          Tallying the ledger...
        </h2>
        <div v-if="stats" class="absolute -top-4 -right-2 md:-right-16 rotate-[15deg] pointer-events-none">
          <div :class="['border-4 font-mono font-bold text-lg tracking-widest px-3 py-1 flex flex-col items-center bg-cream', successRate >= 100 ? 'border-vermilion text-vermilion' : 'border-ink text-ink']">
            {{ successRate }}%<br/>CLEAN
          </div>
        </div>
      </div>

      <div class="flex flex-col items-start xl:items-end gap-4 shrink-0">
        <button @click="scan(true)" :disabled="isScanLoading || scanning" class="ticket-btn-red px-6 py-3 font-mono font-bold uppercase tracking-widest text-sm gap-3">
          <svg v-if="isScanLoading || scanning" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          {{ (isScanLoading || scanning) ? 'Syncing Gmail...' : 'Up to date' }}
        </button>

        <div class="border-2 border-ink bg-[#e8e0d0] p-3 relative shadow-[4px_4px_0_#15120E] w-60">
          <div class="absolute top-1 left-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          <div class="absolute top-1 right-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          <div class="absolute bottom-1 left-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          <div class="absolute bottom-1 right-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          <div class="font-mono text-[9px] uppercase tracking-widest text-ink/60 mb-1 border-b border-ink/20 pb-1">System Status</div>
          <div class="font-mono text-[10px] uppercase tracking-wider font-medium text-ink leading-relaxed">
            OAuth <span class="text-success inline-block animate-pulse text-[8px]">●</span> connected<br/>
            Rules <span class="text-success inline-block animate-pulse text-[8px]">●</span> deterministic<br/>
            Audit log <span class="text-success inline-block animate-pulse text-[8px]">●</span> recording
          </div>
        </div>
      </div>
    </div>

    <div class="border-2 border-ink shadow-[8px_8px_0_#15120E] bg-cream relative overflow-hidden h-44 flex items-center">
      <div class="absolute inset-0 opacity-5" style="background-image: repeating-linear-gradient(0deg, transparent, transparent 19px, #15120E 19px, #15120E 20px);"></div>

      <div class="absolute left-1/2 top-0 bottom-0 w-20 border-l-2 border-r-2 border-ink bg-cream/80 z-20 flex flex-col items-center justify-center -translate-x-1/2">
        <div class="w-10 h-10 rounded-full border-4 border-ink bg-airmail/10 relative flex items-center justify-center">
          <div class="absolute inset-2 border-2 border-airmail rounded-full opacity-50"></div>
        </div>
        <span class="font-hand text-ink text-sm mt-1 rotate-[-8deg]">Scanner</span>
      </div>

      <div class="absolute top-1/2 left-0 w-full h-px bg-ink/20"></div>
      <div class="absolute top-1/2 left-0 w-full border-t border-dashed border-ink/30"></div>

      <div v-if="isScanLoading || scanning" class="w-full h-full relative z-10">
        <div v-for="(env, i) in 3" :key="i" class="absolute top-1/2 left-0 w-40 h-24 bg-cream border-2 border-ink airmail-edge overflow-hidden flex flex-col justify-between p-1" :style="{ animation: `conveyor 3.5s linear ${i * 1.1}s infinite` }">
          <div class="airmail-edge h-1.5 w-full"></div>
          <div class="airmail-edge h-1.5 w-full"></div>
        </div>
      </div>
      <div v-else class="w-full flex flex-col items-center justify-center z-10 gap-2">
        <svg class="w-8 h-8 text-ink/30" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        <span class="font-hand text-2xl text-ink/50">Mailroom is quiet. Nothing to sort.</span>
      </div>
    </div>

    <div class="space-y-3" v-if="emails && emails.length > 0">
      <h3 class="font-mono text-xs uppercase tracking-widest text-ink/60 border-b border-dashed border-ink/30 pb-2">Recent Activity</h3>
      <div v-for="email in emails.slice(0,5)" :key="email.message_id" class="flex items-center justify-between gap-4 py-3 border-b border-dashed border-ink/20">
        <div class="font-mono text-xs text-ink/40 w-12 shrink-0">{{ formatTime(email.updated_at) }}</div>
        <div class="flex-1 min-w-0">
          <span class="font-serif text-lg text-ink truncate block">{{ email.subject || '(no subject)' }}</span>
        </div>
        <span :class="['shrink-0 border-2 px-2 py-0.5 font-mono text-[10px] font-bold tracking-widest uppercase rotate-[-1deg]', email.category === 'spam' ? 'border-vermilion text-vermilion' : 'border-ink text-ink']">
          {{ email.category }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const stats = ref(null)
const emails = ref(null)
const scanning = computed(() => (stats.value?.pending || 0) > 0)

const automatedCount = computed(() => !stats.value ? 0 : (stats.value.total_processed || 0) - (stats.value.needs_review || 0))
const reviewCount = computed(() => stats.value?.needs_review || 0)
const successRate = computed(() => {
  if (!stats.value?.total_processed) return 100
  return Math.round(((stats.value.total_processed - (stats.value.failed || 0)) / stats.value.total_processed) * 100)
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

const isScanLoading = ref(false)

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
  // Trigger background sync immediately after initial data loads
  scan(false)
  // Poll for new data every 10s while on dashboard
  syncInterval = setInterval(fetchData, 10000)
})

onUnmounted(() => {
  clearInterval(syncInterval)
})
</script>

<style scoped>
@keyframes draw { to { stroke-dashoffset: 0; } }
.circle-draw { animation: draw 0.6s ease-out forwards; }
</style>
