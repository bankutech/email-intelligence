<template>
  <div class="min-h-screen bg-canvas text-ink font-sans flex flex-col antialiased">

    <!-- Loading Screen -->
    <div v-if="loading" class="min-h-screen flex items-center justify-center bg-canvas">
      <div class="flex flex-col items-center gap-3">
        <div class="w-8 h-8 rounded-full border-2 border-brand/20 border-t-brand animate-spin"></div>
        <span class="text-xs font-mono text-ink-muted">Initializing workspace...</span>
      </div>
    </div>

    <!-- Unauthenticated Landing Page -->
    <div v-else-if="!user" class="min-h-screen flex flex-col justify-between">
      <header class="px-6 h-16 border-b border-border flex items-center justify-between bg-surface/70 backdrop-blur-md sticky top-0 z-20">
        <div class="flex items-center gap-2.5">
          <div class="w-6 h-6 rounded-lg bg-ink flex items-center justify-center text-surface font-mono text-xs font-bold">
            EA
          </div>
          <span class="font-semibold text-sm tracking-tight text-ink">Email Automata</span>
        </div>
        <a href="/auth/demo" class="text-xs font-semibold text-brand hover:underline">
          Explore Demo Workspace &rarr;
        </a>
      </header>

      <main class="flex-1">
        <Hero />
      </main>

      <footer class="px-6 py-4 border-t border-border-subtle text-center text-xs text-ink-muted font-mono">
        Email Automata &middot; Deterministic Intelligence Engine &middot; Scoped via gmail.modify
      </footer>
    </div>

    <!-- Authenticated Main Application Shell -->
    <div v-else class="h-[100dvh] max-h-[100dvh] w-screen overflow-hidden flex flex-col md:flex-row bg-canvas">
      
      <!-- Collapsible Sidebar Navigation -->
      <aside
        :class="[
          'h-[100dvh] max-h-[100dvh] bg-surface border-r border-border flex flex-col transition-all duration-300 z-30 shrink-0 select-none',
          isSidebarCollapsed ? 'w-16' : 'w-60',
          'hidden md:flex'
        ]"
      >
        <!-- Top: Sidebar Brand & Header -->
        <div class="h-14 px-3.5 border-b border-border flex items-center justify-between shrink-0">
          <div class="flex items-center gap-2.5 min-w-0" :class="{ 'mx-auto': isSidebarCollapsed }">
            <div class="w-7 h-7 rounded-lg bg-ink flex items-center justify-center text-surface font-mono text-xs font-bold shrink-0">
              EA
            </div>
            <span v-if="!isSidebarCollapsed" class="font-semibold text-sm tracking-tight text-ink truncate font-serif">
              Email Automata
            </span>
          </div>

          <button
            v-if="!isSidebarCollapsed"
            @click="isSidebarCollapsed = true"
            class="p-1.5 text-ink-muted hover:text-ink hover:bg-canvas-subtle rounded-md transition-colors"
            title="Collapse sidebar"
            aria-label="Collapse sidebar"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
            </svg>
          </button>
        </div>

        <!-- Collapsed Mode Expand Button -->
        <div v-if="isSidebarCollapsed" class="p-2 border-b border-border-subtle flex justify-center shrink-0">
          <button
            @click="isSidebarCollapsed = false"
            class="p-1.5 text-ink-muted hover:text-ink hover:bg-canvas-subtle rounded-md transition-colors"
            title="Expand sidebar"
            aria-label="Expand sidebar"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
            </svg>
          </button>
        </div>

        <!-- Navigation items: occupies remaining space, scrollable if height is constrained -->
        <nav class="flex-1 min-h-0 overflow-y-auto px-2.5 py-3 space-y-1" aria-label="Main Navigation">
          <button
            v-for="item in navItems"
            :key="item.id"
            @click="currentTab = item.id"
            :class="[
              'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors relative group',
              isSidebarCollapsed ? 'justify-center px-0' : '',
              currentTab === item.id
                ? 'bg-ink text-surface shadow-xs font-semibold'
                : 'text-ink-secondary hover:text-ink hover:bg-canvas-subtle'
            ]"
            :title="isSidebarCollapsed ? item.name : ''"
          >
            <!-- Icon -->
            <span class="w-4 h-4 shrink-0 flex items-center justify-center">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" :d="item.icon"/>
              </svg>
            </span>

            <!-- Label -->
            <span v-if="!isSidebarCollapsed" class="truncate flex-1 text-left">
              {{ item.name }}
            </span>

            <!-- Badge for Review Queue -->
            <span
              v-if="item.id === 'review' && reviewCount > 0"
              :class="[
                'px-1.5 py-0.2 rounded-full font-mono text-[10px] font-bold shrink-0',
                isSidebarCollapsed ? 'absolute -top-1 -right-1 w-4 h-4 p-0 flex items-center justify-center text-[9px]' : '',
                currentTab === 'review' ? 'bg-surface text-ink' : 'bg-status-warning text-surface'
              ]"
            >
              {{ reviewCount }}
            </span>
          </button>
        </nav>

        <!-- Sidebar Footer & User Profile: ANCHORED PERMANENTLY AT BOTTOM WITH mt-auto shrink-0 -->
        <div class="mt-auto shrink-0 p-2.5 border-t border-border bg-surface/50 space-y-2">
          
          <!-- Collapsed Mode Profile & Sign-Out -->
          <div v-if="isSidebarCollapsed" class="flex flex-col items-center gap-2 py-1">
            <div
              class="w-8 h-8 rounded-full bg-brand/10 text-brand flex items-center justify-center text-xs font-mono font-bold shrink-0 border border-brand/20"
              :title="`Signed in as ${user.email} (${user.is_demo ? 'Demo' : 'Live'})`"
            >
              {{ user.email ? user.email.charAt(0).toUpperCase() : 'U' }}
            </div>
            <button
              @click="logout"
              class="w-8 h-8 flex items-center justify-center text-ink-muted hover:text-status-danger hover:bg-canvas-subtle rounded-md transition-colors"
              :title="`Sign Out (${user.email})`"
              aria-label="Sign Out"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
              </svg>
            </button>
          </div>

          <!-- Expanded Mode Profile & Sign-Out -->
          <template v-else>
            <!-- Demo Indicator in Sidebar -->
            <div v-if="user.is_demo" class="px-2.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] flex items-center justify-between">
              <div class="flex items-center gap-1.5 text-amber-800 font-mono font-medium">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                Demo Workspace
              </div>
              <span class="text-[10px] text-amber-700/80 font-mono">Isolated</span>
            </div>

            <!-- User Card with Sign-Out button -->
            <div class="flex items-center justify-between p-2 rounded-lg bg-canvas-subtle border border-border-subtle">
              <div class="flex items-center gap-2 min-w-0 pr-1">
                <div class="w-7 h-7 rounded-full bg-brand/10 text-brand flex items-center justify-center text-xs font-mono font-bold shrink-0 border border-brand/20">
                  {{ user.email ? user.email.charAt(0).toUpperCase() : 'U' }}
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-mono text-ink truncate font-medium leading-tight" :title="user.email">{{ user.email }}</p>
                  <p class="text-[10px] text-ink-muted font-mono leading-tight mt-0.5">{{ user.is_demo ? 'Demo session' : 'Live account' }}</p>
                </div>
              </div>

              <button
                @click="logout"
                class="p-1.5 text-ink-muted hover:text-status-danger hover:bg-surface rounded-md transition-colors shrink-0"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                </svg>
              </button>
            </div>
          </template>
        </div>
      </aside>

      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col min-w-0 h-[100dvh] max-h-[100dvh] overflow-hidden">
        
        <!-- Top App Bar (Workspace Status + Sync Controls) -->
        <header class="h-14 px-5 md:px-8 border-b border-border bg-surface/90 backdrop-blur-md shrink-0 flex items-center justify-between z-10">
          
          <!-- Left: Tab Title & Workspace Badge -->
          <div class="flex items-center gap-3 min-w-0">
            <!-- Mobile Menu Toggle -->
            <button
              @click="isMobileMenuOpen = !isMobileMenuOpen"
              class="md:hidden p-1.5 rounded-lg text-ink-secondary hover:bg-canvas-muted"
              aria-label="Toggle navigation menu"
              :aria-expanded="isMobileMenuOpen"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
              </svg>
            </button>

            <h1 class="text-sm md:text-base font-semibold text-ink font-serif truncate">
              {{ currentTabTitle }}
            </h1>

            <!-- Workspace Status Pill -->
            <span
              v-if="user.is_demo"
              class="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-500/10 text-amber-800 border border-amber-500/20"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              Demo Workspace
            </span>
            <span
              v-else
              class="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-status-successBg text-status-success border border-status-successBorder"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse"></span>
              Gmail Connected
            </span>
          </div>

          <!-- Right: Sync & Actions -->
          <div class="flex items-center gap-3">
            <!-- Sync / Refresh Button -->
            <button
              @click="syncData"
              :disabled="isRefreshing"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface border border-border text-ink hover:bg-canvas-subtle shadow-xs transition-all disabled:opacity-50"
              title="Refresh inbox data"
            >
              <svg :class="['w-3.5 h-3.5', isRefreshing ? 'animate-spin text-brand' : 'text-ink-muted']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span class="hidden sm:inline">{{ isRefreshing ? 'Refreshing...' : 'Refresh' }}</span>
            </button>
          </div>
        </header>

        <!-- Mobile Navigation Menu Drawer -->
        <div v-if="isMobileMenuOpen" class="md:hidden bg-surface border-b border-border p-3 space-y-1.5 shrink-0">
          <button
            v-for="item in navItems"
            :key="item.id"
            @click="currentTab = item.id; isMobileMenuOpen = false"
            :class="[
              'w-full flex items-center justify-between p-2 rounded-lg text-xs font-semibold',
              currentTab === item.id ? 'bg-ink text-surface' : 'text-ink-secondary hover:bg-canvas-subtle'
            ]"
          >
            <span>{{ item.name }}</span>
            <span v-if="item.id === 'review' && reviewCount > 0" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-status-warning text-surface">
              {{ reviewCount }}
            </span>
          </button>
          <div class="pt-2 border-t border-border-subtle flex items-center justify-between px-1">
            <span class="text-xs font-mono text-ink-muted truncate">{{ user.email }}</span>
            <button @click="logout" class="text-xs text-status-danger font-medium">Sign Out</button>
          </div>
        </div>

        <!-- Viewport Container with Independent Scrolling -->
        <main class="flex-1 min-h-0 overflow-y-auto px-4 py-5 md:px-8 md:py-6">
          <div class="max-w-6xl mx-auto w-full">
            <KeepAlive>
              <Dashboard
                v-if="currentTab === 'dashboard'"
                :stats="stats"
                :recentEmails="emails"
                @navigate="handleNavigation"
                @select-email="selectedEmail = $event"
                @refresh="fetchWorkspace"
              />
              <Inbox
                v-else-if="currentTab === 'inbox'"
                :emails="emails"
                :loading="isEmailsLoading"
                :initialCategory="inboxInitialCategory"
                @select-email="selectedEmail = $event"
              />
              <ReviewQueue
                v-else-if="currentTab === 'review'"
                :emails="emails"
                @refresh="fetchWorkspace"
              />
              <Analytics
                v-else-if="currentTab === 'analytics'"
                :stats="stats"
              />
              <Settings
                v-else-if="currentTab === 'settings'"
                :user="user"
                @logout="logout"
                @refresh="fetchWorkspace"
              />
            </KeepAlive>
          </div>
        </main>

      </div>

    </div>

    <!-- Global Slide-over Email Reader -->
    <EmailReader
      v-if="selectedEmail"
      :email="selectedEmail"
      @close="selectedEmail = null"
      @updated="handleEmailUpdated"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Hero from './components/Hero.vue'
