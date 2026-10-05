<template>
  <div class="max-w-3xl mx-auto space-y-8 pb-12">
    <h2 class="font-serif text-4xl text-ink border-b-2 border-ink pb-4">Configuration</h2>

    <div v-if="loading" class="animate-pulse space-y-6">
      <div class="h-20 bg-ink/5 border-2 border-ink/20" v-for="i in 3" :key="i"></div>
    </div>
    
    <div v-else class="space-y-8 relative">
      <!-- Decorative wire/cable -->
      <div class="absolute left-[-40px] top-4 bottom-0 w-2 border-l-4 border-ink border-double opacity-20 hidden md:block"></div>

      <div class="bg-cream border-2 border-ink shadow-[8px_8px_0_#15120E] p-8 relative">
        <!-- Stamp label -->
        <div class="absolute -top-3 -right-2 font-mono text-[10px] font-bold uppercase tracking-widest bg-ink text-cream px-2 py-1 rotate-[3deg]">
          AI ENGINE
        </div>

        <div class="space-y-8">
          <div>
            <label class="flex justify-between text-sm font-mono font-bold uppercase tracking-widest text-ink mb-4">
              <span>Confidence Threshold</span>
              <span class="text-vermilion">{{ Math.round(settings.confidence_threshold * 100) }}%</span>
            </label>
            <input type="range" v-model.number="settings.confidence_threshold" min="0.5" max="1.0" step="0.01" class="interactive w-full appearance-none bg-ink/10 h-2 outline-none slider-thumb-ink border-2 border-ink">
            <p class="text-xs font-mono text-ink/60 mt-4 leading-relaxed">
              Required confidence before automation takes effect. Items below this threshold are placed in the Review Queue.
            </p>
          </div>
          
          <div class="border-t-2 border-dashed border-ink/30 pt-6">
            <label class="block text-sm font-mono font-bold uppercase tracking-widest text-ink mb-4">Spam Protocol</label>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <label class="interactive relative flex cursor-pointer group">
                <input type="radio" v-model="settings.spam_policy" value="label" class="peer sr-only" name="spam_policy">
                <div class="w-full p-4 border-2 border-ink text-center peer-checked:bg-ink peer-checked:text-cream peer-checked:shadow-[4px_4px_0_#FF4B1F] group-hover:-translate-y-1 transition-all">
                  <div class="font-bold font-mono text-xs uppercase tracking-widest">Label</div>
                </div>
              </label>
              <label class="interactive relative flex cursor-pointer group">
                <input type="radio" v-model="settings.spam_policy" value="quarantine" class="peer sr-only" name="spam_policy">
                <div class="w-full p-4 border-2 border-ink text-center peer-checked:bg-ink peer-checked:text-cream peer-checked:shadow-[4px_4px_0_#FF4B1F] group-hover:-translate-y-1 transition-all">
                  <div class="font-bold font-mono text-xs uppercase tracking-widest">Quarantine</div>
                </div>
              </label>
              <label class="interactive relative flex cursor-pointer group">
                <input type="radio" v-model="settings.spam_policy" value="spam" class="peer sr-only" name="spam_policy">
                <div class="w-full p-4 border-2 border-ink text-center peer-checked:bg-ink peer-checked:text-cream peer-checked:shadow-[4px_4px_0_#FF4B1F] group-hover:-translate-y-1 transition-all">
                  <div class="font-bold font-mono text-xs uppercase tracking-widest text-vermilion peer-checked:text-vermilion">Hard Spam</div>
                </div>
              </label>
            </div>
          </div>
          
          <div class="border-t-2 border-dashed border-ink/30 pt-6">
            <label class="interactive flex items-start gap-4 cursor-pointer group">
              <div class="relative flex items-center mt-1">
                <input type="checkbox" v-model="settings.dry_run" class="peer sr-only">
                <div class="w-6 h-6 border-2 border-ink bg-cream peer-checked:bg-vermilion peer-checked:border-vermilion transition-colors shadow-[2px_2px_0_#15120E] group-hover:-translate-y-0.5"></div>
                <svg class="absolute inset-0 w-6 h-6 text-cream pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <div class="text-sm font-mono font-bold uppercase tracking-widest text-ink">Dry Run Mode</div>
                <p class="text-xs font-mono text-ink/60 mt-2 leading-relaxed">
                  Log actions without modifying Gmail state. Use this to safely test new rules.
                </p>
              </div>
            </label>
          </div>
        </div>
      </div>
      
      <div class="flex items-center gap-6">
        <button @click="save" :disabled="saving" class="ticket-btn interactive px-8 py-4 font-mono font-bold text-sm uppercase tracking-widest bg-ink text-cream inline-flex items-center gap-3">
          <svg v-if="saving" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
          Save Configuration
        </button>

        <!-- Feedback Banner -->
        <div v-if="saveMsg" :class="['px-4 py-2 font-mono text-xs uppercase tracking-widest font-bold border-2', saveError ? 'bg-vermilion/10 text-vermilion border-vermilion shadow-[2px_2px_0_#FF4B1F]' : 'bg-ink/10 text-ink border-ink shadow-[2px_2px_0_#15120E]']" role="status">
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
.slider-thumb-ink::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 24px;
  background: #15120E;
  cursor: pointer;
  border: 2px solid #15120E;
}
.slider-thumb-ink::-moz-range-thumb {
  width: 16px;
  height: 24px;
  background: #15120E;
  cursor: pointer;
  border: 2px solid #15120E;
  border-radius: 0;
}

.ticket-btn {
  border: 2px solid #15120E;
  box-shadow: 6px 6px 0 #15120E;
  transition: all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.ticket-btn:hover:not(:disabled) {
  transform: translate(3px, 3px);
  box-shadow: 3px 3px 0 #15120E;
}
.ticket-btn:active:not(:disabled) {
  transform: translate(6px, 6px);
  box-shadow: 0 0 0 #15120E;
}
.ticket-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
