<template>
  <div class="space-y-6 animate-fade pb-12 max-w-4xl mx-auto">
    
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-surface p-4 sm:p-5 rounded-xl border border-border shadow-xs">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-semibold text-ink font-serif tracking-tight">Human Review Queue</h2>
          <span class="px-2 py-0.5 rounded-full text-xs font-mono font-semibold" :class="reviewCount > 0 ? 'bg-status-warningBg text-status-warning border border-status-warningBorder' : 'bg-status-successBg text-status-success border border-status-successBorder'">
            {{ reviewCount }} pending
          </span>
        </div>
        <p class="text-xs text-ink-muted mt-1">Emails requiring human verification before automated actions take effect.</p>
      </div>

      <div class="flex items-center gap-3">
        <button
          v-if="selected.length > 0"
          @click="bulkApprove"
          :disabled="isProcessing"
          class="px-4 py-2 text-xs font-semibold rounded-lg bg-brand text-surface hover:bg-brand-hover shadow-subtle transition-all disabled:opacity-50 inline-flex items-center gap-2"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
          </svg>
          Approve Selected ({{ selected.length }})
        </button>
      </div>
    </div>

    <!-- Alert / Feedback Notification -->
    <div v-if="feedbackMsg" :class="['p-3.5 rounded-xl text-xs font-medium border flex items-center justify-between', feedbackError ? 'bg-status-dangerBg text-status-danger border-status-dangerBorder' : 'bg-status-successBg text-status-success border-status-successBorder']">
      <span>{{ feedbackMsg }}</span>
      <button @click="feedbackMsg = ''" class="hover:opacity-75 font-mono text-sm">&times;</button>
    </div>

    <!-- Empty Queue State -->
    <div v-if="reviewEmails.length === 0" class="py-16 bg-surface rounded-xl border border-border shadow-xs text-center space-y-3">
      <div class="w-12 h-12 rounded-xl bg-status-successBg text-status-success flex items-center justify-center mx-auto border border-status-successBorder">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
      </div>
      <div>
        <h3 class="text-sm font-semibold text-ink">Review Queue is Clear</h3>
        <p class="text-xs text-ink-muted max-w-sm mx-auto mt-0.5">All incoming emails met automation confidence criteria (&ge; 85%) or have been approved.</p>
      </div>
    </div>

    <!-- Review Items List -->
    <div v-else class="space-y-3.5">
      <div
        v-for="email in reviewEmails"
        :key="email.message_id"
        class="bg-surface rounded-xl border border-border shadow-xs p-5 space-y-3.5 hover:border-brand/40 transition-all"
      >
        <!-- Card Top Bar -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-center gap-3">
            <input
              type="checkbox"
              :value="email.message_id"
              v-model="selected"
              :aria-label="'Select email ' + (email.subject || email.message_id)"
              class="w-4 h-4 rounded border-border text-brand focus:ring-brand"
            />
            
            <span :class="['px-2.5 py-0.5 text-xs font-semibold rounded-md border uppercase tracking-wider', categoryBadgeClass(email.category)]">
              {{ email.category }}
            </span>

            <span class="text-xs font-mono font-medium px-2 py-0.5 rounded border bg-status-warningBg text-status-warning border-status-warningBorder">
              {{ Math.round((email.confidence || 0) * 100) }}% confidence
            </span>
          </div>

          <span class="text-xs font-mono text-ink-muted">
            {{ formatFullTime(email.updated_at || email.email_timestamp) }}
          </span>
        </div>

        <!-- Subject & Sender -->
        <div>
          <h3 class="text-base font-semibold text-ink leading-snug">
            {{ email.subject || '(no subject)' }}
          </h3>
          <p class="text-xs text-ink-secondary mt-1">
            From: <span class="font-mono text-ink">{{ email.sender_email || email.sender || 'Unknown Sender' }}</span>
          </p>
        </div>

        <!-- Flag Warning / Triage Reason Box -->
        <div class="bg-canvas-subtle p-3.5 rounded-xl border border-border-subtle space-y-2 text-xs">
          <div class="flex items-center gap-2 text-status-warning font-semibold">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <span>Flag Reason: {{ getTriageReason(email) }}</span>
          </div>
          
          <p v-if="email.reason" class="text-ink-secondary italic pl-6">
            "{{ email.reason }}"
          </p>
        </div>

        <!-- Triage Action Controls -->
        <div class="pt-3 border-t border-border-subtle flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <!-- Manual Category Override Dropdown -->
          <div class="flex items-center gap-2">
            <span class="text-xs text-ink-muted font-medium shrink-0">Re-categorize:</span>
            <select
              v-model="correctionMap[email.message_id]"
              :aria-label="'Re-categorize ' + (email.subject || email.message_id)"
              class="text-xs px-2.5 py-1.5 bg-canvas-subtle border border-border rounded-lg text-ink font-medium focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
            >
              <option value="" disabled>Select category...</option>
              <option value="urgent">Urgent</option>
              <option value="important">Important</option>
              <option value="work">Work</option>
              <option value="academic">Academic</option>
              <option value="meeting">Meeting</option>
              <option value="promotional">Promotional</option>
              <option value="normal">Normal</option>
              <option value="spam">Spam</option>
            </select>
            <button
              @click="submitCorrection(email.message_id)"
              :disabled="!correctionMap[email.message_id] || isProcessing"
              class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface border border-border text-ink hover:bg-canvas-muted disabled:opacity-40 transition-colors shrink-0"
            >
              Apply
            </button>
          </div>

          <!-- Quick Action Buttons -->
          <div class="flex items-center gap-2 justify-end">
            <button
              @click="submitAction(email.message_id, 'dismiss')"
              :disabled="isProcessing"
              class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-canvas-subtle text-ink-secondary hover:text-ink hover:bg-canvas-muted border border-border transition-colors"
            >
              Dismiss
            </button>
            <button
              @click="submitAction(email.message_id, 'approve')"
              :disabled="isProcessing"
              class="px-4 py-1.5 text-xs font-semibold rounded-lg bg-brand text-surface hover:bg-brand-hover shadow-subtle transition-all"
            >
              Approve ({{ email.category }})
            </button>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  emails: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['updated', 'refresh'])

