<template>
  <div class="space-y-6 animate-fade pb-12">

    <!-- Header & Search Controls -->
    <div class="bg-surface p-4 sm:p-5 rounded-xl border border-border shadow-xs space-y-4">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 class="text-base sm:text-lg font-semibold text-ink font-serif tracking-tight">Processed Emails</h2>
          <p class="text-xs text-ink-muted mt-0.5">Automated classifications and applied actions across your inbox.</p>
        </div>

        <div class="flex items-center gap-3 w-full sm:w-auto">
          <!-- Search Input -->
          <div class="relative flex-1 sm:w-72">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              id="inbox-search"
              v-model="searchQuery"
              type="text"
              aria-label="Search emails by subject, sender, or reason"
              placeholder="Search subject, sender, reason..."
              class="w-full pl-9 pr-3 py-1.5 text-xs bg-canvas-subtle border border-border rounded-lg text-ink focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand transition-all"
            />
          </div>

          <!-- Sort Select -->
          <select
            v-model="sortBy"
            aria-label="Sort email results"
            class="text-xs px-3 py-1.5 bg-canvas-subtle border border-border rounded-lg text-ink font-medium focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand shrink-0"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="conf_high">Highest Confidence</option>
            <option value="conf_low">Lowest Confidence</option>
          </select>
        </div>
      </div>

      <!-- Filter Pills: Categories & Priorities -->
      <div class="pt-2 border-t border-border-subtle flex flex-wrap items-center justify-between gap-3">
        <!-- Categories -->
        <div class="flex flex-wrap items-center gap-1.5">
          <span class="text-[11px] text-ink-muted uppercase font-mono mr-1">Category:</span>
          <button
            v-for="cat in categories"
            :key="cat.id"
            @click="activeCategory = cat.id"
            :class="[
              'px-2.5 py-1 text-xs rounded-lg transition-all font-medium',
              activeCategory === cat.id
                ? 'bg-ink text-surface shadow-subtle'
                : 'bg-canvas-subtle text-ink-secondary hover:text-ink hover:bg-canvas-muted'
            ]"
          >
            {{ cat.label }}
          </button>
        </div>

        <!-- Priority Filters -->
        <div class="flex items-center gap-1.5">
          <span class="text-[11px] text-ink-muted uppercase font-mono mr-1">Priority:</span>
          <button
            v-for="prio in priorities"
            :key="prio.id"
            @click="activePriority = prio.id"
            :class="[
              'px-2 py-0.5 text-xs rounded-md transition-all font-mono',
              activePriority === prio.id
                ? 'bg-brand text-surface font-semibold'
                : 'text-ink-secondary hover:bg-canvas-muted'
            ]"
          >
            {{ prio.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Email List Table -->
    <div class="bg-surface rounded-xl border border-border shadow-xs overflow-hidden">
      
      <!-- Table Header -->
      <div class="bg-canvas-subtle px-5 py-3 border-b border-border flex items-center justify-between text-[11px] font-mono text-ink-muted uppercase tracking-wider">
        <div class="flex items-center gap-4 flex-1">
          <span class="w-2"></span>
          <span class="w-28">Category</span>
          <span class="flex-1">Subject & Sender</span>
        </div>
        <div class="flex items-center gap-6 shrink-0">
          <span class="w-28 text-left hidden md:inline">Executed Action</span>
          <span class="w-16 text-right">Confidence</span>
          <span class="w-16 text-right">Date</span>
          <span class="w-4"></span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="p-8 space-y-3">
        <div v-for="i in 5" :key="i" class="h-12 bg-canvas-muted rounded-xl animate-pulse"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredEmails.length === 0" class="py-20 text-center space-y-3">
        <div class="w-12 h-12 rounded-xl bg-canvas-muted flex items-center justify-center text-ink-muted mx-auto">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
        </div>
        <h4 class="text-sm font-semibold text-ink">No matching emails found</h4>
        <p class="text-xs text-ink-muted max-w-sm mx-auto">Try adjusting your category, priority, or search query to find the emails you are looking for.</p>
        <button
          v-if="hasActiveFilters"
          @click="resetFilters"
          class="px-3.5 py-1.5 text-xs font-semibold text-brand hover:underline"
        >
          Clear all filters
        </button>
      </div>

      <!-- Rows -->
      <div v-else class="divide-y divide-border-subtle">
        <div
          v-for="email in paginatedEmails"
          :key="email.message_id"
          @click="$emit('select-email', email)"
          class="px-5 py-3.5 flex items-center justify-between gap-4 hover:bg-canvas-subtle cursor-pointer transition-colors group"
        >
          <!-- Left: Priority & Category & Subject -->
          <div class="flex items-center gap-4 min-w-0 flex-1">
            <span :class="['w-2 h-2 rounded-full shrink-0', priorityDotClass(email.priority)]" :title="`${email.priority} priority`"></span>

            <span :class="['w-28 shrink-0 px-2.5 py-0.5 text-xs font-semibold rounded-md border uppercase tracking-wider truncate text-center', categoryBadgeClass(email.category)]">
              {{ email.category }}
            </span>

            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="text-xs font-semibold text-ink truncate group-hover:text-brand transition-colors">
                  {{ email.subject || '(no subject)' }}
                </span>
                <span v-if="email.status === 'review'" class="px-1.5 py-0.2 text-[10px] font-mono bg-status-warningBg text-status-warning rounded border border-status-warningBorder">
                  Review
                </span>
              </div>
              <p class="text-xs text-ink-secondary truncate mt-0.5">
                {{ email.sender_email || email.sender || 'Unknown Sender' }}
              </p>
            </div>
          </div>

          <!-- Right: Action & Confidence & Date -->
          <div class="flex items-center gap-6 shrink-0">
            <div class="w-28 text-left hidden md:block truncate">
              <span class="text-xs font-mono text-ink-secondary bg-canvas-muted px-2 py-0.5 rounded border border-border">
                {{ email.actions ? email.actions.split(',')[0] : 'In Inbox' }}
              </span>
            </div>

            <div class="w-16 text-right">
              <span :class="['text-xs font-mono px-2 py-0.5 rounded border', confidenceClass(email.confidence)]">
                {{ Math.round((email.confidence || 0) * 100) }}%
              </span>
            </div>

            <span class="w-16 text-right text-xs font-mono text-ink-muted">
              {{ formatRelativeTime(email.updated_at || email.email_timestamp) }}
            </span>

            <svg class="w-4 h-4 text-ink-muted group-hover:text-brand group-hover:translate-x-0.5 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Pagination Footer -->
      <div v-if="totalPages > 1" class="px-5 py-3 border-t border-border-subtle bg-canvas-subtle/50 flex items-center justify-between text-xs">
        <span class="text-ink-muted font-mono">
          Showing {{ ((currentPage - 1) * itemsPerPage) + 1 }} - {{ Math.min(currentPage * itemsPerPage, filteredEmails.length) }} of {{ filteredEmails.length }}
        </span>

        <div class="flex items-center gap-1.5">
          <button
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="px-2.5 py-1 rounded bg-surface border border-border text-ink disabled:opacity-30 disabled:cursor-not-allowed hover:bg-canvas-muted transition-colors font-mono"
          >
            Prev
          </button>
          <span class="px-2 font-mono text-ink-secondary">{{ currentPage }} / {{ totalPages }}</span>
          <button
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="px-2.5 py-1 rounded bg-surface border border-border text-ink disabled:opacity-30 disabled:cursor-not-allowed hover:bg-canvas-muted transition-colors font-mono"
          >
            Next
          </button>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  emails: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  initialCategory: {
    type: String,
    default: 'all'
  }
})

