<script setup>
// Kotak keterangan yang mengikuti kursor (dipasang sekali di App.vue)
import { computed } from 'vue'
import { tip } from '../tooltip'

const gaya = computed(() => {
  const lebar = 260
  const kanan = tip.x + 14 + lebar > window.innerWidth
  return { left: (kanan ? tip.x - 14 - lebar : tip.x + 14) + 'px', top: Math.max(8, tip.y - 12) + 'px', maxWidth: lebar + 'px' }
})
</script>

<template>
  <div v-show="tip.tampil" role="tooltip" :style="gaya"
    class="fixed z-50 pointer-events-none bg-teks text-white rounded-lg px-3 py-2 text-xs leading-relaxed shadow-lg print:hidden">
    <strong class="block text-[12.5px] font-semibold">{{ tip.judul }}</strong>
    <span v-for="(b, i) in tip.baris" :key="i" class="block text-white/80">{{ b }}</span>
  </div>
</template>
