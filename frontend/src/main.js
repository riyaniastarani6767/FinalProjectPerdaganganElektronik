import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './pages/Dashboard.vue'
import UnggahData from './pages/UnggahData.vue'
import Prediksi from './pages/Prediksi.vue'
import Evaluasi from './pages/Evaluasi.vue'
import './style.css'

// Daftar halaman (1 menu = 1 halaman)
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/unggah', component: UnggahData },
    { path: '/prediksi', component: Prediksi },
    { path: '/evaluasi', component: Evaluasi }
  ],
  scrollBehavior: () => ({ top: 0 })
})

createApp(App).use(router).mount('#app')
