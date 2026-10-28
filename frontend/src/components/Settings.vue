<template>
  <div class="space-y-8 animate-fade pb-12 max-w-4xl mx-auto">
    
    <!-- Header -->
    <div class="bg-surface p-4 sm:p-5 rounded-xl border border-border shadow-xs">
      <h2 class="text-base sm:text-lg font-semibold text-ink font-serif tracking-tight">System & Automation Settings</h2>
      <p class="text-xs text-ink-muted mt-0.5">Tune classification thresholds, spam quarantine protocol, and workspace preferences.</p>
    </div>

    <!-- Alert / Message -->
    <div v-if="statusMsg" :class="['p-3.5 rounded-lg text-xs font-medium border flex items-center justify-between', statusError ? 'bg-status-dangerBg text-status-danger border-status-dangerBorder' : 'bg-status-successBg text-status-success border-status-successBorder']">
      <span>{{ statusMsg }}</span>
      <button @click="statusMsg = ''" class="hover:opacity-75 font-mono text-sm">&times;</button>
    </div>

    <!-- Demo Workspace Management Card (If Demo active) -->
    <div v-if="user?.is_demo" class="bg-amber-500/10 border border-amber-500/20 rounded-xl p-5 space-y-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <span class="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></span>
          <h3 class="text-sm font-semibold text-amber-800">Demo Workspace Active</h3>
        </div>
        <button
          @click="resetDemo"
          :disabled="isResettingDemo"
          class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-surface border border-amber-500/30 text-amber-900 hover:bg-surface/80 shadow-xs transition-all disabled:opacity-50"
        >
          {{ isResettingDemo ? 'Resetting...' : 'Reset Demo Data' }}
        </button>
      </div>
      <p class="text-xs text-ink-secondary leading-relaxed">
        You are currently exploring Email Automata in isolated demo mode. Actions and category corrections will not touch any real Google accounts. Use the reset button above to restore the initial 8 sample emails at any time.
      </p>
    </div>

    <!-- Connected Account Card -->
    <div class="bg-surface rounded-xl border border-border shadow-xs p-5 space-y-4">
      <div class="flex items-center justify-between pb-3 border-b border-border-subtle">
        <h3 class="text-sm font-semibold text-ink">Account & Authorization</h3>
        <span class="px-2 py-0.5 rounded text-[11px] font-mono bg-status-successBg text-status-success border border-status-successBorder">
          OAuth 2.0 Scoped
        </span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div class="p-3 rounded-lg bg-canvas-subtle border border-border-subtle space-y-1">
          <span class="text-ink-muted uppercase font-mono block text-[10px]">Connected Address</span>
          <span class="font-mono font-semibold text-ink break-all">{{ user?.email || 'Unknown' }}</span>
        </div>
        <div class="p-3 rounded-lg bg-canvas-subtle border border-border-subtle space-y-1">
          <span class="text-ink-muted uppercase font-mono block text-[10px]">Permission Scope</span>
          <span class="font-mono text-ink">gmail.modify (Labels & Inbox only)</span>
        </div>
      </div>

      <div class="pt-2 flex justify-between items-center text-xs text-ink-muted">
        <span>Permanent deletion is mathematically prevented by API scope limitations.</span>
        <button @click="$emit('logout')" class="text-status-danger hover:underline font-semibold">
          Disconnect Account
        </button>
      </div>
    </div>

    <!-- Main Settings Form -->
    <div class="bg-surface rounded-xl border border-border shadow-xs p-5 sm:p-6 space-y-6">
      
      <!-- 1. Confidence Threshold -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <label class="text-xs font-semibold uppercase tracking-wider text-ink block">Automation Confidence Threshold</label>
            <p class="text-xs text-ink-muted mt-0.5">Emails classified with a confidence score equal to or higher than this percentage are handled automatically.</p>
          </div>
          <span class="text-lg font-mono font-semibold text-brand px-3 py-1 rounded-lg bg-brand-subtle border border-brand/20">
            {{ Math.round(settings.confidence_threshold * 100) }}%
          </span>
        </div>

        <input
          type="range"
          v-model.number="settings.confidence_threshold"
          min="0.50"
          max="1.00"
          step="0.01"
          class="w-full h-2 bg-canvas-muted rounded-lg appearance-none cursor-pointer"
        />

        <div class="flex justify-between text-[11px] font-mono text-ink-muted">
          <span>50% (Aggressive)</span>
          <span class="text-brand font-medium">85% (Recommended Default)</span>
          <span>100% (Manual Triage)</span>
        </div>
      </div>

      <!-- 2. Spam Protocol -->
      <div class="space-y-3 pt-6 border-t border-border-subtle">
        <label class="text-xs font-semibold uppercase tracking-wider text-ink block">Spam Handling Protocol</label>
        <p class="text-xs text-ink-muted">Choose how identified spam and phishing threats are safely isolated.</p>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
          <!-- Quarantine -->
          <label
            :class="[
              'p-4 rounded-xl border cursor-pointer transition-all space-y-1 block',
              settings.spam_policy === 'quarantine'
                ? 'border-brand bg-brand-subtle/50 shadow-subtle'
                : 'border-border bg-canvas-subtle hover:border-brand/40'
            ]"
          >
            <input type="radio" v-model="settings.spam_policy" value="quarantine" class="sr-only" />
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-ink">Quarantine</span>
              <span v-if="settings.spam_policy === 'quarantine'" class="w-2 h-2 rounded-full bg-brand"></span>
            </div>
            <p class="text-[11px] text-ink-secondary leading-snug">
              Applies <code>AI-QUARANTINE</code> and archives from INBOX. Safely isolated and reversible.
            </p>
          </label>

          <!-- Label Only -->
          <label
            :class="[
              'p-4 rounded-xl border cursor-pointer transition-all space-y-1 block',
              settings.spam_policy === 'label'
                ? 'border-brand bg-brand-subtle/50 shadow-subtle'
                : 'border-border bg-canvas-subtle hover:border-brand/40'
            ]"
          >
            <input type="radio" v-model="settings.spam_policy" value="label" class="sr-only" />
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-ink">Label Only</span>
              <span v-if="settings.spam_policy === 'label'" class="w-2 h-2 rounded-full bg-brand"></span>
            </div>
            <p class="text-[11px] text-ink-secondary leading-snug">
              Adds <code>AI-SPAM</code> tag but keeps the email in INBOX for manual review.
            </p>
          </label>

          <!-- Hard Spam -->
          <label
            :class="[
              'p-4 rounded-xl border cursor-pointer transition-all space-y-1 block',
              settings.spam_policy === 'spam'
                ? 'border-status-danger bg-status-dangerBg/50 shadow-subtle'
                : 'border-border bg-canvas-subtle hover:border-status-danger/40'
            ]"
          >
            <input type="radio" v-model="settings.spam_policy" value="spam" class="sr-only" />
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-ink">Mark as Spam</span>
              <span v-if="settings.spam_policy === 'spam'" class="w-2 h-2 rounded-full bg-status-danger"></span>
            </div>
            <p class="text-[11px] text-ink-secondary leading-snug">
              Moves message directly to Gmail's native Spam folder.
            </p>
          </label>
        </div>
      </div>

      <!-- 3. Dry Run Toggle -->
      <div class="space-y-3 pt-6 border-t border-border-subtle">
        <div class="flex items-start justify-between gap-4">
          <div>
            <label class="text-xs font-semibold uppercase tracking-wider text-ink block">Dry-Run Simulation Mode</label>
            <p class="text-xs text-ink-muted mt-0.5">When enabled, emails are fully classified and logged to SQLite, but no actual Gmail labels or archive actions are performed.</p>
          </div>
          
          <button
            type="button"
            @click="settings.dry_run = !settings.dry_run"
            :class="[
              'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
              settings.dry_run ? 'bg-brand' : 'bg-canvas-muted'
            ]"
          >
            <span
              :class="[
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-surface shadow-subtle ring-0 transition duration-200 ease-in-out',
                settings.dry_run ? 'translate-x-5' : 'translate-x-0'
              ]"
            />
          </button>
        </div>
      </div>

      <!-- Submit Footer -->
      <div class="pt-6 border-t border-border-subtle flex items-center justify-between">
        <span class="text-xs text-ink-muted">Settings persist in SQLite user preferences.</span>
        
        <button
          @click="saveSettings"
          :disabled="isSaving"
          class="px-5 py-2 text-xs font-semibold rounded-lg bg-brand text-surface hover:bg-brand-hover shadow-subtle transition-all disabled:opacity-50 inline-flex items-center gap-2"
        >
          <svg v-if="isSaving" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isSaving ? 'Saving...' : 'Save Configuration' }}
        </button>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

