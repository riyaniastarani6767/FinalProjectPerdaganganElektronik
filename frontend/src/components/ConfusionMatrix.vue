<script setup>
import { ribuan } from '../api'
defineProps({ tn: Number, fp: Number, fn: Number, tp: Number })
</script>

<template>
  <div class="grid grid-cols-[110px_1fr_1fr] gap-1.5 text-xs text-center">
    <span></span>
    <span class="font-semibold text-teks-sedang pb-1">Prediksi tidak batal</span>
    <span class="font-semibold text-teks-sedang">Prediksi batal</span>
    <span class="text-left font-semibold text-teks-sedang self-center">Asli tidak batal</span>
    <div class="bg-ungu text-white rounded py-5"><strong class="block text-2xl">{{ ribuan(tn) }}</strong>TN · benar tidak batal</div>
    <div class="bg-pink-muda text-pink-gelap rounded py-5"><strong class="block text-2xl">{{ ribuan(fp) }}</strong>FP · salah ditebak batal</div>
    <span class="text-left font-semibold text-teks-sedang self-center">Asli batal</span>
    <div class="bg-pink-muda text-pink-gelap rounded py-5"><strong class="block text-2xl">{{ ribuan(fn) }}</strong>FN · batal tidak tertangkap</div>
    <div class="bg-ungu text-white rounded py-5"><strong class="block text-2xl">{{ ribuan(tp) }}</strong>TP · benar batal</div>
  </div>
</template>
