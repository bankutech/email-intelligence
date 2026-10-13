<template>
  <div class="flex flex-col items-center justify-center min-h-[85vh] px-4 md:px-[150px] relative">
    
    <div class="max-w-4xl w-full flex flex-col items-center text-center gap-8 relative z-10">
      
      <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-nyalablue/10 text-nyalablue font-medium text-sm">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-nyalablue opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-nyalablue"></span>
        </span>
        Intelligent Email Processing
      </div>

      <h1 class="font-display font-bold text-5xl md:text-7xl text-nyalaslate leading-tight tracking-tight">
        Your inbox, <span class="text-nyalablue">automated</span>
      </h1>
      
      <p class="font-sans text-xl text-nyalaslate/70 max-w-2xl leading-relaxed">
        Connect your Gmail account to let our AI classify, label, and clean up your emails automatically. Save hours every week.
      </p>

      <div class="pt-8 w-full max-w-sm">
        <a href="/auth/google" class="group flex items-center justify-center gap-4 w-full py-4 px-8 rounded-full bg-nyalablue text-nyalawhite font-medium text-lg hover:bg-nyalablue/90 hover:-translate-y-1 transition-all shadow-lg shadow-nyalablue/20">
          <svg class="w-6 h-6" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Connect with Google
          <svg class="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
          </svg>
        </a>
      </div>

    </div>
  </div>
</template>

<script setup>
</script>
