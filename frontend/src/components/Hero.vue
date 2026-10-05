<template>
  <div class="w-full bg-cream text-ink font-dispatchSans selection:bg-vermilion selection:text-cream relative overflow-hidden" ref="container">
    
    <svg class="grain-overlay">
      <filter id="noise">
        <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" stitchTiles="stitch" />
      </filter>
      <rect width="100%" height="100%" filter="url(#noise)" />
    </svg>

    <!-- Custom Cursor -->
    <div ref="cursor" class="fixed top-0 left-0 z-[100] pointer-events-none flex items-center justify-center -translate-x-1/2 -translate-y-1/2">
      <div v-if="isHovering" class="w-8 h-8 rounded-full border-2 border-vermilion bg-vermilion/20 flex items-center justify-center rotate-12 transition-transform duration-200">
        <span class="font-mono text-[8px] font-bold text-vermilion tracking-tighter">CLICK</span>
      </div>
      <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#15120E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="rotate-[-15deg] origin-bottom-right transition-transform duration-200">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
        <polyline points="22,6 12,13 2,6"></polyline>
      </svg>
    </div>

    <!-- Nav -->
    <nav class="absolute top-0 w-full p-4 md:p-8 flex justify-between items-center z-40 text-ink">
      <div class="font-mono text-sm tracking-widest uppercase flex items-center gap-2">
        <div class="w-2 h-2 bg-vermilion rounded-full animate-pulse"></div>
        AI Email Intelligence
      </div>
      <a href="/auth/google" class="ticket-btn bg-cream text-ink px-4 py-2 font-mono text-xs uppercase tracking-widest inline-block" @mouseenter="isHovering = true" @mouseleave="isHovering = false">
        Connect Gmail
      </a>
    </nav>

    <!-- Hero Section -->
    <section class="min-h-screen pt-32 md:pt-0 flex flex-col md:flex-row items-stretch border-b-2 border-ink relative z-10">
      <!-- Left Content -->
      <div class="w-full md:w-1/2 p-6 md:p-16 flex flex-col justify-center relative">
        <div class="font-mono text-xs tracking-widest uppercase mb-8 border-2 border-ink inline-block px-2 py-1 w-max">
          NO. 0001 — INCOMING / OUTGOING
        </div>
        
        <h1 class="font-serif text-[4.5rem] md:text-[clamp(5rem,8vw,11rem)] leading-[0.85] tracking-tight text-ink relative z-10 mb-8">
          <span class="inline-flex"><span v-for="(char, i) in 'Your inbox,'.split('')" :key="i" class="inline-block" :style="{ transform: `translateY(${(Math.random() - 0.5) * 6}px) rotate(${(Math.random() - 0.5) * 4}deg)` }">{{ char === ' ' ? '\u00A0' : char }}</span></span><br/>
          <span class="italic text-vermilion relative inline-block">
            <span class="inline-flex"><span v-for="(char, i) in 'finally'.split('')" :key="i" class="inline-block" :style="{ transform: `translateY(${(Math.random() - 0.5) * 6}px) rotate(${(Math.random() - 0.5) * 4}deg)` }">{{ char }}</span></span>
            <svg class="absolute -bottom-2 md:-bottom-4 left-0 w-full h-8 overflow-visible" viewBox="0 0 200 20" preserveAspectRatio="none">
              <path class="scribble-path" d="M 5,10 Q 50,20 100,5 T 195,15" fill="none" stroke="#FF4B1F" stroke-width="4" stroke-linecap="round" stroke-dasharray="250" stroke-dashoffset="250" />
            </svg>
          </span><br/>
          <span class="inline-flex"><span v-for="(char, i) in 'sorted.'.split('')" :key="i" class="inline-block" :style="{ transform: `translateY(${(Math.random() - 0.5) * 6}px) rotate(${(Math.random() - 0.5) * 4}deg)` }">{{ char === ' ' ? '\u00A0' : char }}</span></span>
        </h1>

        <div class="max-w-md text-lg md:text-xl font-medium text-ink/80 leading-relaxed mb-10 relative">
          <span class="absolute -left-12 top-2 font-hand text-2xl text-vermilion rotate-[-15deg] hidden md:block">Read this! &rarr;</span>
          AI reads every email and decides what it is. Plain Python decides what happens next. Same email twice? Nothing breaks.
        </div>

        <div>
          <a href="/auth/google" class="ticket-btn-red inline-flex px-8 py-4 font-mono text-sm uppercase tracking-widest items-center gap-4" @mouseenter="isHovering = true" @mouseleave="isHovering = false">
            Open the Mailroom
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </a>
        </div>
        
        <div class="postmark absolute top-24 right-8 w-32 h-32 border-2 border-ink rounded-full items-center justify-center opacity-20 pointer-events-none hidden md:flex">
          <div class="text-center font-mono text-[10px] uppercase tracking-widest leading-none">
            Sorted<br/>Filed<br/>Done
          </div>
        </div>
      </div>
      
      <!-- Right Animation Area -->
      <div class="w-full md:w-1/2 flex-1 relative hidden md:block border-l-2 border-ink">
        <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-20 pointer-events-none flex flex-col items-center">
          <div class="w-16 h-32 border-4 border-ink bg-cream relative shadow-[8px_8px_0_#15120E]">
            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full border-4 border-airmail bg-airmail/10 backdrop-blur-sm"></div>
            <div class="absolute -top-6 -left-20 w-16 text-right font-hand text-xl text-ink -rotate-12 tracking-tight">AI Gate</div>
            <svg class="absolute -top-4 -left-6 w-8 h-8 text-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </div>
        </div>

        <div v-for="item in envelopes" :key="item.id" :class="`envelope env-${item.id} absolute top-1/2 left-0 z-10 -translate-y-1/2`">
          <div class="w-48 h-32 bg-cream border-2 border-ink shadow-md relative overflow-hidden flex flex-col justify-between p-1">
            <div class="airmail-edge h-2 w-full"></div>
            <div class="stamp-overlay absolute inset-0 flex items-center justify-center bg-cream/80 backdrop-blur-[1px] opacity-0 scale-150">
              <div :class="`border-4 px-2 py-1 rotate-[-10deg] font-mono font-bold tracking-widest text-lg ${item.label === 'SPAM' ? 'border-vermilion text-vermilion' : 'border-ink text-ink'}`">
                {{ item.label }}
              </div>
            </div>
            <div class="airmail-edge h-2 w-full"></div>
          </div>
        </div>
        
        <div class="absolute bottom-4 right-4 font-mono text-xs uppercase tracking-widest text-ink/50 text-right">
          Mailroom Ticker <br/>
          [ ACTIVE ]
        </div>
      </div>
    </section>

    <!-- Marquee Section -->
    <div class="border-b-2 border-ink bg-vermilion text-cream overflow-hidden py-3 flex relative whitespace-nowrap">
      <div class="marquee-content flex font-mono text-sm uppercase tracking-widest font-medium">
        <div v-for="i in 6" :key="i" class="flex items-center">
          <span class="mx-8">Invoice #4821 &rarr; <span class="border border-cream px-1">RECEIPT</span></span>
          <span class="mx-8">Project Update &rarr; <span class="border border-cream px-1">URGENT</span></span>
          <span class="mx-8">Weekly Digest &rarr; <span class="border border-cream px-1">NEWSLETTER</span></span>
        </div>
      </div>
    </div>

    <!-- Details Section -->
    <section class="flex flex-col md:flex-row min-h-[80vh] relative z-10">
      <!-- Left: How it works -->
      <div class="w-full md:w-1/3 border-r-2 border-ink bg-cream p-8 md:p-12 flex justify-center items-start pt-24">
        <div class="receipt-strip torn-bottom w-full max-w-sm bg-cream p-6 shadow-sm relative">
          <h3 class="font-mono text-sm font-bold tracking-widest border-b-2 border-ink pb-4 mb-6 uppercase">Operating Procedure</h3>
          <ol class="font-mono text-sm space-y-6">
            <li class="flex gap-4">
              <span class="text-vermilion">01</span>
              <span class="leading-relaxed">AI reads the incoming mail. No templates, true understanding.</span>
            </li>
            <li class="flex gap-4">
              <span class="text-vermilion">02</span>
              <span class="leading-relaxed">Python evaluates your deterministic rules.</span>
            </li>
            <li class="flex gap-4">
              <span class="text-vermilion">03</span>
              <span class="leading-relaxed">Gmail is updated. Inbox zero achieved.</span>
            </li>
          </ol>
          <div class="mt-8 pt-4 border-t-2 border-dashed border-ink text-center text-xs opacity-50">END OF TAPE</div>
        </div>
      </div>

      <!-- Right: Typewriter Safe Rules -->
      <div class="w-full md:w-2/3 p-8 md:p-24 flex flex-col justify-center relative overflow-hidden bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwYXRoIGQ9Ik0wIDIwaDQwTTIwIDB2NDAiIHN0cm9rZT0iIzE1MTIwRSIgc3Ryb2tlLW9wYWNpdHk9IjAuMSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+')]">
        <h2 class="font-serif text-5xl md:text-7xl leading-none text-ink mb-8 relative z-10">
          Safe, predictable, <br/><i class="text-vermilion">reliable.</i>
        </h2>
        <p class="font-sans text-xl md:text-2xl text-ink/80 max-w-xl leading-relaxed relative z-10">
          LLMs are chaotic. We contain them. The AI only applies labels—it cannot delete or send mail. Your rules dictate the outcome. 
        </p>
        
        <div class="idempotent-stamp absolute right-12 md:right-32 top-1/2 -translate-y-1/2 z-20 pointer-events-none opacity-0 scale-[3]">
          <div class="border-8 border-vermilion text-vermilion font-mono font-bold text-4xl md:text-6xl tracking-widest px-6 py-4 mix-blend-multiply rotate-[-5deg]">
            IDEMPOTENT
          </div>
        </div>
      </div>
    </section>

    <!-- Footer CTA -->
    <section class="bg-vermilion text-cream p-8 md:p-24 flex flex-col items-center justify-center text-center relative border-t-2 border-ink z-10">
      <h2 class="font-serif text-[4rem] md:text-[8rem] leading-[0.8] italic mb-12">
        Open the mailroom.
      </h2>
      <div class="relative">
        <span class="absolute -left-32 top-2 font-hand text-2xl rotate-[-10deg] hidden md:block">Click here! &rarr;</span>
        <a href="/auth/google" class="ticket-btn bg-cream text-ink px-12 py-6 font-mono text-lg uppercase tracking-widest inline-block" @mouseenter="isHovering = true" @mouseleave="isHovering = false">
          Connect your Gmail
        </a>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const container = ref(null)
