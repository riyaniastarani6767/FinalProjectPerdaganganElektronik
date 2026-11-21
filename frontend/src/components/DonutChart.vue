<script setup>
import { computed } from 'vue'
const props = defineProps({
  segments: { type: Array, required: true },  // [{ label, value, color }]
  center: { type: String, default: '' },
  sub: { type: String, default: '' }
})
const C = 2 * Math.PI * 60
const busur = computed(() => {
  const total = props.segments.reduce((a, s) => a + s.value, 0) || 1
  let offset = 0
  return props.segments.map((s) => {
    const len = (s.value / total) * C
    const r = { ...s, dash: `${len} ${C}`, offset: -offset }
    offset += len
    return r
  })
})
</script>

<template>
  <svg viewBox="0 0 160 160" class="w-[170px] h-[170px]" role="img" :aria-label="segments.map((s) => s.label).join(', ')">
    <g transform="rotate(-90 80 80)" fill="none" stroke-width="24">
      <circle v-for="b in busur" :key="b.label" cx="80" cy="80" r="60" :stroke="b.color" :stroke-dasharray="b.dash" :stroke-dashoffset="b.offset">
        <title>{{ b.label }}</title>
      </circle>
    </g>
    <text x="80" y="78" text-anchor="middle" font-size="22" font-weight="700" fill="#1F1D2B">{{ center }}</text>
    <text x="80" y="97" text-anchor="middle" font-size="11" fill="#6B6880">{{ sub }}</text>
  </svg>
</template>
