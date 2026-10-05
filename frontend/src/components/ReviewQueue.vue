<template>
  <div class="space-y-6 max-w-5xl mx-auto pb-12">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-12">
      <h2 class="font-serif text-4xl text-ink">Review Queue</h2>
      
      <div v-if="selected.length > 0" class="flex items-center gap-3">
        <span class="font-mono text-xs uppercase tracking-widest bg-ink/10 text-ink px-3 py-1 border border-ink">{{ selected.length }} pinned</span>
        <button @click="bulkApprove" :disabled="processing" class="ticket-btn bg-cream text-ink px-4 py-2 font-mono text-xs font-bold uppercase tracking-widest inline-flex items-center gap-2 interactive">
          <svg v-if="processing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          Approve Stack
        </button>
      </div>
    </div>

    <!-- Feedback Banners -->
    <div v-if="errorMsg" class="p-4 bg-vermilion/10 border-2 border-vermilion text-vermilion font-mono text-xs uppercase tracking-widest font-bold shadow-[4px_4px_0_#FF4B1F]" role="alert">
      ERROR: {{ errorMsg }}
    </div>
    <div v-if="successMsg" class="p-4 bg-ink/10 border-2 border-ink text-ink font-mono text-xs uppercase tracking-widest font-bold shadow-[4px_4px_0_#15120E]" role="status">
      SUCCESS: {{ successMsg }}
    </div>

    <div v-if="loading" class="flex flex-col gap-8 items-center mt-12 animate-pulse">
       <div class="w-full max-w-md h-40 bg-ink/5 border-2 border-ink/20 transform rotate-[-2deg]"></div>
       <div class="w-full max-w-md h-40 bg-ink/5 border-2 border-ink/20 transform rotate-[1deg] -mt-20"></div>
    </div>
    
    <div v-else-if="reviewEmails.length === 0" class="flex flex-col items-center justify-center py-20">
      <span class="font-hand text-4xl text-ink/80 rotate-[-4deg] mb-8">Inbox zero. Go touch grass.</span>
    </div>
    
    <div v-else class="relative w-full max-w-2xl mx-auto flex flex-col items-center pb-24 stack-container perspective-1000">
      <TransitionGroup name="paper-stack">
        <div v-for="(email, index) in reviewEmails" :key="email.message_id" 
          :class="['w-full transition-all duration-500 paper-card relative group', animatingCards[email.message_id] ? 'z-50' : '']"
          :style="{
             marginTop: index === 0 ? '0' : '-80px',
             zIndex: reviewEmails.length - index,
             transform: animatingCards[email.message_id] 
                ? (animatingCards[email.message_id] === 'approve' ? 'translate(200px, 50px) rotate(15deg) opacity(0)' : 'translate(-200px, 50px) rotate(-15deg) opacity(0)') 
                : `rotate(${(index % 2 === 0 ? -1 : 1) * (1 + index * 0.5)}deg) translateY(${index * 5}px) scale(${1 - index * 0.02})`
          }">
          
          <div class="bg-cream border-2 border-ink shadow-[8px_8px_0_#15120E] p-6 relative flex flex-col gap-4 transform-style-3d group-hover:-translate-y-4 group-hover:rotate-0 transition-transform duration-300">
            <!-- Pushpin -->
            <div class="absolute -top-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-vermilion shadow-[2px_4px_0_#15120E] border-2 border-ink z-10">
              <div class="absolute inset-1 rounded-full bg-cream/30"></div>
            </div>

            <!-- Header -->
            <div class="flex justify-between items-start border-b-2 border-ink border-dashed pb-4 pt-2">
              <div class="flex items-center gap-3">
                <input type="checkbox" :value="email.message_id" v-model="selected" class="interactive w-5 h-5 rounded-none border-2 border-ink text-vermilion focus:ring-0 bg-cream" />
                <span class="font-mono text-xs font-bold uppercase tracking-widest bg-ink text-cream px-2 py-0.5">
                  {{ email.category }}
                </span>
                <span class="font-hand text-vermilion text-lg leading-none -mt-2 rotate-[-5deg]">
                  {{ Math.round((email.confidence || 0) * 100) }}% sure
                </span>
              </div>
              <div class="font-mono text-xs tracking-widest text-ink/50">{{ formatTime(email.updated_at) }}</div>
            </div>

            <!-- Subject -->
            <div class="pt-2 pb-4">
              <h3 class="font-serif text-2xl md:text-3xl leading-tight text-ink">{{ email.subject || '(no subject)' }}</h3>
              <p class="font-mono text-xs text-ink/70 mt-2 line-clamp-1">From: <span class="text-ink">{{ email.sender_email || 'unknown' }}</span></p>
            </div>

            <!-- Actions -->
            <div class="flex justify-between items-end pt-4 border-t-2 border-ink">
              <span class="font-mono text-[10px] uppercase tracking-widest text-ink/40 w-1/3">Ref: {{ email.message_id.substring(0,8) }}</span>
              <div class="flex gap-4">
                <button @click="triggerAction(email.message_id, 'reject')" :disabled="processing || animatingCards[email.message_id]" class="ticket-btn-red px-6 py-2 font-mono font-bold text-xs uppercase tracking-widest interactive">
                  Reject
                </button>
                <button @click="triggerAction(email.message_id, 'approve')" :disabled="processing || animatingCards[email.message_id]" class="ticket-btn px-6 py-2 font-mono font-bold text-xs uppercase tracking-widest bg-cream interactive">
                  Approve
                </button>
              </div>
            </div>

            <!-- Stamp Overlay Animation -->
            <div v-if="animatingCards[email.message_id]" class="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
              <div :class="['border-8 font-mono font-bold text-4xl md:text-6xl tracking-widest px-6 py-4 mix-blend-multiply rotate-[-15deg] animate-[stampThud_0.3s_cubic-bezier(0.175,0.885,0.32,1.275)_forwards]', animatingCards[email.message_id] === 'approve' ? 'border-ink text-ink' : 'border-vermilion text-vermilion']">
                {{ animatingCards[email.message_id] === 'approve' ? 'APPROVED' : 'REJECTED' }}
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
  // Play local stamp animation first
  animatingCards.value[id] = action
  // Wait for stamp thud and slide away
  setTimeout(() => {
    reviewAction(id, action)
  }, 600)
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
    // successMsg.value = `Email ${action}d successfully.`
    selected.value = selected.value.filter(s => s !== id)
    // Remove locally for snappier UI before refetch
    emails.value = emails.value.filter(e => e.message_id !== id)
  } catch (e) {
    errorMsg.value = "Failed to apply action."
    animatingCards.value[id] = null // Reset animation
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
  
  // Trigger animation for all selected
  selected.value.forEach(id => { animatingCards.value[id] = 'approve' })
  
  // Wait for animation
  await new Promise(r => setTimeout(r, 600))
  
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
    // Clear animation states
    animatingCards.value = {}
  }
}

