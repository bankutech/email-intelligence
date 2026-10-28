<template>
  <div
    v-if="email"
    role="dialog"
    aria-modal="true"
    aria-label="Email Reader"
    class="fixed inset-0 z-50 overflow-hidden flex justify-end bg-ink/30 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-2xl bg-surface h-full shadow-2xl flex flex-col border-l border-border animate-drawer">
      
      <!-- Drawer Header -->
      <div class="px-6 py-5 border-b border-border flex items-center justify-between bg-canvas-subtle/50">
        <div class="flex items-center gap-3">
          <span :class="['px-2.5 py-1 text-xs font-semibold rounded-md border uppercase tracking-wider', categoryBadgeClass(email.category)]">
            {{ email.category }}
          </span>
          <span v-if="email.priority" :class="['px-2 py-0.5 text-xs font-mono rounded border', priorityBadgeClass(email.priority)]">
            {{ email.priority }} priority
          </span>
          <span :class="['text-xs font-mono px-2 py-0.5 rounded border', confidenceClass(email.confidence)]">
            {{ Math.round((email.confidence || 0) * 100) }}% conf
          </span>
        </div>
        
        <button
          @click="$emit('close')"
          class="p-1.5 rounded-lg text-ink-muted hover:text-ink hover:bg-canvas-muted transition-colors"
          title="Close reader (Esc)"
          aria-label="Close email details"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Drawer Content -->
      <div class="flex-1 overflow-y-auto px-6 py-6 space-y-6">

        
        <!-- Subject & Meta -->
        <div>
          <h2 class="text-xl font-semibold text-ink leading-snug mb-3">
            {{ email.subject || '(no subject)' }}
          </h2>
          
          <div class="bg-canvas-subtle rounded-xl p-4 border border-border-subtle space-y-2 text-xs text-ink-secondary">
            <div class="flex items-start justify-between gap-4">
              <span class="text-ink-muted font-medium w-16 shrink-0">From</span>
              <span class="font-mono text-ink text-right break-all">{{ email.sender_email || email.sender || 'Unknown' }}</span>
            </div>
            <div class="flex items-start justify-between gap-4" v-if="email.email_timestamp || email.updated_at">
              <span class="text-ink-muted font-medium w-16 shrink-0">Date</span>
              <span class="font-mono text-ink text-right">{{ formatFullDate(email.email_timestamp || email.updated_at) }}</span>
            </div>
            <div class="flex items-start justify-between gap-4" v-if="email.message_id">
              <span class="text-ink-muted font-medium w-16 shrink-0">Message ID</span>
              <span class="font-mono text-ink-muted text-right text-[11px] truncate">{{ email.message_id }}</span>
            </div>
          </div>
        </div>

        <!-- AI Classification Card -->
        <div class="border border-border rounded-xl p-5 bg-surface space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-border-subtle">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full bg-brand"></div>
              <span class="text-xs font-semibold uppercase tracking-wider text-ink-secondary">AI Intelligence Analysis</span>
            </div>
            <span class="text-[11px] font-mono text-ink-muted bg-canvas-muted px-2 py-0.5 rounded">
              {{ email.model || 'gemini-2.5-flash' }}
            </span>
          </div>

          <!-- Confidence meter -->
          <div>
            <div class="flex justify-between text-xs mb-1.5">
              <span class="text-ink-secondary">Classification Confidence</span>
              <span class="font-mono font-medium text-ink">{{ Math.round((email.confidence || 0) * 100) }}%</span>
            </div>
            <div class="w-full h-1.5 bg-canvas-muted rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500" :style="{ width: `${Math.round((email.confidence || 0) * 100)}%`, backgroundColor: confidenceColor(email.confidence) }"></div>
            </div>
            <div class="flex justify-between text-[10px] text-ink-muted mt-1 font-mono">
              <span>0% (Review)</span>
              <span>Threshold: 85%</span>
              <span>100% (Auto)</span>
            </div>
          </div>

          <!-- AI Reasoning Quote -->
          <div v-if="email.reason" class="p-3.5 bg-canvas-subtle rounded-lg border-l-2 border-brand text-xs text-ink-secondary leading-relaxed">
            <span class="font-semibold text-ink block mb-1">Reasoning</span>
            "{{ email.reason }}"
          </div>
        </div>

        <!-- Deterministic Security Rules Audit -->
        <div class="border border-border rounded-xl p-5 bg-surface space-y-3">
          <div class="flex items-center justify-between pb-3 border-b border-border-subtle">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-ink-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
              </svg>
              <span class="text-xs font-semibold uppercase tracking-wider text-ink-secondary">Pre-LLM Security Rules</span>
            </div>
            <span :class="['text-xs font-medium px-2 py-0.5 rounded border', hasSecurityFlags ? 'bg-status-dangerBg text-status-danger border-status-dangerBorder' : 'bg-status-successBg text-status-success border-status-successBorder']">
              {{ hasSecurityFlags ? 'Flags Triggered' : 'Clean & Verified' }}
            </span>
          </div>

          <div v-if="hasSecurityFlags" class="space-y-2">
            <div v-for="flag in normalizedFlags" :key="flag" class="flex items-center gap-2 text-xs p-2.5 rounded-lg bg-status-dangerBg text-status-danger border border-status-dangerBorder">
              <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
              </svg>
              <span class="font-mono">{{ formatFlag(flag) }}</span>
            </div>
          </div>
          <div v-else class="text-xs text-ink-muted flex items-center gap-2 py-1">
            <svg class="w-4 h-4 text-status-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <span>DMARC/SPF passed, no link domain spoofing, no hazardous attachments.</span>
          </div>
        </div>

        <!-- Executed Actions Timeline -->
        <div class="border border-border rounded-xl p-5 bg-surface space-y-3">
          <div class="flex items-center justify-between pb-3 border-b border-border-subtle">
            <span class="text-xs font-semibold uppercase tracking-wider text-ink-secondary">Executed Automation</span>
            <span class="text-xs font-mono text-ink-muted">Safety: Labels Only</span>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs p-2.5 rounded-lg bg-canvas-subtle border border-border-subtle">
              <span class="text-ink-secondary">Action Applied</span>
              <span class="font-mono font-medium text-ink bg-surface px-2 py-1 rounded border border-border">
                {{ email.actions || 'Kept in Inbox (No label modification)' }}
              </span>
            </div>
            <div class="flex items-center justify-between text-xs p-2.5 rounded-lg bg-canvas-subtle border border-border-subtle">
              <span class="text-ink-secondary">Processing Status</span>
              <span :class="['font-mono font-medium capitalize px-2 py-0.5 rounded', email.status === 'review' ? 'text-status-warning bg-status-warningBg' : 'text-status-success bg-status-successBg']">
                {{ email.status || 'done' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Manual Category Correction Form (Interactive) -->
        <div class="border border-border rounded-xl p-5 bg-canvas-subtle space-y-3">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink block">Correct Classification</span>
          <p class="text-xs text-ink-secondary">If the AI miscategorized this email, select the correct category below to update the system.</p>
          
          <div class="flex items-center gap-3 pt-2">
            <select v-model="selectedCategory" class="flex-1 text-xs px-3 py-2 bg-surface border border-border rounded-lg text-ink font-medium focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand">
              <option value="" disabled>Select corrected category...</option>
              <option value="urgent">Urgent</option>
              <option value="important">Important</option>
              <option value="work">Work</option>
              <option value="academic">Academic</option>
              <option value="meeting">Meeting</option>
              <option value="promotional">Promotional</option>
              <option value="normal">Normal</option>
              <option value="spam">Spam</option>
            </select>
            <button @click="applyCorrection" :disabled="!selectedCategory || isSaving" class="px-4 py-2 text-xs font-semibold text-surface bg-brand hover:bg-brand-hover disabled:opacity-40 rounded-lg transition-colors shrink-0">
              {{ isSaving ? 'Saving...' : 'Apply Correction' }}
            </button>
          </div>
          <p v-if="saveMessage" class="text-xs font-medium text-status-success pt-1">{{ saveMessage }}</p>
        </div>

      </div>

      <!-- Drawer Footer -->
      <div class="px-6 py-4 border-t border-border bg-canvas-subtle/50 flex justify-end">
        <button @click="$emit('close')" class="px-4 py-2 text-xs font-semibold text-ink bg-surface border border-border hover:bg-canvas-muted rounded-lg transition-colors">
          Close Reader
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  email: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'updated'])

