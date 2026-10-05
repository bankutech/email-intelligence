<template>
  <div class="max-w-4xl mx-auto space-y-8 pb-12 animate-slide-up">
    
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h2 class="font-display font-bold text-3xl text-nyalaslate mb-2">Review Queue</h2>
        <p class="text-nyalaslate/60 text-lg">Emails that require your manual confirmation.</p>
      </div>

      <div class="flex gap-4">
        <button v-if="selected.length > 0" @click="bulkApprove" :disabled="processing" class="px-6 py-2.5 rounded-full bg-nyalablue text-nyalawhite font-medium shadow-md shadow-nyalablue/20 hover:bg-nyalablue/90 hover:-translate-y-0.5 transition-all disabled:opacity-50">
          Approve Selected ({{ selected.length }})
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div v-if="errorMsg" class="p-4 bg-danger/10 text-danger rounded-xl font-medium text-sm">{{ errorMsg }}</div>
    <div v-if="successMsg" class="p-4 bg-success/10 text-success rounded-xl font-medium text-sm">{{ successMsg }}</div>

    <div v-if="loading" class="flex flex-col gap-6 animate-pulse">
      <div class="h-48 bg-nyalaslate/5 rounded-3xl" v-for="i in 3" :key="i"></div>
    </div>
    
    <div v-else-if="reviewEmails.length === 0" class="flex flex-col items-center justify-center py-24 bg-nyalawhite rounded-3xl shadow-sm border border-nyalaslate/5 text-center">
      <div class="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mb-6">
        <svg class="w-8 h-8 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
      </div>
      <h3 class="font-display font-bold text-2xl text-nyalaslate mb-2">Queue is empty</h3>
      <p class="text-nyalaslate/60">You're all caught up! No emails need your attention right now.</p>
    </div>
    
    <div v-else class="space-y-6 relative">
      <TransitionGroup name="fade-slide">
        <div v-for="email in reviewEmails" :key="email.message_id" class="w-full transition-all">
          <div :class="['bg-nyalawhite rounded-3xl shadow-sm border p-6 md:p-8 relative overflow-hidden transition-all', animatingCards[email.message_id] ? 'opacity-0 scale-95 translate-x-12' : 'opacity-100 scale-100 translate-x-0 border-nyalaslate/5 hover:shadow-md']">
            
            <div class="flex justify-between items-start mb-6">
              <div class="flex items-center gap-4">
                <input type="checkbox" :value="email.message_id" v-model="selected" class="w-5 h-5 rounded border-nyalaslate/20 text-nyalablue focus:ring-nyalablue" />
                <span class="px-3 py-1 text-xs font-bold rounded-full bg-nyalaslate/10 text-nyalaslate uppercase tracking-wider">
                  {{ email.category }}
                </span>
                <span class="text-sm font-medium" :class="email.confidence < 0.6 ? 'text-danger' : 'text-nyalablue'">
                  {{ Math.round((email.confidence || 0) * 100) }}% confidence
                </span>
              </div>
              <div class="text-sm font-medium text-nyalaslate/40">{{ formatTime(email.updated_at) }}</div>
            </div>

            <!-- Subject -->
            <div class="mb-6">
              <h3 class="font-display font-bold text-2xl md:text-3xl text-nyalaslate mb-2">{{ email.subject || '(no subject)' }}</h3>
              <p class="text-nyalaslate/60 mb-4">From: <span class="text-nyalaslate font-medium">{{ email.sender_email || 'unknown sender' }}</span></p>
              <div v-if="email.reason" class="bg-nyalaslate/5 p-4 rounded-xl border border-nyalaslate/10">
                <span class="text-xs font-bold text-nyalaslate/50 uppercase tracking-wider block mb-1">AI Reasoning</span>
                <p class="text-sm text-nyalaslate/90 italic">"{{ email.reason }}"</p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-between items-end pt-6 border-t border-nyalaslate/5">
              <span class="text-xs font-mono text-nyalaslate/30 uppercase tracking-widest">ID: {{ email.message_id.substring(0,8) }}</span>
              <div class="flex gap-4">
                <button @click="triggerAction(email.message_id, 'reject')" :disabled="processing || animatingCards[email.message_id]" class="px-6 py-2.5 rounded-full bg-danger/10 text-danger font-bold hover:bg-danger/20 transition-colors">
                  Reject
                </button>
                <button @click="triggerAction(email.message_id, 'approve')" :disabled="processing || animatingCards[email.message_id]" class="px-6 py-2.5 rounded-full bg-nyalablue text-nyalawhite font-bold shadow-md shadow-nyalablue/20 hover:bg-nyalablue/90 hover:-translate-y-0.5 transition-all">
                  Approve
                </button>
              </div>
            </div>

          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const emails = ref([])