defineEmits(['select-email'])

const searchQuery = ref('')
const activeCategory = ref(props.initialCategory || 'all')
const activePriority = ref('all')
const sortBy = ref('newest')
const currentPage = ref(1)
const itemsPerPage = 12

watch(() => props.initialCategory, (newVal) => {
  if (newVal) activeCategory.value = newVal.toLowerCase()
})

const categories = [
  { id: 'all', label: 'All' },
  { id: 'urgent', label: 'Urgent' },
  { id: 'work', label: 'Work' },
  { id: 'academic', label: 'Academic' },
  { id: 'meeting', label: 'Meeting' },
  { id: 'important', label: 'Important' },
  { id: 'promotional', label: 'Promotional' },
  { id: 'spam', label: 'Spam' },
  { id: 'normal', label: 'Normal' },
]

const priorities = [
  { id: 'all', label: 'All' },
  { id: 'high', label: 'High' },
  { id: 'medium', label: 'Medium' },
  { id: 'low', label: 'Low' },
]

const hasActiveFilters = computed(() => {
  return searchQuery.value || activeCategory.value !== 'all' || activePriority.value !== 'all'
})

const resetFilters = () => {
  searchQuery.value = ''
  activeCategory.value = 'all'
  activePriority.value = 'all'
}

const filteredEmails = computed(() => {
  let result = [...props.emails]

  // Category filter
  if (activeCategory.value !== 'all') {
    result = result.filter(e => (e.category || '').toLowerCase() === activeCategory.value)
  }

  // Priority filter
  if (activePriority.value !== 'all') {
    result = result.filter(e => (e.priority || '').toLowerCase() === activePriority.value)
  }

  // Search query
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    result = result.filter(e =>
      (e.subject && e.subject.toLowerCase().includes(q)) ||
      (e.sender_email && e.sender_email.toLowerCase().includes(q)) ||
      (e.category && e.category.toLowerCase().includes(q)) ||
      (e.reason && e.reason.toLowerCase().includes(q))
    )
  }

  // Sorting
  if (sortBy.value === 'newest') {
    result.sort((a, b) => new Date(b.updated_at || b.email_timestamp || 0) - new Date(a.updated_at || a.email_timestamp || 0))
  } else if (sortBy.value === 'oldest') {
    result.sort((a, b) => new Date(a.updated_at || a.email_timestamp || 0) - new Date(b.updated_at || b.email_timestamp || 0))
  } else if (sortBy.value === 'conf_high') {
    result.sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
  } else if (sortBy.value === 'conf_low') {
    result.sort((a, b) => (a.confidence || 0) - (b.confidence || 0))
  }

  return result
})

