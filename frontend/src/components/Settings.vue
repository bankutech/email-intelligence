<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <h2 class="text-xl font-semibold text-textMain">Configuration</h2>
    <div class="panel p-6">
      <div v-if="loading" class="animate-pulse space-y-4">
        <div class="h-10 bg-surfaceElevated rounded"></div>
        <div class="h-10 bg-surfaceElevated rounded"></div>
      </div>
      <div v-else class="space-y-6">
        <div>
          <label for="conf" class="block text-sm font-medium text-textMain mb-1">Confidence Threshold ({{ (settings.confidence_threshold * 100).toFixed(0) }}%)</label>
          <input id="conf" type="range" v-model.number="settings.confidence_threshold" min="0.5" max="1.0" step="0.05" class="w-full accent-primary">
          <p class="text-xs text-textMuted mt-1">Emails below this confidence will be sent to the review queue.</p>
        </div>
        
        <div>
           <label for="spam" class="block text-sm font-medium text-textMain mb-1">Spam Policy</label>
           <select id="spam" v-model="settings.spam_policy" class="w-full bg-surface border border-border rounded-md px-3 py-2 text-sm text-textMain focus:outline-none focus:ring-1 focus:ring-primary">
             <option value="label">Label only</option>
             <option value="quarantine">Quarantine (Review Queue)</option>
             <option value="spam">Mark as Spam</option>
           </select>
        </div>
        
        <div class="flex items-center gap-2">
           <input id="dry" type="checkbox" v-model="settings.dry_run" class="rounded border-border bg-background focus:ring-primary">
           <label for="dry" class="text-sm font-medium text-textMain">Enable Dry-Run Mode</label>
        </div>

        <button @click="save" :disabled="saving" class="btn btn-primary text-sm w-full sm:w-auto">
          {{ saving ? 'Saving...' : 'Save Configuration' }}
        </button>
        <div v-if="saveMsg" :class="['mt-4 p-3 rounded-md text-sm', saveError ? 'bg-danger/10 text-danger border border-danger/20' : 'bg-success/10 text-success border border-success/20']" role="status">
          {{ saveMsg }}
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'

const settings = ref({
  confidence_threshold: 0.85,
  spam_policy: 'quarantine',
  dry_run: false
})
const loading = ref(true)
const saving = ref(false)
const saveMsg = ref('')
const saveError = ref(false)

const load = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/settings')
    if (res.ok) {
      settings.value = await res.json()
      // Ensure numeric type after JSON parse
      settings.value.confidence_threshold = parseFloat(settings.value.confidence_threshold) || 0.85
    }
  } finally {
    loading.value = false
  }
}

const save = async () => {
  saving.value = true
  saveMsg.value = ''
  try {
    const payload = {
      ...settings.value,
      confidence_threshold: parseFloat(settings.value.confidence_threshold)
    }
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      saveMsg.value = 'Configuration saved successfully.'
      saveError.value = false
    } else {
      const err = await res.json().catch(() => ({}))
      saveMsg.value = err.detail || 'Failed to save settings.'
      saveError.value = true
    }
  } catch (e) {
    saveMsg.value = 'Network error while saving.'
    saveError.value = true
  } finally {
    saving.value = false
  }
}

onMounted(() => load())
</script>
