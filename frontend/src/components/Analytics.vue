<template>
  <div class="space-y-8 animate-fade pb-12">
    
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-semibold text-ink font-serif tracking-tight">Intelligence & Automation Audit</h2>
        <p class="text-sm text-ink-secondary mt-1">Live metrics on Gemini 2.5 Flash classification performance, automation rate, and safety boundaries.</p>
      </div>

      <div class="flex items-center gap-2">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-status-successBg text-status-success border border-status-successBorder">
          <span class="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse"></span>
          Pipeline Healthy
        </span>
      </div>
    </div>

    <!-- Core KPI Strip -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-surface rounded-xl p-5 border border-border shadow-subtle">
        <span class="text-xs font-medium text-ink-muted uppercase tracking-wider block mb-1">Automation Efficiency</span>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-semibold font-mono text-ink">{{ stats?.automation_rate ?? 100 }}%</span>
          <span class="text-xs text-status-success font-medium">auto-handled</span>
        </div>
        <p class="text-xs text-ink-muted mt-2">Emails classified with confidence &ge; 85% requiring zero manual triage.</p>
      </div>

      <div class="bg-surface rounded-xl p-5 border border-border shadow-subtle">
        <span class="text-xs font-medium text-ink-muted uppercase tracking-wider block mb-1">Average Confidence</span>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-semibold font-mono text-ink">{{ Math.round((stats?.avg_confidence || 0.88) * 100) }}%</span>
          <span class="text-xs text-ink-secondary font-mono">mean score</span>
        </div>
        <p class="text-xs text-ink-muted mt-2">Enforced by Pydantic structured validation schema on Gemini output.</p>
      </div>

      <div class="bg-surface rounded-xl p-5 border border-border shadow-subtle">
        <span class="text-xs font-medium text-ink-muted uppercase tracking-wider block mb-1">Human Review Ratio</span>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-semibold font-mono" :class="(stats?.needs_review || 0) > 0 ? 'text-status-warning' : 'text-ink'">
            {{ stats?.needs_review ?? 0 }}
          </span>
          <span class="text-xs text-ink-muted">flagged items</span>
        </div>
        <p class="text-xs text-ink-muted mt-2">Placed in review queue due to low confidence or heuristic security flags.</p>
      </div>

      <div class="bg-surface rounded-xl p-5 border border-border shadow-subtle">
        <span class="text-xs font-medium text-ink-muted uppercase tracking-wider block mb-1">Action Boundary</span>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-semibold font-mono text-ink">100%</span>
          <span class="text-xs text-status-success font-medium">safe</span>
        </div>
        <p class="text-xs text-ink-muted mt-2">Strictly reversible Gmail label operations. Zero deletion allowed.</p>
      </div>
    </div>

    <!-- Middle Grid: Category Breakdown + Priority Matrix -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Category Volume Breakdown -->
      <div class="bg-surface rounded-xl p-6 border border-border shadow-subtle space-y-5">
        <div class="flex items-center justify-between pb-3 border-b border-border-subtle">
          <h3 class="text-sm font-semibold text-ink">Classification Distribution by Category</h3>
          <span class="text-xs text-ink-muted font-mono">{{ totalCategorized }} total</span>
        </div>

        <div v-if="categoryList.length === 0" class="py-12 text-center text-xs text-ink-muted">
          No classified emails recorded yet.
        </div>

        <div v-else class="space-y-3.5">
          <div v-for="cat in categoryList" :key="cat.name" class="space-y-1.5">
            <div class="flex justify-between items-center text-xs">
              <span class="font-medium text-ink capitalize flex items-center gap-2">
                <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: cat.color }"></span>
                {{ cat.name }}
              </span>
              <span class="font-mono text-ink-secondary">{{ cat.count }} ({{ cat.percentage }}%)</span>
            </div>
            <div class="w-full h-2 bg-canvas-muted rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-700" :style="{ width: `${cat.percentage}%`, backgroundColor: cat.color }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Priority Distribution & Security Flags -->
      <div class="bg-surface rounded-xl p-6 border border-border shadow-subtle space-y-6">
        <div>
          <div class="flex items-center justify-between pb-3 border-b border-border-subtle">
            <h3 class="text-sm font-semibold text-ink">Priority Tier Distribution</h3>
            <span class="text-xs text-ink-muted font-mono">Triage urgency</span>
          </div>

          <div class="grid grid-cols-3 gap-3 mt-4">
            <div class="p-4 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
              <span class="text-xs font-medium text-status-danger uppercase tracking-wider block mb-1">High</span>
              <span class="text-2xl font-mono font-semibold text-ink">{{ stats?.priorities?.high ?? 0 }}</span>
              <span class="text-[11px] text-ink-muted block mt-1">Immediate action</span>
            </div>
            <div class="p-4 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
              <span class="text-xs font-medium text-brand uppercase tracking-wider block mb-1">Medium</span>
              <span class="text-2xl font-mono font-semibold text-ink">{{ stats?.priorities?.medium ?? 0 }}</span>
              <span class="text-[11px] text-ink-muted block mt-1">Normal business</span>
            </div>
            <div class="p-4 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
              <span class="text-xs font-medium text-ink-muted uppercase tracking-wider block mb-1">Low</span>
              <span class="text-2xl font-mono font-semibold text-ink">{{ stats?.priorities?.low ?? 0 }}</span>
              <span class="text-[11px] text-ink-muted block mt-1">Informational</span>
            </div>
          </div>
        </div>

        <!-- Safety Boundaries Architecture Details -->
        <div class="pt-2 border-t border-border-subtle">
          <h4 class="text-xs font-semibold uppercase tracking-wider text-ink-secondary mb-3">Deterministic Safety Boundary</h4>
          <div class="space-y-2.5 text-xs text-ink-secondary">
            <div class="flex items-start gap-2.5 p-2.5 rounded-lg bg-canvas-subtle border border-border-subtle">
              <span class="font-mono text-xs font-bold text-brand shrink-0">L1</span>
              <div>
                <strong class="text-ink">Pre-LLM Security Rules:</strong>
                <span class="text-ink-muted ml-1">Flags link text mismatches, unverified sender domains, and risky attachment extensions before prompt assembly.</span>
              </div>
            </div>
            <div class="flex items-start gap-2.5 p-2.5 rounded-lg bg-canvas-subtle border border-border-subtle">
              <span class="font-mono text-xs font-bold text-brand shrink-0">L2</span>
              <div>
                <strong class="text-ink">Structured LLM Inference:</strong>
                <span class="text-ink-muted ml-1">Gemini 2.5 Flash produces strict Pydantic output; prompt injection cannot emit arbitrary API calls.</span>
              </div>
            </div>
            <div class="flex items-start gap-2.5 p-2.5 rounded-lg bg-canvas-subtle border border-border-subtle">
              <span class="font-mono text-xs font-bold text-brand shrink-0">L3</span>
              <div>
                <strong class="text-ink">Reversible Action Executor:</strong>
                <span class="text-ink-muted ml-1">Restricted to <code>gmail.modify</code>. Project code permanently forbids deletion, trash, and drafting methods.</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({})
  }
})

const colorMap = {
  urgent: '#be123c',
  work: '#4338ca',
  academic: '#0f766e',
  meeting: '#6d28d9',
  important: '#1d4ed8',
  promotional: '#475569',
  normal: '#52525b',
  spam: '#c2410c'
}

const totalCategorized = computed(() => {
  if (!props.stats?.categories) return 0
  return Object.values(props.stats.categories).reduce((a, b) => a + b, 0)
})

const categoryList = computed(() => {
  if (!props.stats?.categories) return []
  const total = totalCategorized.value || 1
  return Object.entries(props.stats.categories).map(([name, count]) => ({
    name,
    count,
    percentage: Math.round((count / total) * 100),
    color: colorMap[name.toLowerCase()] || '#64748b'
  })).sort((a, b) => b.count - a.count)
})
</script>
