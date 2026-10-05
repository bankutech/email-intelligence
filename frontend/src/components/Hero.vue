<template>
  <div class="flex flex-col items-center justify-center min-h-[70vh] text-center px-4 w-full">
    <div class="max-w-3xl space-y-8 fade-in-up">
      <h1 class="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-textMain leading-tight">
        Your inbox.<br/>Under control.
      </h1>
      <p class="text-lg text-textMuted max-w-xl mx-auto">
        Military-grade deterministic inbox automation. AI classifies incoming messages. Python enforces safe, idempotent rules.
      </p>
      <div class="flex justify-center">
        <a href="/auth/google" class="btn btn-primary text-base px-6 py-3 shadow-lg flex items-center gap-2" role="button">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"></path></svg>
          Continue with Google
        </a>
      </div>
    </div>
  </div>
</template>
<style scoped>
.fade-in-up {
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  .fade-in-up { animation: none; opacity: 1; transform: none; }
}
</style>