const selectedCategory = ref('')
const isSaving = ref(false)
const saveMessage = ref('')

const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

const normalizedFlags = computed(() => {
  if (!props.email?.rule_flags) return []
  if (Array.isArray(props.email.rule_flags)) return props.email.rule_flags
  try {
    return JSON.parse(props.email.rule_flags)
  } catch {
    return []
  }
})

const hasSecurityFlags = computed(() => normalizedFlags.value.length > 0)

const formatFlag = (flag) => {
  const map = {
    link_text_mismatch: 'Suspicious Link Target Mismatch',
    suspicious_sender: 'Unverified Sender Domain / Display Spoof',
    risky_attachment: 'Executable or Dangerous Attachment',
    dmarc_failed: 'DMARC Authentication Failed'
  }
  return map[flag] || flag.replace(/_/g, ' ')
}

const formatFullDate = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short'
  })
}

const confidenceClass = (conf) => {
  const val = conf || 0
  if (val >= 0.85) return 'bg-status-successBg text-status-success border-status-successBorder'
  if (val >= 0.60) return 'bg-status-warningBg text-status-warning border-status-warningBorder'
  return 'bg-status-dangerBg text-status-danger border-status-dangerBorder'
}

const confidenceColor = (conf) => {
  const val = conf || 0
  if (val >= 0.85) return '#059669'
  if (val >= 0.60) return '#d97706'
  return '#e11d48'
}

const priorityBadgeClass = (prio) => {
  const p = (prio || '').toLowerCase()
  if (p === 'high') return 'bg-status-dangerBg text-status-danger border-status-dangerBorder'
  if (p === 'medium') return 'bg-brand-subtle text-brand border-border'
  return 'bg-canvas-muted text-ink-muted border-border'
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

const applyCorrection = async () => {
  if (!selectedCategory.value || !props.email) return
  isSaving.value = true
  saveMessage.value = ''
  try {
    const res = await fetch(`/api/emails/${props.email.message_id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'change_category',
        new_category: selectedCategory.value
      })
    })
    if (res.ok) {
      saveMessage.value = `Successfully updated category to ${selectedCategory.value}.`
      props.email.category = selectedCategory.value
      props.email.confidence = 1.0
      props.email.status = 'done'
      emit('updated', props.email)
      setTimeout(() => { saveMessage.value = '' }, 3000)
    }
  } catch (err) {
    console.error(err)
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
@keyframes drawerSlide {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
.animate-drawer {
  animation: drawerSlide 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
