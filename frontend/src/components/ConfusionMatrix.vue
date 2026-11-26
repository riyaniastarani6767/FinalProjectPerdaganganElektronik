<script setup>
// Confusion matrix 2x2. Hover/ketuk kotak untuk melihat arti dan persentasenya.
import { computed } from 'vue'
import { ribuan } from '../api'
const props = defineProps({ tn: Number, fp: Number, fn: Number, tp: Number })
const total = computed(() => props.tn + props.fp + props.fn + props.tp)
const pct = (v) => ((v / total.value) * 100).toFixed(1).replace('.', ',') + '% dari data uji'
const kotak = computed(() => [
  { k: 'TN', v: props.tn, label: 'benar tidak batal', benar: true, arti: 'Tamu tidak batal dan model menebak tidak batal.' },
  { k: 'FP', v: props.fp, label: 'salah ditebak batal', benar: false, arti: 'Tamu tidak batal tetapi model menebak batal. Berisiko jika hotel melakukan overbooking.' },
  { k: 'FN', v: props.fn, label: 'batal tidak tertangkap', benar: false, arti: 'Tamu batal tetapi model menebak tidak batal. Kamar berisiko kosong.' },
  { k: 'TP', v: props.tp, label: 'benar batal', benar: true, arti: 'Tamu batal dan model berhasil menebak batal.' }
])
</script>

<template>
  <div class="grid grid-cols-[96px_1fr_1fr] gap-1.5 text-xs text-center">
    <span></span>
    <span class="font-semibold text-teks-sedang pb-1">Prediksi tidak batal</span>
    <span class="font-semibold text-teks-sedang">Prediksi batal</span>
    <template v-for="(b, i) in kotak" :key="b.k">
      <span v-if="i % 2 === 0" class="text-left font-semibold text-teks-sedang self-center">{{ i === 0 ? 'Asli tidak batal' : 'Asli batal' }}</span>
      <div v-tip="[`${b.k} · ${b.label}`, `${ribuan(b.v)} reservasi (${pct(b.v)})`, b.arti]"
        class="rounded-[10px] py-5 transition-shadow hover:ring-2 hover:ring-offset-1"
        :class="b.benar ? 'bg-ungu-muda text-ungu-gelap hover:ring-ungu' : 'bg-pink-muda text-pink-gelap hover:ring-pink'">
        <strong class="block text-2xl">{{ ribuan(b.v) }}</strong>{{ b.k }} · {{ b.label }}
      </div>
    </template>
  </div>
</template>
