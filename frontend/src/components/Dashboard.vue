<template>
  <div class="space-y-6 animate-fade pb-10">

    <!-- Workspace Header & Engine Controls -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-border">
      <div>
        <div class="flex items-center gap-2.5">
          <h2 class="text-base sm:text-lg font-semibold text-ink tracking-tight font-serif">Workspace Overview</h2>
          <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Live Engine (60s)
          </span>
        </div>
        <p class="text-xs text-ink-secondary mt-0.5">
          Deterministic security rules paired with Gemini 2.5 Flash classification.
          <span v-if="stats?.last_sync" class="text-ink-muted ml-1">&middot; Last sync: {{ formatRelative(stats.last_sync) }}</span>
        </p>
      </div>

      <div class="flex items-center gap-2 shrink-0">
        <button
          @click="triggerScan"
          :disabled="isScanning"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-brand text-surface hover:bg-brand-hover shadow-xs transition-all disabled:opacity-50"
        >
          <svg v-if="isScanning" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          <span>{{ isScanning ? 'Syncing...' : 'Scan Now' }}</span>
        </button>
      </div>
    </div>

    <!-- Review Queue Alert Callout (If items need review) -->
    <div
      v-if="(stats?.needs_review || 0) > 0"
      class="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 shadow-xs"
    >
      <div class="flex items-center gap-2.5 min-w-0">
        <span class="w-2 h-2 rounded-full bg-amber-500 shrink-0"></span>
        <p class="text-xs font-medium text-amber-900 truncate">
          <strong class="font-semibold">{{ stats.needs_review }} email{{ stats.needs_review > 1 ? 's' : '' }}</strong> require human confirmation due to lower confidence or rule flags.
        </p>
      </div>
      <button
        @click="$emit('navigate', 'review')"
        class="inline-flex items-center gap-1 text-xs font-semibold text-amber-900 hover:text-amber-950 underline underline-offset-2 shrink-0"
      >
        Open Review Queue &rarr;
      </button>
    </div>

    <!-- Integrated Intelligence Metrics Strip (Human-Designed Editorial Grid) -->
    <div class="grid grid-cols-2 md:grid-cols-4 rounded-xl border border-border bg-surface divide-y md:divide-y-0 md:divide-x divide-border shadow-xs overflow-hidden">
      <!-- Total Processed -->
      <div class="p-4 sm:p-5">
        <span class="text-[11px] font-mono uppercase tracking-wider text-ink-muted block">Total Processed</span>
        <div class="flex items-baseline gap-2 mt-1">
          <span class="text-2xl sm:text-3xl font-semibold font-mono text-ink tracking-tight">{{ stats?.total_processed ?? 0 }}</span>
          <span class="text-xs text-ink-muted">inbox items</span>
        </div>
        <p class="text-[11px] text-ink-secondary mt-1.5 flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          Indexed in SQLite
        </p>
      </div>

      <!-- Automation Rate -->
      <div class="p-4 sm:p-5">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-mono uppercase tracking-wider text-ink-muted">Automation Rate</span>
          <span class="text-[10px] font-mono font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded">autonomous</span>
        </div>
        <div class="flex items-baseline gap-2 mt-1">
          <span class="text-2xl sm:text-3xl font-semibold font-mono text-ink tracking-tight">{{ stats?.automation_rate ?? 100 }}%</span>
        </div>
        <p class="text-[11px] text-ink-secondary mt-1.5 truncate">
          {{ stats?.automated_count ?? stats?.total_processed ?? 0 }} handled without review
        </p>
      </div>

      <!-- Review Queue -->
      <div
        class="p-4 sm:p-5 cursor-pointer hover:bg-canvas-subtle/60 transition-colors group"
        @click="$emit('navigate', 'review')"
        title="View Review Queue"
      >
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-mono uppercase tracking-wider text-ink-muted group-hover:text-ink transition-colors">Review Queue</span>
          <span
            v-if="(stats?.needs_review || 0) > 0"
            class="text-[10px] font-mono font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.2 rounded"
          >
            Action needed
          </span>
        </div>
        <div class="flex items-baseline gap-2 mt-1">
          <span class="text-2xl sm:text-3xl font-semibold font-mono" :class="(stats?.needs_review || 0) > 0 ? 'text-amber-600' : 'text-ink'">
            {{ stats?.needs_review ?? 0 }}
          </span>
          <span class="text-xs text-ink-muted">pending</span>
        </div>
        <p class="text-[11px] text-ink-secondary mt-1.5">
          {{ (stats?.needs_review || 0) > 0 ? 'Awaiting confirmation' : 'Zero backlog' }}
        </p>
      </div>

      <!-- High Priority -->
      <div class="p-4 sm:p-5">
        <span class="text-[11px] font-mono uppercase tracking-wider text-ink-muted block">High Priority</span>
        <div class="flex items-baseline gap-2 mt-1">
          <span class="text-2xl sm:text-3xl font-semibold font-mono" :class="(stats?.high_priority || 0) > 0 ? 'text-rose-600' : 'text-ink'">
            {{ stats?.high_priority ?? 0 }}
          </span>
          <span class="text-xs text-ink-muted">urgent items</span>
        </div>
        <p class="text-[11px] text-ink-secondary mt-1.5">
          Avg confidence: {{ Math.round((stats?.avg_confidence || 0.95) * 100) }}%
        </p>
      </div>
    </div>

    <!-- Category Distribution & Proportion Bar -->
    <div class="bg-surface rounded-xl p-5 border border-border shadow-xs space-y-3.5">
      <div class="flex items-center justify-between pb-2.5 border-b border-border-subtle">
        <div>
          <h3 class="text-xs font-semibold uppercase font-mono tracking-wider text-ink-secondary">Category Distribution</h3>
          <p class="text-xs text-ink-muted mt-0.5">Classification breakdown across active inbox emails</p>
        </div>
        <button
          @click="$emit('navigate', 'analytics')"
          class="text-xs font-medium text-brand hover:text-brand-hover transition-colors"
        >
          View Full Audit &rarr;
        </button>
      </div>

      <div v-if="!stats?.categories || Object.keys(stats.categories).length === 0" class="py-6 text-center text-xs text-ink-muted font-mono">
        No email classifications recorded yet.
      </div>

      <div v-else class="space-y-3">
        <!-- Segmented Visual Proportion Bar -->
        <div class="w-full h-2 rounded-full bg-canvas-muted overflow-hidden flex">
          <div
            v-for="(count, cat) in stats.categories"
            :key="cat"
            class="h-full transition-all duration-300 first:rounded-l-full last:rounded-r-full"
            :style="{
              width: `${getCategoryPercent(count)}%`,
              backgroundColor: getCategoryColor(cat)
            }"
            :title="`${cat}: ${count} (${getCategoryPercent(count)}%)`"
          ></div>
        </div>

        <!-- Interactive Category Chips -->
        <div class="flex flex-wrap gap-2 pt-1">
          <button
            v-for="(count, cat) in stats.categories"
            :key="cat"
            @click="$emit('navigate', 'inbox', cat)"
            class="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-canvas-subtle hover:bg-canvas-muted border border-border-subtle hover:border-border text-xs transition-colors group cursor-pointer"
            :title="`Filter inbox by ${cat}`"
          >
            <span class="w-2 h-2 rounded-full shrink-0" :style="{ backgroundColor: getCategoryColor(cat) }"></span>
            <span class="font-medium text-ink capitalize">{{ cat }}</span>
            <span class="font-mono text-ink-muted text-[11px] font-semibold">{{ count }}</span>
            <span class="text-[10px] font-mono text-ink-muted/70">({{ getCategoryPercent(count) }}%)</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Recent Intelligence Activity -->
    <div class="bg-surface rounded-xl border border-border shadow-xs overflow-hidden">
      <div class="p-4 sm:p-5 border-b border-border-subtle flex items-center justify-between">
        <div>
          <h3 class="text-xs font-semibold uppercase font-mono tracking-wider text-ink-secondary">Recent Intelligence Stream</h3>
          <p class="text-xs text-ink-muted mt-0.5">Latest emails classified by deterministic rules and Gemini 2.5 Flash</p>
        </div>
        <button
          @click="$emit('navigate', 'inbox')"
          class="text-xs font-medium text-brand hover:text-brand-hover transition-colors"
        >
          View Processed Inbox &rarr;
        </button>
      </div>

      <div v-if="!recentEmails || recentEmails.length === 0" class="py-12 text-center text-xs text-ink-muted font-mono">
        No recent emails discovered.
      </div>

      <div v-else class="divide-y divide-border-subtle">
        <div
          v-for="email in recentEmails.slice(0, 7)"
          :key="email.message_id"
          @click="$emit('select-email', email)"
          class="px-4 py-3 sm:px-5 sm:py-3.5 flex items-center justify-between gap-4 hover:bg-canvas-subtle/70 cursor-pointer transition-colors group"
        >
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <span
              :class="['w-2 h-2 rounded-full shrink-0', priorityDotClass(email.priority)]"
              :title="`${email.priority || 'normal'} priority`"
            ></span>
            
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-ink truncate group-hover:text-brand transition-colors">
                  {{ email.subject || '(no subject)' }}
                </span>
                <span
                  v-if="email.status === 'review'"
                  class="px-1.5 py-0.2 text-[10px] font-mono bg-amber-50 text-amber-800 rounded border border-amber-200 shrink-0 font-medium"
                >
                  Review
                </span>
              </div>
              <p class="text-[11px] font-mono text-ink-muted truncate mt-0.5">
                {{ email.sender_email || email.sender || 'Unknown Sender' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-3 shrink-0">
            <span :class="['px-2 py-0.5 text-[11px] font-semibold rounded border uppercase tracking-wider font-mono', categoryBadgeClass(email.category)]">
              {{ email.category }}
            </span>

            <span class="text-xs font-mono text-ink-muted hidden sm:inline w-11 text-right">
              {{ Math.round((email.confidence || 0) * 100) }}%
            </span>

            <span class="text-xs font-mono text-ink-muted w-14 text-right">
              {{ formatTime(email.updated_at || email.email_timestamp) }}
            </span>

            <svg class="w-4 h-4 text-ink-muted/50 group-hover:text-brand group-hover:translate-x-0.5 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({})
  },
  recentEmails: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['navigate', 'select-email', 'refresh'])

