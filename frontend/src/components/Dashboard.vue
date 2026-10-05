<template>
  <div class="space-y-12">
    
    <!-- Hero Stat Strip & Actions -->
    <div class="flex flex-col xl:flex-row justify-between items-start gap-8 border-b-2 border-ink pb-8">
      <div class="max-w-4xl relative">
        <h2 class="font-serif text-5xl md:text-7xl leading-tight text-ink relative z-10" v-if="stats">
          <strong class="font-bold">{{ stats.total_processed || 0 }}</strong> emails read today. 
          <strong class="font-bold">{{ automatedCount }}</strong> filed automatically. 
          <span class="relative inline-block">
            <strong :class="['font-bold relative z-10', reviewCount > 0 ? 'text-vermilion' : '']">{{ reviewCount }}</strong>
            <!-- Hand-drawn circle if Z > 0 -->
            <svg v-if="reviewCount > 0" class="absolute -inset-4 w-[calc(100%+32px)] h-[calc(100%+32px)] z-0 text-vermilion pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
              <path d="M 50,5 C 80,10 95,40 90,70 C 85,95 40,95 15,80 C 0,60 10,20 40,10" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" class="scribble-circle" stroke-dasharray="300" stroke-dashoffset="0" />
            </svg>
          </span> waiting for you.
        </h2>
        <h2 v-else class="font-serif text-5xl md:text-7xl leading-tight text-ink/50 animate-pulse">
          Tallying the ledger...
        </h2>
        
        <!-- Rubber stamp success rate -->
        <div v-if="stats" class="absolute -top-4 -right-12 md:-right-24 rotate-[15deg] pointer-events-none z-20">
          <div class="border-4 border-vermilion text-vermilion font-mono font-bold text-lg md:text-xl tracking-widest px-3 py-1 mix-blend-multiply flex flex-col items-center justify-center bg-cream shadow-[4px_4px_0_rgba(255,75,31,0.2)]" :class="{'opacity-50 border-ink text-ink shadow-[4px_4px_0_#15120E]': successRate < 100}">
            {{ successRate }}%<br/>CLEAN
          </div>
        </div>
      </div>

      <div class="flex flex-col items-end gap-4 shrink-0">
        <!-- Scan Button -->
        <button @click="scan" :disabled="scanning" class="ticket-btn-red px-6 py-3 font-mono font-bold uppercase tracking-widest text-sm flex items-center gap-3 interactive" aria-label="Trigger manual scan">
          <svg v-if="scanning" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
          {{ scanning ? 'Scanning...' : 'Scan Mailroom' }}
        </button>

        <!-- System Status Machine Plate -->
        <div class="border-2 border-ink bg-[#e5ddd0] p-3 relative shadow-[4px_4px_0_#15120E] mt-4 w-64 interactive group cursor-help">
          <!-- Rivets -->
          <div class="absolute top-1 left-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          <div class="absolute top-1 right-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          <div class="absolute bottom-1 left-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          <div class="absolute bottom-1 right-1 w-1.5 h-1.5 bg-ink rounded-full"></div>
          
          <div class="font-mono text-[9px] uppercase tracking-widest text-ink/70 mb-1 border-b border-ink/20 pb-1">System Status Plate</div>
          <div class="font-mono text-[10px] uppercase tracking-wider font-medium text-ink leading-relaxed">
            OAuth <span class="text-success inline-block animate-pulse text-[8px] mx-0.5">●</span> connected<br/>
            Rules <span class="text-success inline-block animate-pulse text-[8px] mx-0.5">●</span> deterministic<br/>
            Audit log <span class="text-success inline-block animate-pulse text-[8px] mx-0.5">●</span> recording
          </div>
        </div>
      </div>
    </div>

    <!-- Live Mail Flow Animation -->
    <div class="panel-border bg-cream border-2 border-ink shadow-[8px_8px_0_#15120E] p-1 relative overflow-hidden h-48 flex items-center">
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwYXRoIGQ9Ik0wIDIwaDQwTTIwIDB2NDAiIHN0cm9rZT0iIzE1MTIwRSIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+')] opacity-50 pointer-events-none"></div>
      
      <!-- Central Sorting Lens -->
      <div class="absolute left-1/2 top-0 bottom-0 w-24 border-l-2 border-r-2 border-ink bg-cream/80 backdrop-blur z-20 flex flex-col items-center justify-center -translate-x-1/2">
        <div class="w-12 h-12 rounded-full border-4 border-ink bg-airmail/10 mb-2 relative">
          <div class="absolute inset-2 border-2 border-airmail rounded-full opacity-50"></div>
        </div>
        <div class="font-hand text-ink text-sm rotate-[-10deg]">Scanner</div>
      </div>

      <!-- Belt -->
      <div class="absolute top-1/2 left-0 w-full h-1 bg-ink/20 -translate-y-1/2"></div>
      <div class="absolute top-1/2 left-0 w-full h-1 border-t border-dashed border-ink/40 -translate-y-1/2"></div>

      <!-- Animation Area or Idle State -->
      <div v-if="scanning" class="w-full h-full relative z-10 live-mail-container">
        <!-- JS will inject envelopes here if we want, or we can use CSS. Let's use simple CSS keyframes for 3 envelopes -->
        <div class="absolute top-1/2 left-0 -translate-y-1/2 animate-[conveyor_3s_linear_infinite]" style="animation-delay: 0s;">
          <div class="w-16 h-10 border-2 border-ink bg-cream airmail-edge shadow-sm p-0.5 flex flex-col justify-between"></div>
        </div>
        <div class="absolute top-1/2 left-0 -translate-y-1/2 animate-[conveyor_3s_linear_infinite]" style="animation-delay: 1s;">
          <div class="w-16 h-10 border-2 border-ink bg-cream shadow-sm flex items-center justify-center">
             <div class="w-10 h-1 bg-ink/20"></div>
          </div>
        </div>
        <div class="absolute top-1/2 left-0 -translate-y-1/2 animate-[conveyor_3s_linear_infinite]" style="animation-delay: 2s;">
          <div class="w-16 h-10 border-2 border-ink bg-cream airmail-edge shadow-sm p-0.5"></div>
        </div>
      </div>
      <div v-else class="w-full h-full flex flex-col items-center justify-center relative z-10">
        <svg class="w-8 h-8 text-ink/40 mb-2" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        <span class="font-hand text-2xl text-ink/60 rotate-[-2deg]">Mailroom is quiet. Nothing to sort.</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const stats = ref(null)
