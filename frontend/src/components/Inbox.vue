<template>
  <div class="max-w-6xl mx-auto space-y-6 pb-12 relative">
    
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
      <h2 class="font-serif text-4xl text-ink">Processed Ledger</h2>
      <div class="relative w-full sm:w-64 border-2 border-ink shadow-[4px_4px_0_#15120E] bg-cream">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        <input v-model="searchQuery" type="text" placeholder="Search ledger..." class="w-full pl-9 pr-4 py-2 bg-transparent text-sm focus:outline-none font-mono text-ink placeholder-ink/50" aria-label="Search processed emails">
      </div>
    </div>

    <div v-if="loading" class="flex flex-col gap-4 animate-pulse">
      <div class="h-12 bg-ink/5 border-b-2 border-dashed border-ink/20" v-for="i in 5" :key="i"></div>
    </div>
    
    <div v-else-if="filteredEmails.length === 0" class="flex flex-col items-center justify-center py-20">
      <span class="font-hand text-4xl text-ink/80 rotate-[-4deg] mb-8">No records found.</span>
    </div>
    
    <div v-else class="receipt-strip w-full bg-cream border-r-2 border-ink shadow-[8px_8px_0_#15120E] relative overflow-hidden">
      <!-- Top edge of receipt -->
      <div class="w-full h-4 border-b-2 border-ink border-dashed opacity-50 mb-4"></div>

      <div class="px-8 pb-8 flex flex-col">
        <div v-for="(email, i) in paginatedEmails" :key="email.message_id" class="flex flex-col">
          <!-- Row -->
          <button @click="toggleRow(email.message_id)" class="interactive flex flex-col md:flex-row items-start md:items-center justify-between gap-4 py-4 border-b-2 border-dashed border-ink/30 hover:bg-ink/5 transition-colors text-left relative group">
            
            <div class="flex items-center gap-4 w-full md:w-auto">
              <span class="font-mono text-xs text-ink/40 w-12">{{ formatTime(email.updated_at) }}</span>
              <div class="flex-1">
                <h4 class="font-serif text-xl text-ink group-hover:text-vermilion transition-colors">{{ email.subject || '(no subject)' }}</h4>
                <div class="font-mono text-[10px] uppercase tracking-widest text-ink/60 mt-1">
                  CONFIDENCE: {{ Math.round((email.confidence || 0) * 100) }}% — {{ email.sender_email || 'unknown' }}
                </div>
              </div>
            </div>
            
            <div class="flex items-center gap-4 shrink-0 mt-2 md:mt-0">
              <span :class="['px-2 py-0.5 font-mono text-[10px] font-bold tracking-widest uppercase border-2 rotate-[-2deg]', email.category === 'SPAM' ? 'border-vermilion text-vermilion' : 'border-ink text-ink']">
                {{ email.category }}
              </span>
              <svg class="w-4 h-4 text-ink/30 transform transition-transform" :class="{'rotate-180': expandedRows[email.message_id]}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </button>

          <!-- Expanded Audit Trail (Telegram style) -->
          <div v-if="expandedRows[email.message_id]" class="bg-[#e5ddd0] p-6 border-b-2 border-dashed border-ink/30 relative">
            <div class="absolute top-2 right-2 font-mono text-[8px] uppercase tracking-widest text-ink/30">AUDIT TRAIL // {{ email.message_id }}</div>
            <div class="font-mono text-xs text-ink whitespace-pre-wrap leading-relaxed max-w-3xl">
              ++ INCOMING TRANSMISSION ++
              <br/><br/>
              ACTION EXECUTED: <span class="font-bold bg-ink text-cream px-1">{{ email.actions || 'None' }}</span>
              <br/><br/>
              AI DETERMINATION: <span class="italic">{{ email.category }}</span>
              <br/><br/>
              ++ END OF RECORD ++
            </div>
          </div>
        </div>
      </div>
      
      <!-- Bottom torn edge -->
      <div class="torn-bottom w-full h-8 bg-cream absolute bottom-0 left-0"></div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center items-center gap-6 mt-8 font-mono uppercase tracking-widest text-xs">
      <button @click="currentPage--" :disabled="currentPage === 1" class="interactive hover:text-vermilion disabled:opacity-30 disabled:hover:text-ink transition-colors">&larr; PREV</button>
      <span class="font-bold text-ink border-b-2 border-ink px-2">{{ currentPage }} / {{ totalPages }}</span>
      <button @click="currentPage++" :disabled="currentPage === totalPages" class="interactive hover:text-vermilion disabled:opacity-30 disabled:hover:text-ink transition-colors">NEXT &rarr;</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'

const emails = ref([])
const loading = ref(true)
const searchQuery = ref('')
const currentPage = ref(1)
const itemsPerPage = 10
const expandedRows = ref({})

const fetchEmails = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/emails')
    if (res.ok) {
      const data = await res.json()
      emails.value = data.filter(e => e.status !== 'review')
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const toggleRow = (id) => {
  expandedRows.value[id] = !expandedRows.value[id]
}

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const filteredEmails = computed(() => {
  if (!searchQuery.value) return emails.value
  const q = searchQuery.value.toLowerCase()
  return emails.value.filter(e => 
    (e.subject && e.subject.toLowerCase().includes(q)) || 
    (e.category && e.category.toLowerCase().includes(q)) ||
    (e.sender_email && e.sender_email.toLowerCase().includes(q))
  )
})

const totalPages = computed(() => Math.ceil(filteredEmails.value.length / itemsPerPage) || 1)

const paginatedEmails = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredEmails.value.slice(start, start + itemsPerPage)
})

watch(searchQuery, () => {
  currentPage.value = 1
})

onMounted(() => {
  fetchEmails()
})
</script>

<style scoped>
.receipt-strip {
  background-image: 
    radial-gradient(circle at 0px 10px, transparent 4px, #15120E 5px, #15120E 6px, transparent 7px);
  background-size: 100% 20px;
  background-position: -6px 0;
  background-repeat: repeat-y;
  border-left: 2px dashed #15120E;
}

.torn-bottom {
  mask-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 100 10" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><path d="M0,0 L100,0 L100,2 Q95,10 90,2 Q85,10 80,2 Q75,10 70,2 Q65,10 60,2 Q55,10 50,2 Q45,10 40,2 Q35,10 30,2 Q25,10 20,2 Q15,10 10,2 Q5,10 0,2 Z" fill="black"/></svg>');
  mask-size: 100% 10px;
  mask-position: bottom;
  mask-repeat: no-repeat;
}
</style>
