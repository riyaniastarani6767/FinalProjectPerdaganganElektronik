<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const lihat = ref(false)
const error = ref('')

function masuk() {
  error.value = ''
  if (login(username.value, password.value)) router.replace('/')
  else error.value = 'Username atau password salah.'
}
const isian = 'min-h-[44px] w-full border border-garis rounded-[10px] px-3 text-sm text-teks bg-white focus:outline-none focus:border-ungu'
</script>

<template>
  <div class="min-h-screen grid place-items-center p-4 bg-latar">
    <form class="w-full max-w-[380px] bg-white rounded-[18px] p-7 flex flex-col gap-5 shadow-sm" @submit.prevent="masuk">
      <div class="flex flex-col items-center gap-3 text-center">
        <span class="w-14 h-14 rounded-full bg-ungu-gelap text-white grid place-items-center">
          <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M12 3l7 2.6v5.1c0 4-3 7.3-7 7.9-4-.6-7-3.9-7-7.9V5.6z" /><path d="M9 11.5l2 2 4-4" />
          </svg>
        </span>
        <div>
          <h1 class="text-xl font-bold">HotelGuard</h1>
          <p class="sub mt-1">Masuk untuk membuka dashboard prediksi pembatalan reservasi</p>
        </div>
      </div>

      <label class="flex flex-col gap-1.5 text-[12.5px] font-medium text-teks-sedang">Username
        <input v-model="username" type="text" autocomplete="username" required placeholder="Masukkan username" :class="isian" />
      </label>
      <label class="flex flex-col gap-1.5 text-[12.5px] font-medium text-teks-sedang">Password
        <span class="relative">
          <input v-model="password" :type="lihat ? 'text' : 'password'" autocomplete="current-password" required placeholder="Masukkan password" :class="isian + ' pr-16'" />
          <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-semibold text-ungu px-2 py-1" @click="lihat = !lihat">{{ lihat ? 'Sembunyikan' : 'Lihat' }}</button>
        </span>
      </label>

      <p v-if="error" class="text-sm text-pink-tua -mt-2">{{ error }}</p>
      <button type="submit" class="btn-ungu min-h-[46px] w-full text-sm">Masuk</button>
      <p class="sub text-center">Kelompok 3 · Perdagangan Elektronik dan Intelligent Bisnis</p>
    </form>
  </div>
</template>