const emails = ref(null)
const loading = ref(true)
const scanning = ref(false)

const automatedCount = computed(() => {
  if (!stats.value) return 0
  return (stats.value.total_processed || 0) - (stats.value.needs_review || 0)
})

const reviewCount = computed(() => {
  if (!stats.value) return 0
  return stats.value.needs_review || 0
})

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

<style scoped>
.airmail-edge {
  background: repeating-linear-gradient(
    45deg,
    #FF4B1F,
    #FF4B1F 4px,
    transparent 4px,
    transparent 8px,
    #2B4BFF 8px,
    #2B4BFF 12px,
    transparent 12px,
    transparent 16px
  );
}

.ticket-btn-red {
  background-color: #FF4B1F;
  color: #F1E9DA;
  border: 2px solid #15120E;
  box-shadow: 4px 4px 0 #15120E;
  transition: all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.ticket-btn-red:hover {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 #15120E;
}
.ticket-btn-red:active {
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 #15120E;
}

@keyframes conveyor {
  0% { transform: translate(-100px, -50%); opacity: 0; }
  10% { opacity: 1; }
  45% { transform: translate(calc(50vw - 80px), -50%) scale(1); }
  50% { transform: translate(calc(50vw - 32px), -50%) scale(1.1); }
  55% { transform: translate(calc(50vw + 16px), -50%) scale(1); }
  90% { opacity: 1; }
  100% { transform: translate(100vw, -50%); opacity: 0; }
}

@keyframes draw {
  to {
    stroke-dashoffset: 0;
  }
}
.scribble-circle {
  animation: draw 0.6s ease-out forwards;
}
</style>