onMounted(() => {
  fetchEmails()
})
</script>

<style scoped>
.ticket-btn {
  background-color: #F1E9DA;
  border: 2px solid #15120E;
  box-shadow: 4px 4px 0 #15120E;
  transition: all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.ticket-btn:hover:not(:disabled) {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 #15120E;
}
.ticket-btn:active:not(:disabled) {
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 #15120E;
}
.ticket-btn:disabled {
  opacity: 0.5; cursor: not-allowed;
}

.ticket-btn-red {
  background-color: #FF4B1F;
  color: #F1E9DA;
  border: 2px solid #15120E;
  box-shadow: 4px 4px 0 #15120E;
  transition: all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.ticket-btn-red:hover:not(:disabled) {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 #15120E;
}
.ticket-btn-red:active:not(:disabled) {
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 #15120E;
}
.ticket-btn-red:disabled {
  opacity: 0.5; cursor: not-allowed;
}

@keyframes stampThud {
  0% { transform: scale(1.5) rotate(-15deg); opacity: 0; }
  60% { transform: scale(0.9) rotate(-15deg); opacity: 1; }
  80% { transform: scale(1.05) rotate(-15deg); opacity: 1; }
  100% { transform: scale(1) rotate(-15deg); opacity: 1; }
}

.paper-stack-move { transition: transform 0.5s ease; }
.paper-stack-enter-active { transition: all 0.5s ease; }
.paper-stack-leave-active { transition: all 0.5s cubic-bezier(0.5, 0, 0, 1); position: absolute; }
.paper-stack-enter-from { opacity: 0; transform: translateY(-50px) scale(0.9); }
/* Leave animation is handled by inline styles mapped to animatingCards state before leaving */
</style>