const cursor = ref(null)
const isHovering = ref(false)

const envelopes = [
  { id: 1, label: 'RECEIPT', delay: 0 },
  { id: 2, label: 'NEWSLETTER', delay: 1.5 },
  { id: 3, label: 'SPAM', delay: 3.0 },
  { id: 4, label: 'URGENT', delay: 4.5 },
]

const moveCursor = (e) => {
  if (cursor.value) {
    gsap.to(cursor.value, { x: e.clientX, y: e.clientY, duration: 0.1, ease: 'power2.out' })
  }
}

onMounted(() => {
  // Cursor tracking
  window.addEventListener('mousemove', moveCursor)

  // Scribble animation
  gsap.to('.scribble-path', {
    strokeDashoffset: 0,
    duration: 1,
    delay: 0.5,
    ease: 'power2.inOut'
  })

  // Postmark rotation
  gsap.to('.postmark', {
    rotate: 360,
    duration: 20,
    repeat: -1,
    ease: 'none'
  })

  // Envelope Animations
  envelopes.forEach((env) => {
    const el = `.env-${env.id}`
    const tl = gsap.timeline({ repeat: -1, delay: env.delay })
    
    // Fly in
    tl.fromTo(el, 
      { x: '-20vw', rotate: -15, scale: 0.8 },
      { x: '110vw', y: env.label === 'SPAM' ? 200 : -20, rotate: env.label === 'SPAM' ? 90 : 5, scale: 0.8, duration: 4.5, ease: 'none' }
    )
    
    // Stamp overlay pops in when passing the center
    const stampOverlay = `${el} .stamp-overlay`
    const stampTl = gsap.timeline({ repeat: -1, delay: env.delay })
    stampTl.to(stampOverlay, { duration: 2.16, opacity: 0, scale: 2 })
           .to(stampOverlay, { duration: 0.1, opacity: 1, scale: 1 })
           .to(stampOverlay, { duration: 2.24, opacity: 1, scale: 1 })
  })

  // Marquee
  gsap.to('.marquee-content', {
    x: '-50%',
    duration: 15,
    repeat: -1,
    ease: 'none'
  })

  // Receipt strip scroll reveal
  gsap.fromTo('.receipt-strip', 
    { y: 50, opacity: 0 },
    { 
      y: 0, opacity: 1, duration: 0.8, 
      scrollTrigger: {
        trigger: '.receipt-strip',
        start: 'top 85%'
      }
    }
  )

  // Idempotent Stamp reveal
  gsap.to('.idempotent-stamp', {
    scale: 1,
    opacity: 0.9,
    rotate: -5,
    duration: 0.6,
    ease: 'back.out(1.7)',
    scrollTrigger: {
      trigger: '.idempotent-stamp',
      start: 'top 70%'
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('mousemove', moveCursor)
  ScrollTrigger.getAll().forEach(t => t.kill())
})
</script>

<style scoped>
.grain-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  pointer-events: none;
  z-index: 50;
  opacity: 0.05;
}

.ticket-btn {
  background-color: #F1E9DA;
  border: 2px solid #15120E;
  box-shadow: 6px 6px 0 #15120E;
  transition: all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.ticket-btn:hover {
  transform: translate(3px, 3px);
  box-shadow: 3px 3px 0 #15120E;
}
.ticket-btn:active {
  transform: translate(6px, 6px);
  box-shadow: 0 0 0 #15120E;
}

.ticket-btn-red {
  background-color: #FF4B1F;
  color: #F1E9DA;
  border: 2px solid #15120E;
  box-shadow: 6px 6px 0 #15120E;
  transition: all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.ticket-btn-red:hover {
  transform: translate(3px, 3px);
  box-shadow: 3px 3px 0 #15120E;
}
.ticket-btn-red:active {
  transform: translate(6px, 6px);
  box-shadow: 0 0 0 #15120E;
}

.airmail-edge {
  background: repeating-linear-gradient(
    45deg,
    #FF4B1F,
    #FF4B1F 10px,
    transparent 10px,
    transparent 20px,
    #2B4BFF 20px,
    #2B4BFF 30px,
    transparent 30px,
    transparent 40px
  );
}

.receipt-strip {
  background-image: 
    radial-gradient(circle at 0px 10px, transparent 4px, #15120E 5px, #15120E 6px, transparent 7px),
    radial-gradient(circle at 100% 10px, transparent 4px, #15120E 5px, #15120E 6px, transparent 7px);
  background-size: 100% 20px;
  background-position: -6px 0, 6px 0;
  background-repeat: repeat-y;
  border-left: 2px dashed #15120E;
  border-right: 2px dashed #15120E;
}

.torn-bottom {
  mask-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 100 10" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><path d="M0,0 L100,0 L100,2 Q95,10 90,2 Q85,10 80,2 Q75,10 70,2 Q65,10 60,2 Q55,10 50,2 Q45,10 40,2 Q35,10 30,2 Q25,10 20,2 Q15,10 10,2 Q5,10 0,2 Z" fill="black"/></svg>');
  mask-size: 100% 10px;
  mask-position: bottom;
  mask-repeat: no-repeat;
  padding-bottom: 15px;
}
</style>
