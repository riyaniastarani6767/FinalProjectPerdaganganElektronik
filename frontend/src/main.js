import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import { vTip } from './tooltip'
import Dashboard from './pages/Dashboard.vue'
import UnggahData from './pages/UnggahData.vue'
import Prediksi from './pages/Prediksi.vue'
import Login from './pages/Login.vue'
import { auth } from './auth'
import './style.css'

// Daftar halaman (1 menu = 1 halaman)
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { publik: true } },
    { path: '/', component: Dashboard },
    { path: '/unggah', component: UnggahData },
    { path: '/prediksi', component: Prediksi },
    { path: '/evaluasi', redirect: '/prediksi' }  // halaman Evaluasi digabung ke Prediksi
  ],
  scrollBehavior: () => new Promise((r) => setTimeout(() => r({ top: 0, behavior: 'instant' }), 180))
})

// Halaman selain Login hanya bisa dibuka setelah masuk
router.beforeEach((to) => {
  if (!to.meta.publik && !auth.masuk) return '/login'
  if (to.path === '/login' && auth.masuk) return '/'
})

createApp(App).use(router).directive('tip', vTip).mount('#app')
