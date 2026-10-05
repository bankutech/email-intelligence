<template>
  <div class="space-y-6 max-w-5xl mx-auto">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <h2 class="text-xl font-semibold text-textMain">Review Queue</h2>
      
      <div v-if="selected.length > 0" class="flex items-center gap-3">
        <span class="text-sm font-medium text-textMuted bg-surface px-3 py-1 rounded-full border border-border">{{ selected.length }} selected</span>
        <button @click="bulkApprove" :disabled="processing" class="btn btn-success text-sm flex items-center gap-2">
          <svg v-if="processing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          Approve All
        </button>
      </div>
    </div>

    <!-- Feedback Banners -->
    <div v-if="errorMsg" class="p-4 bg-danger/10 border border-danger/20 rounded-md text-danger text-sm" role="alert">
      {{ errorMsg }}
    </div>
    <div v-if="successMsg" class="p-4 bg-success/10 border border-success/20 rounded-md text-success text-sm" role="status">
      {{ successMsg }}
    </div>

    <div v-if="loading" class="space-y-4">
      <div class="h-24 bg-surfaceElevated animate-pulse rounded-lg" v-for="i in 3" :key="i"></div>
    </div>
    
    <div v-else-if="reviewEmails.length === 0" class="panel p-12 text-center border-dashed border-2 border-border bg-transparent">
      <svg class="w-12 h-12 mx-auto text-textMuted/40 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 13l4 4L19 7"></path></svg>
      <p class="text-lg font-medium text-textMain">Queue is empty</p>
      <p class="text-textMuted mt-1">All emails have been processed.</p>
    </div>
    
    <div v-else class="space-y-4">
      <!-- Desktop Table View -->
      <div class="hidden md:block panel overflow-hidden">
        <table class="w-full text-left text-sm whitespace-nowrap">
          <thead class="bg-surfaceElevated border-b border-border">
            <tr>
              <th scope="col" class="p-4 w-4">
                <input type="checkbox" :checked="selected.length === reviewEmails.length && reviewEmails.length > 0" @change="toggleAll" class="rounded border-border bg-background focus:ring-primary w-4 h-4" aria-label="Select all rows" />
              </th>
              <th scope="col" class="p-4 font-medium text-textMuted">Subject</th>
              <th scope="col" class="p-4 font-medium text-textMuted">Category</th>
              <th scope="col" class="p-4 font-medium text-textMuted">Confidence</th>
              <th scope="col" class="p-4 font-medium text-textMuted text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="email in reviewEmails" :key="email.message_id" class="hover:bg-surfaceElevated/50 transition-colors" :class="{'bg-surfaceElevated/30': selected.includes(email.message_id)}">
              <td class="p-4">
                <input type="checkbox" :value="email.message_id" v-model="selected" class="rounded border-border bg-background focus:ring-primary w-4 h-4" :aria-label="'Select email ' + email.subject" />
              </td>
              <td class="p-4">
                <div class="font-medium text-textMain truncate max-w-xs" :title="email.subject">{{ email.subject || '(no subject)' }}</div>
                <div class="text-xs text-textMuted mt-0.5">{{ formatTime(email.updated_at) }}</div>
              </td>
              <td class="p-4">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase bg-surface border border-border text-textMuted">{{ email.category }}</span>
              </td>
              <td class="p-4">
                <div class="flex items-center gap-2">
                  <div class="w-16 h-1.5 bg-surface rounded-full overflow-hidden">
                    <div class="h-full bg-warning" :style="`width: ${(email.confidence || 0) * 100}%`"></div>
                  </div>
                  <span class="text-xs font-medium">{{ Math.round((email.confidence || 0) * 100) }}%</span>
                </div>
              </td>
              <td class="p-4 text-right">
                <button @click="reviewAction(email.message_id, 'approve')" :disabled="processing" class="btn btn-secondary text-xs">Approve</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile Stacked Card View -->
      <div class="md:hidden space-y-4">
        <div class="flex items-center gap-2 px-1">
          <input type="checkbox" id="selectAllMob" :checked="selected.length === reviewEmails.length && reviewEmails.length > 0" @change="toggleAll" class="rounded border-border bg-background focus:ring-primary w-4 h-4" />
          <label for="selectAllMob" class="text-sm text-textMuted font-medium">Select All</label>
        </div>
        <div v-for="email in reviewEmails" :key="email.message_id" class="panel p-4 flex flex-col gap-3 transition-colors" :class="{'border-primary/50 bg-primary/5': selected.includes(email.message_id)}">
          <div class="flex justify-between items-start gap-2">
            <div class="flex items-start gap-3 overflow-hidden">
              <input type="checkbox" :value="email.message_id" v-model="selected" class="rounded border-border bg-background focus:ring-primary w-4 h-4 mt-1 shrink-0" :aria-label="'Select email ' + email.subject" />
              <div class="min-w-0">
                <div class="font-medium text-textMain line-clamp-2 leading-snug">{{ email.subject || '(no subject)' }}</div>
                <div class="text-xs text-textMuted mt-1">{{ formatTime(email.updated_at) }}</div>
              </div>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase bg-surface border border-border text-textMuted shrink-0">{{ email.category }}</span>
          </div>
          <div class="flex justify-between items-end border-t border-border pt-3 mt-1">
            <div class="flex items-center gap-2">
              <div class="text-xs text-textMuted">Confidence</div>
              <span class="text-xs font-medium text-warning">{{ Math.round((email.confidence || 0) * 100) }}%</span>
            </div>
            <button @click="reviewAction(email.message_id, 'approve')" :disabled="processing" class="btn btn-secondary text-xs px-3 py-1.5">Approve</button>
          </div>
        </div>
      </div>
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

const reviewEmails = computed(() => {
  return emails.value.filter(e => e.status === 'review')
})

const toggleAll = (e) => {
  if (e.target.checked) {
    selected.value = reviewEmails.value.map(em => em.message_id)
  } else {
    selected.value = []
  }
}

const formatTime = (ts) => {
  if (!ts) return ''
  return new Date(ts).toLocaleString()
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
    successMsg.value = 'Email approved successfully.'
    selected.value = selected.value.filter(s => s !== id)
    await fetchEmails()
  } catch (e) {
    errorMsg.value = "Failed to apply action."
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
    
    if (succeeded === total) {
      successMsg.value = `Successfully approved all ${total} emails.`
    } else {
      errorMsg.value = `Partial failure: Approved ${succeeded} out of ${total} emails.`
    }
    
    await fetchEmails()
  } catch (e) {
    errorMsg.value = "An unexpected error occurred during bulk approval."
  } finally {
    processing.value = false
  }
}

onMounted(() => {
  fetchEmails()
})
</script>