const totalPages = computed(() => Math.ceil(filteredEmails.value.length / itemsPerPage) || 1)

const paginatedEmails = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredEmails.value.slice(start, start + itemsPerPage)
})

watch([searchQuery, activeCategory, activePriority, sortBy], () => {
  currentPage.value = 1
})

const formatRelativeTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const priorityDotClass = (prio) => {
  const p = (prio || '').toLowerCase()
  if (p === 'high') return 'bg-status-danger'
  if (p === 'medium') return 'bg-brand'
  return 'bg-ink-faint'
}

const confidenceClass = (conf) => {
  const val = conf || 0
  if (val >= 0.85) return 'bg-status-successBg text-status-success border-status-successBorder'
  if (val >= 0.60) return 'bg-status-warningBg text-status-warning border-status-warningBorder'
  return 'bg-status-dangerBg text-status-danger border-status-dangerBorder'
}

const categoryBadgeClass = (cat) => {
  const c = (cat || '').toLowerCase()
  if (c === 'urgent') return 'bg-[#fef2f2] text-[#991b1b] border-[#fecaca]'
  if (c === 'work') return 'bg-[#eef2ff] text-[#3730a3] border-[#c7d2fe]'
  if (c === 'academic') return 'bg-[#ecfeff] text-[#0e7490] border-[#a5f3fc]'
  if (c === 'meeting') return 'bg-[#faf5ff] text-[#6b21a8] border-[#e9d5ff]'
  if (c === 'promotional') return 'bg-[#f8fafc] text-[#475569] border-[#e2e8f0]'
  if (c === 'spam') return 'bg-[#fff7ed] text-[#c2410c] border-[#fed7aa]'
  return 'bg-[#f4f4f5] text-[#52525b] border-[#e4e4e7]'
}
</script>
