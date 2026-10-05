<template>
  <div class="w-full bg-cream text-ink font-dispatchSans relative overflow-hidden">

    <svg class="pointer-events-none fixed inset-0 z-50 opacity-[0.04] w-full h-full">
      <filter id="heroNoise">
        <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" stitchTiles="stitch"/>
      </filter>
      <rect width="100%" height="100%" filter="url(#heroNoise)"/>
    </svg>

    <nav class="absolute top-0 w-full px-4 md:px-8 py-4 flex justify-between items-center z-40">
      <div class="font-mono text-xs tracking-widest uppercase flex items-center gap-2">
        <div class="w-2 h-2 bg-vermilion rounded-full animate-pulse"></div>
        AI Email Intelligence
      </div>
      <a href="/auth/google" class="ticket-btn px-4 py-2 font-mono text-xs uppercase tracking-widest font-bold">
        Connect Gmail
      </a>
    </nav>

    <section class="min-h-screen pt-28 md:pt-0 flex flex-col md:flex-row items-stretch border-b-2 border-ink">
      <div class="w-full md:w-1/2 p-6 md:p-16 flex flex-col justify-center relative">

        <div class="font-mono text-xs tracking-widest uppercase mb-8 border-2 border-ink inline-block px-2 py-1 w-max">
          NO. 0001 — INCOMING / OUTGOING
        </div>

        <h1 class="font-serif leading-[0.85] tracking-tight text-ink relative z-10 mb-8" style="font-size: clamp(4rem, 9vw, 11rem)">
          <span class="block">Your inbox,</span>
          <span class="italic text-vermilion relative inline-block">
            finally
            <svg class="absolute -bottom-2 md:-bottom-4 left-0 w-full overflow-visible" viewBox="0 0 200 20" preserveAspectRatio="none" height="24">
              <path ref="scribblePath" d="M 5,10 Q 50,20 100,5 T 195,15" fill="none" stroke="#FF4B1F" stroke-width="4" stroke-linecap="round" stroke-dasharray="250" stroke-dashoffset="250"/>
            </svg>
          </span>
          <span class="block">sorted.</span>
        </h1>

        <p class="max-w-md text-lg md:text-xl font-medium text-ink/75 leading-relaxed mb-10 relative">
          <span class="absolute -left-12 top-1 font-hand text-2xl text-vermilion rotate-[-15deg] hidden md:block">Read this! →</span>
          AI reads every email and decides what it is. Plain Python decides what happens next. Same email twice? Nothing breaks.
        </p>

        <a href="/auth/google" class="ticket-btn-red px-8 py-4 font-mono text-sm uppercase tracking-widest font-bold w-max gap-3">
          Open the Mailroom
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </a>

        <div ref="postmark" class="absolute top-24 right-8 w-28 h-28 border-2 border-ink rounded-full flex items-center justify-center opacity-15 pointer-events-none hidden md:flex">
          <span class="font-mono text-[9px] uppercase tracking-widest text-center leading-relaxed">Sorted<br/>Filed<br/>Done</span>
        </div>
      </div>

      <div class="w-full md:w-1/2 border-l-2 border-ink relative overflow-hidden hidden md:block" style="min-height: 500px;">
        <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-20">
          <div class="w-16 h-32 border-4 border-ink bg-cream shadow-[8px_8px_0_#15120E] relative flex items-center justify-center">
            <div class="w-10 h-10 rounded-full border-4 border-airmail bg-airmail/10"></div>
            <span class="absolute -top-7 -left-20 font-hand text-xl text-ink -rotate-12">AI Gate</span>
          </div>
        </div>
        <div class="absolute top-1/2 left-0 w-full h-px bg-ink/20"></div>
        <div v-for="env in envelopes" :key="env.id" :class="`env-${env.id} absolute top-1/2 left-0 z-10`">
          <div class="w-44 h-28 bg-cream border-2 border-ink shadow-md overflow-hidden flex flex-col justify-between p-1">
            <div class="airmail-edge h-2 w-full"></div>
            <div :class="`env-stamp-${env.id} absolute inset-0 flex items-center justify-center bg-cream/85 opacity-0 scale-150`">
              <span :class="['border-4 px-2 py-1 font-mono font-bold tracking-widest text-base rotate-[-10deg]', env.label === 'SPAM' ? 'border-vermilion text-vermilion' : 'border-ink text-ink']">{{ env.label }}</span>
            </div>
            <div class="airmail-edge h-2 w-full"></div>
          </div>
        </div>
        <div class="absolute bottom-4 right-4 font-mono text-[10px] uppercase tracking-widest text-ink/40 text-right">
          Mailroom<br/>[ LIVE ]
        </div>
      </div>
    </section>

    <div class="border-b-2 border-ink bg-vermilion text-cream overflow-hidden py-3 whitespace-nowrap">
      <div ref="marquee" class="flex font-mono text-sm uppercase tracking-widest font-bold">
        <div v-for="i in 8" :key="i" class="flex items-center shrink-0">
          <span class="mx-8">Invoice #4821 → <span class="border border-cream px-1">RECEIPT</span></span>
          <span class="mx-8">Project Deadline → <span class="border border-cream px-1">URGENT</span></span>
          <span class="mx-8">Weekly Digest → <span class="border border-cream px-1">NEWSLETTER</span></span>
        </div>
      </div>
    </div>

    <section class="flex flex-col md:flex-row min-h-[80vh]">
      <div class="w-full md:w-1/3 border-r-2 border-ink p-8 md:p-12 flex justify-center items-start pt-16">
        <div class="receipt-strip-left w-full max-w-sm p-6 bg-cream shadow-[6px_6px_0_#15120E] border-r-2 border-ink">
          <h3 class="font-mono text-sm font-bold tracking-widest border-b-2 border-ink pb-4 mb-6 uppercase">Operating Procedure</h3>
          <ol class="font-mono text-sm space-y-6">
            <li class="flex gap-4">
              <span class="text-vermilion font-bold">01</span>
              <span class="leading-relaxed">AI reads each incoming message. No templates — true semantic understanding.</span>
            </li>
            <li class="flex gap-4">
              <span class="text-vermilion font-bold">02</span>
              <span class="leading-relaxed">Plain Python rules decide what happens next. Deterministic, auditable.</span>
            </li>
            <li class="flex gap-4">
              <span class="text-vermilion font-bold">03</span>
              <span class="leading-relaxed">Gmail is updated. Same email processed twice? Nothing breaks.</span>
            </li>
          </ol>
          <div class="mt-8 pt-4 border-t-2 border-dashed border-ink text-center font-mono text-xs opacity-40">END OF TAPE</div>
        </div>
      </div>

      <div class="w-full md:w-2/3 p-8 md:p-24 flex flex-col justify-center relative overflow-hidden">
        <div class="absolute inset-0 opacity-5" style="background-image: repeating-linear-gradient(0deg, transparent, transparent 39px, #15120E 39px, #15120E 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, #15120E 39px, #15120E 40px);"></div>
        <h2 class="font-serif text-5xl md:text-7xl leading-none text-ink mb-8 relative z-10">
          Safe, predictable,<br/><i class="text-vermilion">reliable.</i>
        </h2>
        <p class="font-dispatchSans text-xl md:text-2xl text-ink/75 max-w-xl leading-relaxed relative z-10">
          The AI only applies labels. It cannot delete or send mail. Your Python rules dictate every outcome.
        </p>
        <div ref="idempotentStamp" class="absolute right-8 md:right-24 top-1/2 -translate-y-1/2 z-20 pointer-events-none opacity-0 scale-[3]">
          <div class="border-8 border-vermilion text-vermilion font-mono font-bold text-3xl md:text-5xl tracking-widest px-4 py-3 mix-blend-multiply rotate-[-5deg]">
            IDEMPOTENT
          </div>
        </div>
      </div>
    </section>

    <section class="bg-vermilion text-cream p-8 md:p-24 flex flex-col items-center justify-center text-center border-t-2 border-ink relative">
      <h2 class="font-serif italic mb-12 leading-[0.85]" style="font-size: clamp(3.5rem, 8vw, 9rem)">Open the mailroom.</h2>
      <div class="relative">
        <span class="absolute -left-32 top-2 font-hand text-2xl rotate-[-10deg] hidden md:block">Click here! →</span>
        <a href="/auth/google" class="ticket-btn font-mono text-lg uppercase tracking-widest font-bold px-12 py-6">
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

