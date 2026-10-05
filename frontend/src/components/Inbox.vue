<template>
  <div class="max-w-6xl mx-auto space-y-6 pb-12 relative animate-slide-up">
    
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
      <h2 class="font-display font-bold text-3xl text-nyalaslate">Processed Emails</h2>
      <div class="relative w-full sm:w-64">
        <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-nyalaslate/50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        <input v-model="searchQuery" type="text" placeholder="Search emails..." class="w-full pl-10 pr-4 py-2.5 bg-nyalawhite border border-nyalaslate/10 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-nyalablue/20 focus:border-nyalablue text-nyalaslate transition-all">
      </div>
    </div>

    <div v-if="loading" class="flex flex-col gap-4">
      <div class="h-20 bg-nyalaslate/5 rounded-2xl animate-pulse" v-for="i in 5" :key="i"></div>
    </div>
    
    <div v-else-if="filteredEmails.length === 0" class="flex flex-col items-center justify-center py-24 bg-nyalawhite rounded-3xl shadow-sm border border-nyalaslate/5">
      <div class="w-16 h-16 rounded-full bg-nyalaslate/5 flex items-center justify-center mb-4">
        <svg class="w-8 h-8 text-nyalaslate/30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg>
      </div>
      <span class="font-medium text-lg text-nyalaslate/60">No records found.</span>
    </div>
    
    <div v-else class="flex flex-col gap-4">
      <div v-for="(email, i) in paginatedEmails" :key="email.message_id" class="bg-nyalawhite rounded-2xl shadow-sm border border-nyalaslate/5 overflow-hidden transition-all hover:shadow-md">
        
        <button @click="toggleRow(email.message_id)" class="w-full flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 md:p-6 text-left">
          
          <div class="flex items-center gap-6 w-full md:w-auto overflow-hidden">
            <span class="text-xs font-medium text-nyalaslate/40 w-12 shrink-0">{{ formatTime(email.updated_at) }}</span>
            <div class="flex-1 min-w-0">
              <h4 class="font-display font-semibold text-lg text-nyalaslate truncate">{{ email.subject || '(no subject)' }}</h4>
              <div class="text-sm text-nyalaslate/60 mt-1 truncate">
                {{ email.sender_email || 'unknown sender' }} &middot; Confidence: {{ Math.round((email.confidence || 0) * 100) }}%
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-4 shrink-0 mt-2 md:mt-0 ml-auto md:ml-0">
            <span :class="['px-3 py-1 text-xs font-bold rounded-full', categoryClass(email.category)]">
              {{ email.category }}
            </span>
            <svg class="w-5 h-5 text-nyalaslate/30 transform transition-transform" :class="{'rotate-180': expandedRows[email.message_id]}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </div>
        </button>

        <div v-if="expandedRows[email.message_id]" class="bg-nyalaslate/[0.02] p-5 md:p-6 border-t border-nyalaslate/5">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h5 class="text-xs font-bold text-nyalaslate/50 uppercase tracking-wider mb-2">Executed Actions</h5>
              <p class="text-sm text-nyalaslate font-medium bg-nyalawhite px-3 py-2 rounded border border-nyalaslate/10 inline-block">{{ email.actions || 'None' }}</p>
            </div>
            <div>
              <h5 class="text-xs font-bold text-nyalaslate/50 uppercase tracking-wider mb-2">AI Determination</h5>
              <p class="text-sm text-nyalaslate mb-2">Category: <strong>{{ email.category }}</strong></p>
              <p v-if="email.reason" class="text-sm text-nyalaslate/80 italic border-l-2 border-nyalablue/30 pl-3">"{{ email.reason }}"</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center items-center gap-2 mt-8">
      <button @click="currentPage--" :disabled="currentPage === 1" class="p-2 rounded-full hover:bg-nyalaslate/5 text-nyalaslate disabled:opacity-30 disabled:hover:bg-transparent transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
      </button>
      <span class="font-medium text-sm text-nyalaslate bg-nyalawhite px-4 py-1.5 rounded-full border border-nyalaslate/10">{{ currentPage }} of {{ totalPages }}</span>
      <button @click="currentPage++" :disabled="currentPage === totalPages" class="p-2 rounded-full hover:bg-nyalaslate/5 text-nyalaslate disabled:opacity-30 disabled:hover:bg-transparent transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
      </button>
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

const categoryClass = (cat) => {
  if (!cat) return 'bg-nyalaslate/10 text-nyalaslate'
  const c = cat.toUpperCase()
  if (c === 'SPAM') return 'bg-danger/10 text-danger'
  if (c === 'URGENT') return 'bg-nyalablue/10 text-nyalablue'
  if (c === 'NEWSLETTER') return 'bg-success/10 text-success'
  return 'bg-nyalaslate/10 text-nyalaslate'
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
