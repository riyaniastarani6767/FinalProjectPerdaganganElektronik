<script setup>
// Layout utama: sidebar gelap di kiri, bar sapaan di atas, isi halaman di kanan
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { NAMA_PENGGUNA, store } from './api'
import Tooltip from './components/Tooltip.vue'
import { logout } from './auth'

const route = useRoute()
const aktif = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))
const menu = [
  { to: '/', label: 'Dashboard', icon: 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z' },
  { to: '/unggah', label: 'Unggah Data', icon: 'M12 15V4M7.5 8.5L12 4l4.5 4.5M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4' },
  { to: '/prediksi', label: 'Prediksi', icon: 'M3 3v18h18M7 15l4-5 3 3 5-7' }
]
const tanggal = new Date().toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

// Penanda menu aktif yang bergeser halus ke menu yang dipilih
const navEl = ref(null)
const penanda = ref({ opacity: 0 })
function geserPenanda() {
  const el = navEl.value?.querySelector('[data-aktif="true"]')
  if (!el) return
  penanda.value = { opacity: 1, width: el.offsetWidth + 'px', height: el.offsetHeight + 'px', transform: `translate(${el.offsetLeft}px, ${el.offsetTop}px)` }
}
watch(() => route.path, () => nextTick(geserPenanda))
onMounted(() => {
  store.muatStatus()
  nextTick(geserPenanda)
  window.addEventListener('resize', geserPenanda)
})
onBeforeUnmount(() => window.removeEventListener('resize', geserPenanda))

// Keluar: hapus status masuk lalu muat ulang ke halaman login agar isian dan hasil di semua halaman ikut terhapus
function keluar() {
  logout()
  window.location.href = '/login'
}
</script>

<template>
  <RouterView v-if="route.meta.publik" />
  <div v-else class="min-h-screen flex flex-col md:flex-row gap-4 md:gap-5 p-3 md:p-4">
    <!-- Sidebar -->
    <aside class="md:w-[220px] shrink-0 bg-ungu-gelap text-white rounded-[18px] p-3 md:px-4 md:py-5 flex md:flex-col gap-3
                  md:sticky md:top-4 md:h-[calc(100vh-32px)] md:overflow-y-auto items-center md:items-stretch print:hidden">

      <nav ref="navEl" aria-label="Menu utama" class="relative w-full md:w-auto grid grid-cols-3 md:flex md:flex-col gap-1">
        <span aria-hidden="true" class="absolute left-0 top-0 rounded-[10px] bg-white shadow-sm pointer-events-none transition-[transform,width,height,opacity] duration-300 ease-out" :style="penanda"></span>
        <RouterLink v-for="m in menu" :key="m.to" :to="m.to" :data-aktif="aktif(m.to)"
          class="relative z-10 flex items-center justify-center md:justify-start gap-1.5 md:gap-3 px-2 md:px-3.5 py-2.5 rounded-[10px] text-[12.5px] md:text-[13.5px] font-medium whitespace-nowrap transition-colors duration-300"
          :class="aktif(m.to) ? 'text-ungu-gelap font-semibold' : 'text-white/75 hover:bg-white/10 hover:text-white'">
          <svg class="w-[18px] h-[18px] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="m.icon" /></svg>
          {{ m.label }}
        </RouterLink>
      </nav>

      <button type="button" class="hidden md:flex md:mt-auto shrink-0 items-center gap-3 px-3.5 py-2.5 rounded-[10px] text-[13.5px] font-medium text-white/75 hover:bg-white/10 hover:text-white transition-colors" @click="keluar">
        <svg class="w-[18px] h-[18px] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" /></svg>
        <span class="hidden md:inline">Keluar</span>
      </button>
    </aside>

    <!-- Isi -->
    <div class="flex-1 min-w-0 flex flex-col gap-4">
      <header class="bg-white rounded-[14px] px-5 md:px-6 py-4 flex flex-wrap items-center justify-between gap-3 print:hidden">
        <div>
          <h1 class="text-xl font-bold">Selamat datang, {{ NAMA_PENGGUNA }}</h1>
          <p class="text-[12.5px] text-teks-redup mt-0.5 capitalize">{{ tanggal }}</p>
        </div>
        <button type="button" class="md:hidden btn-garis min-h-[36px] px-3.5" @click="keluar">Keluar</button>
      </header>
      <main class="min-w-0">
        <!-- halaman disimpan (KeepAlive) agar isian dan data tidak hilang saat pindah menu -->
        <RouterView v-slot="{ Component }">
          <Transition name="halaman" mode="out-in">
            <KeepAlive><component :is="Component" /></KeepAlive>
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
  <Tooltip />
</template>