const scribblePath = ref(null)
const postmark = ref(null)
const marquee = ref(null)
const idempotentStamp = ref(null)

const envelopes = [
  { id: 1, label: 'RECEIPT', delay: 0 },
  { id: 2, label: 'NEWSLETTER', delay: 1.6 },
  { id: 3, label: 'SPAM', delay: 3.2 },
  { id: 4, label: 'URGENT', delay: 4.8 },
]

let ctx

onMounted(() => {
  ctx = gsap.context(() => {
    gsap.to(scribblePath.value, { strokeDashoffset: 0, duration: 1, delay: 0.4, ease: 'power2.inOut' })
    gsap.to(postmark.value, { rotate: 360, duration: 20, repeat: -1, ease: 'none' })
    gsap.to(marquee.value, { x: '-50%', duration: 18, repeat: -1, ease: 'none' })

    envelopes.forEach((env) => {
      const el = `.env-${env.id}`
      const stamp = `.env-stamp-${env.id}`
      const tl = gsap.timeline({ repeat: -1, delay: env.delay })
      tl.fromTo(el,
        { x: '-120px', y: '-50%', rotate: -12, scale: 0.85, opacity: 0 },
        { x: '110vw', y: env.label === 'SPAM' ? '30%' : '-60%', rotate: env.label === 'SPAM' ? 80 : 4, scale: 0.85, opacity: 1, duration: 5, ease: 'none' }
      )
      const stampTl = gsap.timeline({ repeat: -1, delay: env.delay })
      stampTl
        .to(stamp, { duration: 2.3, opacity: 0, scale: 2 })
        .to(stamp, { duration: 0.12, opacity: 1, scale: 1, ease: 'back.out(2)' })
        .to(stamp, { duration: 2.58, opacity: 1 })
    })

    gsap.fromTo('.receipt-strip-left',
      { y: 40, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.7, scrollTrigger: { trigger: '.receipt-strip-left', start: 'top 85%' } }
    )

    gsap.to(idempotentStamp.value, {
      scale: 1, opacity: 0.9,
      duration: 0.5, ease: 'back.out(1.5)',
      scrollTrigger: { trigger: idempotentStamp.value, start: 'top 70%' }
    })
  })
})

onUnmounted(() => {
  ctx && ctx.revert()
  ScrollTrigger.getAll().forEach(t => t.kill())
})
</script>