const isScanning = ref(false)

const triggerScan = async () => {
  if (isScanning.value) return
  isScanning.value = true
  try {
    const res = await fetch('/api/scan', { method: 'POST' })
    if (res.ok) {
      setTimeout(() => {
        emit('refresh')
        isScanning.value = false
      }, 2500)
    } else {
      isScanning.value = false
    }
  } catch (err) {
    console.error(err)
    isScanning.value = false
  }
}

const totalCategoryCount = computed(() => {
  if (!props.stats?.categories) return 0
  return Object.values(props.stats.categories).reduce((acc, curr) => acc + (curr || 0), 0)
})

const getCategoryPercent = (count) => {
  const total = totalCategoryCount.value
  if (!total) return 0
  return Math.round((count / total) * 100)
}

const getCategoryColor = (cat) => {
  const c = (cat || '').toLowerCase()
  if (c === 'work') return '#4338ca'      // Indigo
  if (c === 'urgent') return '#dc2626'    // Red
  if (c === 'academic') return '#0d9488'  // Teal
  if (c === 'meeting') return '#7c3aed'   // Purple
  if (c === 'promotional') return '#64748b' // Slate
  if (c === 'spam') return '#ea580c'      // Orange
  return '#94a3b8'
}

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const formatRelative = (ts) => {
  if (!ts) return 'recently'
  const d = new Date(ts)
  const diffSec = Math.round((Date.now() - d.getTime()) / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  return `${Math.floor(diffSec / 3600)}h ago`
}

const priorityDotClass = (prio) => {
  const p = (prio || '').toLowerCase()
  if (p === 'high') return 'bg-rose-500'
  if (p === 'medium') return 'bg-brand'
  return 'bg-gray-300'
}

const categoryBadgeClass = (cat) => {
  const c = (cat || '').toLowerCase()
  if (c === 'urgent') return 'bg-rose-50 text-rose-800 border-rose-200'
  if (c === 'work') return 'bg-indigo-50 text-indigo-800 border-indigo-200'
  if (c === 'academic') return 'bg-teal-50 text-teal-800 border-teal-200'
  if (c === 'meeting') return 'bg-purple-50 text-purple-800 border-purple-200'
  if (c === 'promotional') return 'bg-slate-50 text-slate-700 border-slate-200'
  if (c === 'spam') return 'bg-orange-50 text-orange-800 border-orange-200'
  return 'bg-gray-50 text-gray-700 border-gray-200'
}
</script>
