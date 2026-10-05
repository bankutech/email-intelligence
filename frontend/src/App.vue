<template>
  <div class="min-h-screen bg-nyalbg text-nyalaslate font-sans flex flex-col">

    <header v-if="user" class="bg-nyalawhite shadow-sm sticky top-0 z-40 transition-all">
      <div class="px-4 md:px-[150px] h-20 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <svg class="w-8 h-8 text-nyalablue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
          <span class="font-display font-bold text-xl text-nyalablue hidden sm:inline">Nyalazone Mail</span>
        </div>
        <div class="flex items-center gap-6">
          <span class="hidden sm:inline font-medium text-nyalaslate/70">{{ user.email }}</span>
          <button @click="logout" class="px-6 py-2.5 rounded-full bg-nyalaslate/10 text-nyalaslate font-medium hover:bg-nyalaslate/20 transition-colors">Sign Out</button>
        </div>
      </div>
    </header>

    <main class="flex-1 flex flex-col w-full animate-slide-up opacity-0">
      <Hero v-if="!user && !loading"/>

      <div v-else-if="user" class="flex flex-col w-full px-4 md:px-[150px] pt-12 mx-auto">
        <nav class="flex gap-8 border-b border-nyalaslate/10" aria-label="Main Navigation">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="currentTab = tab.id"
            :class="[
              'pb-4 font-medium text-base transition-colors relative',
              currentTab === tab.id
                ? 'text-nyalablue'
                : 'text-nyalaslate/50 hover:text-nyalaslate'
            ]"
          >
            {{ tab.name }}
            <div v-if="currentTab === tab.id" class="absolute bottom-0 left-0 w-full h-0.5 bg-nyalablue rounded-t-full"></div>
          </button>
        </nav>

        <div class="flex-1 pt-12 pb-24">
          <KeepAlive>
            <Dashboard v-if="currentTab === 'dashboard'"/>
            <Inbox v-else-if="currentTab === 'inbox'"/>
            <ReviewQueue v-else-if="currentTab === 'review'"/>
            <Settings v-else-if="currentTab === 'settings'"/>
          </KeepAlive>
        </div>
      </div>

      <div v-if="loading" class="flex-1 flex items-center justify-center min-h-[50vh]">
        <div class="flex flex-col items-center gap-6 animate-pulse">
          <div class="w-12 h-12 rounded-full border-4 border-nyalablue/20 border-t-nyalablue animate-spin"></div>
          <span class="font-display text-xl text-nyalaslate/70">Loading workspace...</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Hero from './components/Hero.vue'
import Dashboard from './components/Dashboard.vue'
import Inbox from './components/Inbox.vue'
import ReviewQueue from './components/ReviewQueue.vue'
import Settings from './components/Settings.vue'

const user = ref(null)
const loading = ref(true)
const currentTab = ref('dashboard')

const tabs = [
  { id: 'dashboard', name: 'Overview' },
  { id: 'inbox', name: 'Processed' },
  { id: 'review', name: 'Review Queue' },
  { id: 'settings', name: 'Settings' },
]

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

onMounted(() => {
  fetchUser()
})
</script>