const loading = ref(true)
const processing = ref(false)
const selected = ref([])
const errorMsg = ref('')
const successMsg = ref('')
const animatingCards = ref({})

const reviewEmails = computed(() => {
  return emails.value.filter(e => e.status === 'review')
})

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getDate()}/${d.getMonth()+1}/${d.getFullYear()} ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
}

const clearMsgs = () => {
  errorMsg.value = ''
  successMsg.value = ''
}

const fetchEmails = async () => {
  loading.value = true
  clearMsgs()
  try {
    const res = await fetch('/api/emails')
    if (res.ok) {
      emails.value = await res.json()
    } else {
      errorMsg.value = "Failed to load review queue. Please try again."
    }
  } catch (e) {
    errorMsg.value = "Network error while loading queue."
  } finally {
    loading.value = false
  }
}

const triggerAction = (id, action) => {
  animatingCards.value[id] = action
  setTimeout(() => {
    reviewAction(id, action)
  }, 400)
}

const reviewAction = async (id, action) => {
  processing.value = true
  clearMsgs()
  try {
    const res = await fetch(`/api/emails/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    })
    if (!res.ok) throw new Error('Action failed')
    selected.value = selected.value.filter(s => s !== id)
    emails.value = emails.value.filter(e => e.message_id !== id)
  } catch (e) {
    errorMsg.value = "Failed to apply action."
    animatingCards.value[id] = null
  } finally {
    processing.value = false
  }
}

const bulkApprove = async () => {
  if (!confirm(`Approve ${selected.value.length} selected emails?`)) return
  processing.value = true
  clearMsgs()
  
  const total = selected.value.length
  let succeeded = 0
  
  selected.value.forEach(id => { animatingCards.value[id] = 'approve' })
  
  await new Promise(r => setTimeout(r, 400))
  
  try {
    const promises = selected.value.map(async (id) => {
      const res = await fetch(`/api/emails/${id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve' })
      })
      if (!res.ok) throw new Error('Failed')
      return id
    })
    
    const results = await Promise.allSettled(promises)
    const successfulIds = results.filter(r => r.status === 'fulfilled').map(r => r.value)
    
    succeeded = successfulIds.length
    selected.value = selected.value.filter(id => !successfulIds.includes(id))
    
    emails.value = emails.value.filter(e => !successfulIds.includes(e.message_id))
    
    if (succeeded === total) {
      successMsg.value = `Successfully approved all ${total} emails.`
    } else {
      errorMsg.value = `Partial failure: Approved ${succeeded} out of ${total} emails.`
    }
  } catch (e) {
    errorMsg.value = "An error occurred during bulk approval."
  } finally {
    processing.value = false
    animatingCards.value = {}
  }
}

onMounted(() => {
  fetchEmails()
})
</script>

<style scoped>
.fade-slide-move { transition: transform 0.5s ease; }
.fade-slide-enter-active { transition: all 0.5s ease; }
.fade-slide-leave-active { transition: all 0.4s ease; position: absolute; width: 100%; }
.fade-slide-enter-from { opacity: 0; transform: translateY(20px); }
</style>
