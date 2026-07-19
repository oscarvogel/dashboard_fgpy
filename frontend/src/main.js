import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/index.css'
import VueApexCharts from 'vue3-apexcharts'
import { installUpdateActivityTracker } from './updateActivity'

if (import.meta.env.DEV && 'serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations()
    .then(registrations => registrations.forEach(registration => registration.unregister()))
    .catch(() => {})
}

const savedTheme = localStorage.getItem('fgpy-theme')
const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
  document.documentElement.classList.add('dark')
}

installUpdateActivityTracker()

const app = createApp(App)
app.use(router)
app.use(VueApexCharts)
app.mount('#app')
