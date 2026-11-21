<script setup>
// Layout utama: header di atas, sidebar 4 menu di kiri, isi halaman di tengah
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { store } from './api'

const route = useRoute()
const aktif = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
const menu = [
  { to: '/', label: 'Dashboard', icon: 'M4 15a8 8 0 0 1 16 0 M12 15l3.5-4 M3 18h18' },
  { to: '/unggah', label: 'Unggah Data', icon: 'M12 15V4 M7.5 8.5L12 4l4.5 4.5 M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4' },
  { to: '/prediksi', label: 'Prediksi', icon: 'M3 3v18h18 M6 16l4-5 3 3 5-7' },
  { to: '/evaluasi', label: 'Evaluasi', icon: 'M3 21h18 M5 12h3v6H5z M10.5 8h3v10h-3z M16 4h3v14h-3z' }
]

onMounted(() => store.muatStatus())
</script>

<template>
  <div class="min-h-screen flex flex-col">
  <header class="flex flex-wrap items-center justify-between gap-4 px-4 md:px-8 py-3 bg-white border-b-2 border-ungu print:hidden">
    <span class="min-h-[40px] inline-flex items-center px-3 border border-ungu rounded text-ungu text-sm">
      Data aktif: {{ store.dataset?.nama_file || 'memuat...' }}
    </span>
    <RouterLink to="/" class="text-[26px] tracking-wide text-teks">Hotel<strong>Guard</strong><span class="text-ungu font-bold">.</span></RouterLink>
    <span class="text-sm text-teks-sedang hidden sm:inline">Kelompok 3 · PEIB</span>
  </header>
    <div class="flex-1 flex flex-col md:flex-row">
  <nav aria-label="Menu utama" class="md:w-[132px] shrink-0 bg-[#F7F7F9] border-b md:border-b-0 md:border-r border-garis flex md:flex-col overflow-x-auto print:hidden">
    <RouterLink v-for="m in menu" :key="m.to" :to="m.to"
      class="relative flex flex-col items-center justify-center gap-2 min-h-[88px] md:min-h-[120px] min-w-[96px] px-2 border-r md:border-r-0 md:border-b border-garis text-sm text-center text-teks font-medium"
      :class="aktif(m.to) ? '!text-ungu bg-white font-semibold' : ''">
      <span class="absolute left-0 top-0 bottom-0 w-1 rounded-r" :class="aktif(m.to) ? 'bg-ungu' : ''"></span>
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path :d="m.icon" />
      </svg>
      {{ m.label }}
    </RouterLink>
  </nav>
      <main class="flex-1 min-w-0 bg-latar px-4 md:px-10 py-8 flex flex-col gap-5">
        <RouterView />
      </main>
    </div>
  </div>
</template>