import Dashboard from './components/Dashboard.vue'
import Inbox from './components/Inbox.vue'
import ReviewQueue from './components/ReviewQueue.vue'
import Analytics from './components/Analytics.vue'
import Settings from './components/Settings.vue'
import EmailReader from './components/EmailReader.vue'

const user = ref(null)
const loading = ref(true)
const currentTab = ref('dashboard')
const isSidebarCollapsed = ref(false)
const isMobileMenuOpen = ref(false)

const stats = ref(null)
const emails = ref([])
const isEmailsLoading = ref(false)
const isRefreshing = ref(false)
const selectedEmail = ref(null)
const inboxInitialCategory = ref('all')

const navItems = [
  { id: 'dashboard', name: 'Overview', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { id: 'inbox', name: 'Processed Inbox', icon: 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4' },
  { id: 'review', name: 'Review Queue', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
  { id: 'analytics', name: 'Intelligence Audit', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { id: 'settings', name: 'System Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z' },
]

const currentTabTitle = computed(() => {
  const item = navItems.find(i => i.id === currentTab.value)
  return item ? item.name : 'Workspace'
})

const reviewCount = computed(() => {
  return emails.value.filter(e => e.status === 'review').length
})

const handleNavigation = (tab, category = 'all') => {
  currentTab.value = tab
  if (tab === 'inbox' && category) {
    inboxInitialCategory.value = category
  }
}

const handleEmailUpdated = (updated) => {
  const idx = emails.value.findIndex(e => e.message_id === updated.message_id)
  if (idx !== -1) {
    emails.value[idx] = { ...emails.value[idx], ...updated }
  }
  fetchWorkspace()
}

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

const fetchWorkspace = async () => {
  if (!user.value) return
  isEmailsLoading.value = true
  try {
    const [statsRes, emailsRes] = await Promise.all([
      fetch('/api/dashboard', { cache: 'no-store' }),
      fetch('/api/emails', { cache: 'no-store' })
    ])
    if (statsRes.ok) stats.value = await statsRes.json()
    if (emailsRes.ok) emails.value = await emailsRes.json()
  } catch (err) {
    console.error('Workspace fetch error:', err)
  } finally {
    isEmailsLoading.value = false
  }
}

const syncData = async () => {
  isRefreshing.value = true
  await fetchWorkspace()
  setTimeout(() => { isRefreshing.value = false }, 500)
}

const logout = async () => {
  await fetch('/api/disconnect', { method: 'POST' })
  window.location.href = '/'
}

let pollTimer
onMounted(async () => {
  await fetchUser()
  if (user.value) {
    await fetchWorkspace()
    pollTimer = setInterval(fetchWorkspace, 15000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade {
  animation: fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
