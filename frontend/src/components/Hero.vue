<template>
  <div class="min-h-[88vh] flex flex-col justify-center px-4 sm:px-8 py-12 max-w-5xl mx-auto animate-fade">
    
    <!-- Hero Header -->
    <div class="space-y-6 text-center max-w-3xl mx-auto">
      
      <!-- Trust Badge -->
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium bg-brand-subtle text-brand border border-brand/20">
        <span class="w-2 h-2 rounded-full bg-brand animate-pulse"></span>
        Deterministic Safety &middot; Gemini 2.5 Flash Intelligence
      </div>

      <!-- Main Headline -->
      <h1 class="text-4xl sm:text-6xl font-semibold tracking-tight text-ink font-serif leading-[1.12]">
        Intelligent email automation with <span class="italic text-brand font-serif">provable safety boundaries</span>.
      </h1>

      <!-- Subtitle -->
      <p class="text-sm sm:text-base text-ink-secondary max-w-2xl mx-auto leading-relaxed">
        Watch your Gmail inbox, classify incoming messages with Gemini 2.5 Flash, and apply reversible labels with strict confidence gates. No permanent deletion, zero data leakage.
      </p>

      <!-- Action Buttons -->
      <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto">
        <a
          href="/auth/google"
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3 rounded-xl bg-ink text-surface hover:bg-ink/90 font-medium text-xs shadow-panel transition-all"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Connect with Google
        </a>

        <a
          href="/auth/demo"
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-surface border border-border text-ink hover:bg-canvas-subtle font-medium text-xs shadow-subtle transition-all"
        >
          <span class="w-2 h-2 rounded-full bg-status-success"></span>
          Explore Demo Workspace
        </a>
      </div>

      <div class="text-[11px] text-ink-muted">
        <span>No credentials required for demo. Real Gmail connections use restricted <code>gmail.modify</code> scopes.</span>
      </div>

    </div>

    <!-- 3 Pillars Feature Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16">
      
      <div class="bg-surface rounded-2xl p-6 border border-border shadow-subtle space-y-2.5">
        <div class="w-8 h-8 rounded-lg bg-canvas-muted flex items-center justify-center text-ink shrink-0 font-mono text-xs font-semibold">
          01
        </div>
        <h3 class="text-sm font-semibold text-ink">Deterministic Security Engine</h3>
        <p class="text-xs text-ink-secondary leading-relaxed">
          Pre-LLM checks inspect SPF/DMARC headers, link domain spoofing, and dangerous attachment formats before anything touches an AI model.
        </p>
      </div>

      <div class="bg-surface rounded-2xl p-6 border border-border shadow-subtle space-y-2.5">
        <div class="w-8 h-8 rounded-lg bg-brand-subtle flex items-center justify-center text-brand shrink-0 font-mono text-xs font-semibold">
          02
        </div>
        <h3 class="text-sm font-semibold text-ink">Strict Structured Output</h3>
        <p class="text-xs text-ink-secondary leading-relaxed">
          Gemini 2.5 Flash evaluates contextual urgency with Pydantic JSON schemas. Prompt injection is structurally incapable of triggering unauthorized actions.
        </p>
      </div>

      <div class="bg-surface rounded-2xl p-6 border border-border shadow-subtle space-y-2.5">
        <div class="w-8 h-8 rounded-lg bg-canvas-muted flex items-center justify-center text-ink shrink-0 font-mono text-xs font-semibold">
          03
        </div>
        <h3 class="text-sm font-semibold text-ink">Mathematical Non-Destruction</h3>
        <p class="text-xs text-ink-secondary leading-relaxed">
          All actions are reversible Gmail labels (`AI-URGENT`, `AI-WORK`, `AI-QUARANTINE`). Email bodies are never saved to database storage.
        </p>
      </div>

    </div>

  </div>
</template>

<script setup>
</script>