const selected = ref([])
const isProcessing = ref(false)
const feedbackMsg = ref('')
const feedbackError = ref(false)
const correctionMap = ref({})

const reviewEmails = computed(() => {
  return props.emails.filter(e => e.status === 'review')
})

const reviewCount = computed(() => reviewEmails.value.length)

const getTriageReason = (email) => {
  if (email.rule_flags && email.rule_flags.length > 0) {
    const flags = Array.isArray(email.rule_flags) ? email.rule_flags : JSON.parse(email.rule_flags)
    return `Security Flag: ${flags.join(', ').replace(/_/g, ' ')}`
  }
  const conf = Math.round((email.confidence || 0) * 100)
  return `Confidence (${conf}%) below automation threshold (85%)`
}

const formatFullTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const categoryBadgeClass = (cat) => {
  const c = (cat || '').toLowerCase()
  if (c === 'urgent') return 'bg-[#fef2f2] text-[#991b1b] border-[#fecaca]'
  if (c === 'work') return 'bg-[#eef2ff] text-[#3730a3] border-[#c7d2fe]'
  if (c === 'academic') return 'bg-[#ecfeff] text-[#0e7490] border-[#a5f3fc]'
  if (c === 'meeting') return 'bg-[#faf5ff] text-[#6b21a8] border-[#e9d5ff]'
  if (c === 'promotional') return 'bg-[#f8fafc] text-[#475569] border-[#e2e8f0]'
  if (c === 'spam') return 'bg-[#fff7ed] text-[#c2410c] border-[#fed7aa]'
  return 'bg-[#f4f4f5] text-[#52525b] border-[#e4e4e7]'
}

const submitAction = async (messageId, action) => {
  isProcessing.value = true
  feedbackMsg.value = ''
  try {
    const res = await fetch(`/api/emails/${messageId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    })
    if (res.ok) {
      feedbackMsg.value = `Email marked as ${action === 'approve' ? 'approved' : 'dismissed'}.`
      feedbackError.value = false
      selected.value = selected.value.filter(id => id !== messageId)
      emit('refresh')
    } else {
      feedbackMsg.value = 'Failed to record action. Please retry.'
      feedbackError.value = true
    }
  } catch (err) {
    feedbackMsg.value = 'Network error while updating review queue.'
    feedbackError.value = true
  } finally {
    isProcessing.value = false
    setTimeout(() => { if (!feedbackError.value) feedbackMsg.value = '' }, 3500)
  }
}

const submitCorrection = async (messageId) => {
  const newCat = correctionMap.value[messageId]
  if (!newCat) return
  isProcessing.value = true
  feedbackMsg.value = ''
  try {
    const res = await fetch(`/api/emails/${messageId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'change_category',
        new_category: newCat
      })
    })
    if (res.ok) {
      feedbackMsg.value = `Updated category to "${newCat}" and marked as approved.`
      feedbackError.value = false
      delete correctionMap.value[messageId]
      selected.value = selected.value.filter(id => id !== messageId)
      emit('refresh')
    } else {
      feedbackMsg.value = 'Failed to update category.'
      feedbackError.value = true
    }
  } catch (err) {
    feedbackMsg.value = 'Network error while submitting correction.'
    feedbackError.value = true
  } finally {
    isProcessing.value = false
    setTimeout(() => { if (!feedbackError.value) feedbackMsg.value = '' }, 3500)
  }
}

const bulkApprove = async () => {
  if (selected.value.length === 0) return
  isProcessing.value = true
  feedbackMsg.value = ''
  const total = selected.value.length
  try {
    const promises = selected.value.map(id =>
      fetch(`/api/emails/${id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve' })
      })
    )
    await Promise.all(promises)
    feedbackMsg.value = `Successfully approved all ${total} selected emails.`
    feedbackError.value = false
    selected.value = []
    emit('refresh')
  } catch (err) {
    feedbackMsg.value = 'Error during bulk approval.'
    feedbackError.value = true
  } finally {
    isProcessing.value = false
    setTimeout(() => { if (!feedbackError.value) feedbackMsg.value = '' }, 3500)
  }
}
</script>
