<template>
  <div class="min-h-screen bg-cream text-ink font-dispatchSans flex flex-col relative overflow-hidden">

    <div ref="cursor" class="fixed top-0 left-0 z-[100] pointer-events-none -translate-x-1/2 -translate-y-1/2 hidden md:flex items-center justify-center">
      <div v-if="isHovering" class="w-8 h-8 rounded-full border-2 border-vermilion bg-vermilion/20 flex items-center justify-center rotate-12">
        <span class="font-mono text-[8px] font-bold text-vermilion tracking-tighter">CLICK</span>
      </div>
      <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#15120E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="rotate-[-15deg]">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
        <polyline points="22,6 12,13 2,6"/>
      </svg>
    </div>

    <svg class="pointer-events-none fixed inset-0 z-50 opacity-[0.04] w-full h-full mix-blend-multiply">
      <filter id="grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" stitchTiles="stitch"/>
      </filter>
      <rect width="100%" height="100%" filter="url(#grain)"/>
    </svg>

    <header v-if="user" class="border-b-2 border-ink bg-cream sticky top-0 z-40">
      <div class="px-4 sm:px-8 h-12 flex items-center justify-between font-mono uppercase tracking-widest text-xs">
        <div class="flex items-center gap-3">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
          <span class="font-bold hidden sm:inline">AI Email Intelligence</span>
        </div>
        <div class="absolute left-1/2 -translate-x-1/2 font-bold hidden md:block">
          {{ currentDateStr }} — VOL. 1
        </div>
        <div class="flex items-center gap-4">
          <span class="hidden sm:inline font-bold truncate max-w-[200px]">{{ user.email }}</span>
          <button @click="logout" class="ticket-btn px-3 py-1 font-mono text-xs font-bold uppercase tracking-widest">Sign Out</button>
        </div>
      </div>
    </header>

    <main class="flex-1 flex flex-col w-full">
      <Hero v-if="!user && !loading"/>

      <div v-else-if="user" class="flex flex-col w-full px-4 sm:px-8 pt-8 max-w-[1600px] mx-auto">
        <nav class="flex overflow-x-auto hide-scrollbar gap-1 border-b-2 border-ink" aria-label="Main Navigation">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="currentTab = tab.id"
            :class="[
              'px-6 py-3 font-mono uppercase tracking-widest text-sm font-bold border-2 border-ink border-b-0 rounded-t-lg transition-all whitespace-nowrap',
              currentTab === tab.id
                ? 'bg-cream text-ink z-10 pb-4 -mb-[2px]'
                : 'bg-ink/5 text-ink/50 hover:bg-ink/10 hover:text-ink'
            ]"
          >
            {{ tab.name }}
          </button>
        </nav>

        <div class="flex-1 pt-8 pb-16">
          <KeepAlive>
            <Dashboard v-if="currentTab === 'dashboard'"/>
            <Inbox v-else-if="currentTab === 'inbox'"/>
            <ReviewQueue v-else-if="currentTab === 'review'"/>
            <Settings v-else-if="currentTab === 'settings'"/>
          </KeepAlive>
        </div>
      </div>

      <div v-if="loading" class="flex-1 flex items-center justify-center min-h-[50vh]">
        <div class="flex flex-col items-center gap-4">
          <svg class="w-12 h-12 text-ink animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
          <span class="font-hand text-2xl text-ink">Sorting the mailroom...</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import gsap from 'gsap'
import Hero from './components/Hero.vue'
import Dashboard from './components/Dashboard.vue'
import Inbox from './components/Inbox.vue'
import ReviewQueue from './components/ReviewQueue.vue'
import Settings from './components/Settings.vue'

const user = ref(null)
const loading = ref(true)
const currentTab = ref('dashboard')
const cursor = ref(null)
const isHovering = ref(false)

const tabs = [
  { id: 'dashboard', name: 'Overview' },
  { id: 'inbox', name: 'Processed' },
  { id: 'review', name: 'Review Queue' },
  { id: 'settings', name: 'Settings' },
]

const currentDateStr = computed(() => {
  const d = new Date()
  const days = ['SUN','MON','TUE','WED','THU','FRI','SAT']
  const months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
  return `${days[d.getDay()]} ${String(d.getDate()).padStart(2,'0')} ${months[d.getMonth()]} ${d.getFullYear()}`
})

const fetchUser = async () => {
  try {
    const res = await fetch('/api/me', { cache: 'no-store' })
    if (res.ok) {
      const data = await res.json()
      user.value = data.connected ? data : null
    } else {
      user.value = null
    }
  } catch {
    user.value = null
  } finally {
    loading.value = false
  }
}

const logout = async () => {
  await fetch('/api/disconnect', { method: 'POST' })
  window.location.href = '/'
}

const moveCursor = (e) => {
  if (cursor.value) gsap.to(cursor.value, { x: e.clientX, y: e.clientY, duration: 0.1, ease: 'power2.out' })
}

const handleMouseOver = (e) => {
  isHovering.value = !!(e.target.closest('button') || e.target.closest('a'))
}

onMounted(() => {
  fetchUser()
  window.addEventListener('mousemove', moveCursor)
  window.addEventListener('mouseover', handleMouseOver)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', moveCursor)
  window.removeEventListener('mouseover', handleMouseOver)
})
</script>
