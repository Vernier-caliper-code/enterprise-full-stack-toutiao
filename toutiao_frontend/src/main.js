import { createPinia } from 'pinia'
import Vant from 'vant'
import { createApp } from 'vue'

import 'vant/lib/index.css'
import './style.css'
import App from './App.vue'
import router from './router'

const savedTheme = localStorage.getItem('toutiao_theme') || 'system'
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
document.documentElement.dataset.theme = savedTheme === 'dark' || (savedTheme === 'system' && prefersDark)
  ? 'dark'
  : 'light'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Vant)
app.mount('#app')
