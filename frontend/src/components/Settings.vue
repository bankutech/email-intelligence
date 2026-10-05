<template>
  <div class="max-w-4xl mx-auto space-y-12 pb-12 animate-slide-up">
    <div>
      <h2 class="font-display font-bold text-3xl text-nyalaslate mb-2">Settings</h2>
      <p class="text-nyalaslate/60 text-lg">Configure your email intelligence preferences</p>
    </div>

    <div v-if="loading" class="flex flex-col gap-8 animate-pulse">
      <div class="h-32 bg-nyalaslate/5 rounded-2xl" v-for="i in 3" :key="i"></div>
    </div>
    
    <div v-else class="space-y-8">
      
      <div class="bg-nyalawhite border border-nyalaslate/10 shadow-sm rounded-3xl p-8 space-y-10">
        
        <div>
          <label class="flex justify-between text-sm font-bold uppercase tracking-wider text-nyalaslate/70 mb-4">
            <span>Confidence Threshold</span>
            <span class="text-nyalablue">{{ Math.round(settings.confidence_threshold * 100) }}%</span>
          </label>
          <input type="range" v-model.number="settings.confidence_threshold" min="0.5" max="1.0" step="0.01" class="w-full h-2 bg-nyalaslate/10 rounded-full appearance-none cursor-pointer outline-none slider-nyalablue">
          <p class="text-sm text-nyalaslate/60 mt-4 leading-relaxed">
            Required confidence before automation takes effect. Items below this threshold are placed in the Review Queue.
          </p>
        </div>
        
        <div class="border-t border-nyalaslate/10 pt-8">
          <label class="block text-sm font-bold uppercase tracking-wider text-nyalaslate/70 mb-4">Spam Protocol</label>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <label class="relative flex cursor-pointer group">
              <input type="radio" v-model="settings.spam_policy" value="label" class="peer sr-only" name="spam_policy">
              <div class="w-full p-4 rounded-xl border border-nyalaslate/10 text-center peer-checked:bg-nyalablue peer-checked:text-nyalawhite peer-checked:border-nyalablue transition-all hover:border-nyalablue/50">
                <div class="font-bold text-sm uppercase tracking-wider">Label</div>
              </div>
            </label>
            <label class="relative flex cursor-pointer group">
              <input type="radio" v-model="settings.spam_policy" value="quarantine" class="peer sr-only" name="spam_policy">
              <div class="w-full p-4 rounded-xl border border-nyalaslate/10 text-center peer-checked:bg-nyalablue peer-checked:text-nyalawhite peer-checked:border-nyalablue transition-all hover:border-nyalablue/50">
                <div class="font-bold text-sm uppercase tracking-wider">Quarantine</div>
              </div>
            </label>
            <label class="relative flex cursor-pointer group">
              <input type="radio" v-model="settings.spam_policy" value="spam" class="peer sr-only" name="spam_policy">
              <div class="w-full p-4 rounded-xl border border-nyalaslate/10 text-center peer-checked:bg-danger peer-checked:text-nyalawhite peer-checked:border-danger transition-all hover:border-danger/50">
                <div class="font-bold text-sm uppercase tracking-wider">Hard Spam</div>
              </div>
            </label>
          </div>
        </div>
        
        <div class="border-t border-nyalaslate/10 pt-8">
          <label class="flex items-start gap-4 cursor-pointer group">
            <div class="relative flex items-center mt-1">
              <input type="checkbox" v-model="settings.dry_run" class="peer sr-only">
              <div class="w-6 h-6 rounded border-2 border-nyalaslate/20 bg-nyalawhite peer-checked:bg-nyalablue peer-checked:border-nyalablue transition-colors"></div>
              <svg class="absolute inset-0 w-6 h-6 text-nyalawhite pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <div class="text-sm font-bold uppercase tracking-wider text-nyalaslate/70">Dry Run Mode</div>
              <p class="text-sm text-nyalaslate/60 mt-2 leading-relaxed">
                Log actions without modifying Gmail state. Use this to safely test new rules.
              </p>
            </div>
          </label>
        </div>
      </div>
      
      <div class="flex items-center gap-6">
        <button @click="save" :disabled="saving" class="px-8 py-4 rounded-full bg-nyalablue text-nyalawhite font-medium shadow-md shadow-nyalablue/20 hover:bg-nyalablue/90 hover:-translate-y-0.5 transition-all disabled:opacity-50 inline-flex items-center gap-3">
          <svg v-if="saving" class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
          Save Configuration
        </button>

        <div v-if="saveMsg" :class="['px-4 py-2 font-medium text-sm rounded-lg', saveError ? 'bg-danger/10 text-danger' : 'bg-success/10 text-success']" role="status">
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
      saveMsg.value = 'Settings saved.'
      saveError.value = false
    } else {
      const err = await res.json().catch(() => ({}))
      saveMsg.value = err.detail || 'Save failed.'
      saveError.value = true
    }
  } catch (e) {
    saveMsg.value = 'Network error.'
    saveError.value = true
  } finally {
    saving.value = false
    setTimeout(() => { if (!saveError.value) saveMsg.value = '' }, 3000)
  }
}

onMounted(() => load())
</script>

<style scoped>
.slider-nyalablue::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: #0C49A2;
  cursor: pointer;
  border-radius: 50%;
  border: 4px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.slider-nyalablue::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #0C49A2;
  cursor: pointer;
  border-radius: 50%;
  border: 4px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
</style>
