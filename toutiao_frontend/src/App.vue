<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import TabBar from './components/TabBar.vue'
import { useUserStore } from './store/user'

const THEME_KEY = 'toutiao_theme'
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const themePreference = ref(localStorage.getItem(THEME_KEY) || 'system')
const systemDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
const resolvedTheme = computed(() => {
  if (themePreference.value === 'system') return systemDark.value ? 'dark' : 'light'
  return themePreference.value === 'dark' ? 'dark' : 'light'
})

const syncTheme = () => {
  document.documentElement.dataset.theme = resolvedTheme.value
}

watch(resolvedTheme, syncTheme, { immediate: true })

function onSystemThemeChange(event) {
  systemDark.value = event.matches
}

function onThemeChange(event) {
  const nextTheme = event.detail?.theme || localStorage.getItem(THEME_KEY) || 'system'
  themePreference.value = ['light', 'dark', 'system'].includes(nextTheme) ? nextTheme : 'system'
}

function onUnauthorized() {
  userStore.clearAuth()
  const current = router.currentRoute.value
  if (current.path === '/login' || current.path === '/register') return
  router.replace({
    path: '/login',
    query: { redirect: current.fullPath },
  })
}

onMounted(() => {
  mediaQuery.addEventListener('change', onSystemThemeChange)
  window.addEventListener('toutiao:theme-change', onThemeChange)
  window.addEventListener('toutiao:unauthorized', onUnauthorized)

  if (userStore.isLoggedIn && !userStore.initialized) {
    userStore.fetchUserInfo().catch(() => {})
  }
})

onBeforeUnmount(() => {
  mediaQuery.removeEventListener('change', onSystemThemeChange)
  window.removeEventListener('toutiao:theme-change', onThemeChange)
  window.removeEventListener('toutiao:unauthorized', onUnauthorized)
})
</script>

<template>
  <van-config-provider :theme="resolvedTheme" class="app-provider">
    <div class="app-shell" :class="{ 'app-shell--with-tabbar': route.meta.showTabBar }">
      <router-view v-slot="{ Component, route: viewRoute }">
        <transition name="route-fade" mode="out-in">
          <component :is="Component" :key="viewRoute.path" />
        </transition>
      </router-view>
      <TabBar v-if="route.meta.showTabBar" />
    </div>
  </van-config-provider>
</template>
