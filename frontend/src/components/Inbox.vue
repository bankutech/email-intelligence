<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <h2 class="text-xl font-semibold text-textMain">Processed Emails</h2>
      <div class="relative w-full sm:w-64">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        <input v-model="searchQuery" type="text" placeholder="Search..." class="w-full pl-9 pr-4 py-2 bg-surface border border-border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-primary text-textMain transition-shadow" aria-label="Search processed emails">
      </div>
    </div>

    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="h-32 bg-surfaceElevated animate-pulse rounded" v-for="i in 4" :key="i"></div>
    </div>
    
    <div v-else-if="filteredEmails.length === 0" class="panel p-12 text-center">
      <p class="text-lg font-medium text-textMain">No emails found</p>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="email in paginatedEmails" :key="email.message_id" class="panel p-4 flex flex-col h-full hover:border-textMuted/50 transition-colors">
        <div class="flex justify-between items-start mb-3">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase bg-surface border border-border text-textMuted">{{ email.category }}</span>
          <div class="text-xs text-textMuted">{{ formatTime(email.updated_at) }}</div>
        </div>
        <h4 class="font-medium text-textMain mb-1 line-clamp-2 leading-snug">{{ email.subject || '(no subject)' }}</h4>
        
        <div class="mt-auto pt-3 border-t border-border flex justify-between items-end">
          <div class="text-xs">
             <div class="text-textMuted mb-1">Confidence</div>
             <span class="font-medium text-textMain">{{ Math.round((email.confidence || 0) * 100) }}%</span>
          </div>
          <div class="text-xs text-textMuted truncate max-w-[150px]" :title="email.actions">{{ email.actions || 'Processed' }}</div>
        </div>
      </div>
    </div>

    <div v-if="totalPages > 1" class="flex justify-center items-center gap-4 mt-6">
      <button @click="currentPage--" :disabled="currentPage === 1" class="btn btn-secondary text-sm" aria-label="Previous page">Previous</button>
      <span class="text-sm text-textMuted">Page {{ currentPage }} of {{ totalPages }}</span>
      <button @click="currentPage++" :disabled="currentPage === totalPages" class="btn btn-secondary text-sm" aria-label="Next page">Next</button>
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

const filteredEmails = computed(() => {
  if (!searchQuery.value) return emails.value
  const q = searchQuery.value.toLowerCase()
  return emails.value.filter(e => 
    (e.subject && e.subject.toLowerCase().includes(q)) || 
    (e.category && e.category.toLowerCase().includes(q))
  )
})

const totalPages = computed(() => Math.ceil(filteredEmails.value.length / itemsPerPage))

watch(searchQuery, () => {
  currentPage.value = 1
})

const paginatedEmails = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredEmails.value.slice(start, start + itemsPerPage)
})

const formatTime = (ts) => {
  if (!ts) return ''
  return new Date(ts).toLocaleString()
}

const fetchEmails = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/emails')
    if (res.ok) {
      emails.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchEmails()
})
</script>
