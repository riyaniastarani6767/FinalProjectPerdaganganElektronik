// Tooltip bersama untuk semua grafik.
// Pakai: v-tip="'teks'" atau v-tip="['Judul', 'baris 1', 'baris 2']" pada elemen HTML maupun SVG.
// Laptop: muncul saat kursor di atas elemen. HP: muncul saat elemen diketuk. Hilang saat halaman di-scroll.
import { reactive } from 'vue'

export const tip = reactive({ tampil: false, judul: '', baris: [], x: 0, y: 0 })

function isi(nilai) {
  const arr = Array.isArray(nilai) ? nilai : [nilai]
  tip.judul = arr[0] ?? ''
  tip.baris = arr.slice(1)
}

function posisi(x, y) {
  tip.x = x
  tip.y = y
}

export function sembunyikan() {
  tip.tampil = false
}

export const vTip = {
  mounted(el, binding) {
    el._tip = binding.value
    el.style.cursor = 'pointer'
    el._masuk = (e) => { isi(el._tip); posisi(e.clientX, e.clientY); tip.tampil = true }
    el._gerak = (e) => posisi(e.clientX, e.clientY)
    el._ketuk = (e) => {
      const t = e.touches?.[0]
      const r = el.getBoundingClientRect()
      isi(el._tip)
      posisi(t ? t.clientX : r.left + r.width / 2, t ? t.clientY : r.top)
      tip.tampil = true
    }
    el.addEventListener('mouseenter', el._masuk)
    el.addEventListener('mousemove', el._gerak)
    el.addEventListener('mouseleave', sembunyikan)
    el.addEventListener('touchstart', el._ketuk, { passive: true })
  },
  updated(el, binding) {
    el._tip = binding.value
  },
  unmounted(el) {
    el.removeEventListener('mouseenter', el._masuk)
    el.removeEventListener('mousemove', el._gerak)
    el.removeEventListener('mouseleave', sembunyikan)
    el.removeEventListener('touchstart', el._ketuk)
    sembunyikan()
  }
}

// tooltip ditutup saat halaman di-scroll agar tidak tertinggal di posisi lama
window.addEventListener('scroll', sembunyikan, { passive: true })
