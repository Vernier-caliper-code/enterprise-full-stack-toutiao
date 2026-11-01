<script setup>
import { computed, ref } from 'vue'
import { showConfirmDialog, showDialog, showToast } from 'vant'
import { useRouter } from 'vue-router'

import { useUserStore } from '../store/user'

const THEME_KEY = 'toutiao_theme'
const router = useRouter()
const userStore = useUserStore()
const themeSheetVisible = ref(false)
const themePreference = ref(localStorage.getItem(THEME_KEY) || 'system')
const themeActions = [
  { name: '浅色', value: 'light' },
  { name: '深色', value: 'dark' },
  { name: '跟随系统', value: 'system' },
]

const themeLabel = computed(
  () => themeActions.find((item) => item.value === themePreference.value)?.name || '跟随系统',
)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/my')
}

function selectTheme(action) {
  themePreference.value = action.value
  localStorage.setItem(THEME_KEY, action.value)
  window.dispatchEvent(new CustomEvent('toutiao:theme-change', { detail: { theme: action.value } }))
  themeSheetVisible.value = false
}

function showComingSoon() {
  showToast('功能开发中')
}

function showAbout() {
  showDialog({
    title: '关于我们',
    message: 'AI 掘金头条\n版本 1.0.0\n一个专注于新闻浏览、收藏与 AI 问答的移动端资讯应用。',
    confirmButtonText: '知道了',
  })
}

async function logout() {
  try {
    await showConfirmDialog({
      title: '退出登录',
      message: '确定要退出当前账号吗？',
      confirmButtonText: '退出',
      confirmButtonColor: '#ee0a24',
    })
    userStore.logout()
    showToast('已退出登录')
    router.replace('/my')
  } catch {
    // Cancelled by the user.
  }
}
</script>

<template>
  <div class="page settings-page">
    <van-nav-bar title="设置" left-arrow @click-left="goBack" />

    <main class="settings-content">
      <p class="section-label">个性化</p>
      <van-cell-group class="settings-group">
        <van-cell title="主题定制" :value="themeLabel" is-link @click="themeSheetVisible = true">
          <template #icon>
            <van-icon name="brush-o" size="20" class="settings-icon" />
          </template>
        </van-cell>
        <van-cell title="语言设置" value="简体中文" is-link @click="showComingSoon">
          <template #icon>
            <van-icon name="language-o" size="20" class="settings-icon" />
          </template>
        </van-cell>
      </van-cell-group>

      <p class="section-label">账户</p>
      <van-cell-group class="settings-group">
        <van-cell title="隐私设置" is-link @click="showComingSoon">
          <template #icon>
            <van-icon name="shield-o" size="20" class="settings-icon" />
          </template>
        </van-cell>
        <van-cell title="关于我们" is-link @click="showAbout">
          <template #icon>
            <van-icon name="info-o" size="20" class="settings-icon" />
          </template>
        </van-cell>
      </van-cell-group>

      <van-button
        v-if="userStore.isLoggedIn"
        class="logout-button"
        plain
        block
        @click="logout"
      >
        退出登录
      </van-button>
    </main>

    <van-action-sheet
      v-model:show="themeSheetVisible"
      class="theme-action-sheet"
      :actions="themeActions"
      cancel-text="取消"
      close-on-click-action
      @select="selectTheme"
    />
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100dvh;
  background: var(--app-bg);
}

.settings-content {
  padding: 4px 0 36px;
}

.settings-group {
  margin: 0 16px;
  overflow: hidden;
  border-radius: 8px;
}

.settings-group + .section-label {
  margin-top: 8px;
}

.settings-icon {
  margin-right: 12px;
  color: var(--van-primary-color);
}

.logout-button {
  width: calc(100% - 32px);
  height: 46px;
  margin: 24px 16px 0;
  border-color: var(--app-danger);
  border-radius: 8px;
  background: var(--app-surface);
  color: var(--app-danger);
}

.theme-action-sheet {
  left: 50%;
  right: auto;
  width: min(100vw, 480px);
  margin-left: -240px;
}

@media (max-width: 520px) {
  .theme-action-sheet {
    width: 100vw;
    margin-left: -50vw;
  }
}
</style>

