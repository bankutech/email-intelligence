<template>
  <div class="min-h-screen flex flex-col">
    <!-- Navbar -->
    <header class="border-b border-border bg-background sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-sm bg-primary text-white flex items-center justify-center font-bold">EI</div>
          <span class="font-semibold text-lg tracking-tight text-textMain">AI Email Intelligence</span>
        </div>
        <div class="flex items-center gap-4">
          <template v-if="user">
            <span class="text-sm text-textMuted hidden sm:inline">{{ user.email }}</span>
            <button @click="logout" class="text-sm text-textMuted hover:text-textMain transition-colors" aria-label="Sign out">Sign out</button>
          </template>
          <a v-else href="/auth/google" class="btn btn-primary text-sm" role="button">Connect Gmail</a>
        </div>
      </div>
    </header>

    <main class="flex-1 flex w-full max-w-7xl mx-auto">
      <!-- Unauthenticated Hero -->
      <Hero v-if="!user && !loading" />
      
      <!-- Authenticated Layout -->
      <div v-else-if="user" class="flex flex-col md:flex-row w-full">
        <!-- Sidebar Navigation -->
        <nav class="w-full md:w-64 shrink-0 p-4 border-b md:border-b-0 md:border-r border-border flex md:flex-col gap-2 overflow-x-auto hide-scrollbar" aria-label="Main Navigation">
          <button v-for="tab in tabs" :key="tab.id" @click="currentTab = tab.id" 
            :class="['text-left px-3 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap', currentTab === tab.id ? 'bg-surfaceElevated text-textMain' : 'text-textMuted hover:bg-surface hover:text-textMain']"
            :aria-current="currentTab === tab.id ? 'page' : null">
            {{ tab.name }}
          </button>
        </nav>
        
        <!-- Tab Content -->
        <div class="flex-1 p-4 md:p-8 overflow-hidden">
          <KeepAlive>
            <Dashboard v-if="currentTab === 'dashboard'" />
            <Inbox v-else-if="currentTab === 'inbox'" />
            <ReviewQueue v-else-if="currentTab === 'review'" />
            <Settings v-else-if="currentTab === 'settings'" />
          </KeepAlive>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex-1 flex items-center justify-center min-h-[50vh]">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" role="status" aria-label="Loading application"></div>
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
  { id: 'inbox', name: 'Processed Emails' },
  { id: 'review', name: 'Review Queue' },
  { id: 'settings', name: 'Configuration' }
]

const fetchUser = async () => {
  try {
    const res = await fetch('/api/me')
    if (res.ok) {
      const data = await res.json()
      user.value = data.connected ? data : null
    } else {
      user.value = null
    }
  } catch (e) {
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