defineProps({
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['logout', 'refresh'])

const settings = ref({
  confidence_threshold: 0.85,
  spam_policy: 'quarantine',
  dry_run: false
})

const isSaving = ref(false)
const isResettingDemo = ref(false)
const statusMsg = ref('')
const statusError = ref(false)

const loadSettings = async () => {
  try {
    const res = await fetch('/api/settings')
    if (res.ok) {
      const data = await res.json()
      settings.value = {
        confidence_threshold: parseFloat(data.confidence_threshold) || 0.85,
        spam_policy: data.spam_policy || 'quarantine',
        dry_run: Boolean(data.dry_run)
      }
    }
  } catch (err) {
    console.error(err)
  }
}

const saveSettings = async () => {
  isSaving.value = true
  statusMsg.value = ''
  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings.value)
    })
    if (res.ok) {
      statusMsg.value = 'Settings saved successfully.'
      statusError.value = false
    } else {
      const err = await res.json().catch(() => ({}))
      statusMsg.value = err.detail || 'Failed to save settings.'
      statusError.value = true
    }
  } catch (err) {
    statusMsg.value = 'Network error while saving settings.'
    statusError.value = true
  } finally {
    isSaving.value = false
    setTimeout(() => { if (!statusError.value) statusMsg.value = '' }, 3500)
  }
}

const resetDemo = async () => {
  if (!confirm('Reset demo workspace back to the initial 8 sample emails?')) return
  isResettingDemo.value = true
  statusMsg.value = ''
  try {
    const res = await fetch('/api/demo/reset', { method: 'POST' })
    if (res.ok) {
      statusMsg.value = 'Demo workspace successfully reset.'
      statusError.value = false
      emit('refresh')
    } else {
      statusMsg.value = 'Failed to reset demo workspace.'
      statusError.value = true
    }
  } catch (err) {
    statusMsg.value = 'Network error while resetting demo.'
    statusError.value = true
  } finally {
    isResettingDemo.value = false
    setTimeout(() => { if (!statusError.value) statusMsg.value = '' }, 3500)
  }
}

onMounted(() => {
  loadSettings()
})
</script>
