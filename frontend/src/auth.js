// Login sederhana untuk demo: satu akun tetap untuk kelompok.
// Catatan: pengecekan dilakukan di browser, jadi ini hanya pembatas tampilan, bukan pengamanan sungguhan.
import { reactive } from 'vue'

// Ganti username dan password di sini jika perlu
export const AKUN = { username: 'ayu', password: 'peib2026' }

const KUNCI = 'hotelguard_masuk'

function bacaStatus() {
  try { return localStorage.getItem(KUNCI) === '1' } catch { return false }
}

export const auth = reactive({ masuk: bacaStatus() })

export function login(username, password) {
  if (username.trim() !== AKUN.username || password !== AKUN.password) return false
  auth.masuk = true
  try { localStorage.setItem(KUNCI, '1') } catch { /* status hanya tersimpan selama tab terbuka */ }
  return true
}

export function logout() {
  auth.masuk = false
  try { localStorage.removeItem(KUNCI) } catch { /* abaikan */ }
}
