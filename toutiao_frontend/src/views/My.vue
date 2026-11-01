<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { DEFAULT_AVATAR } from '../config/api'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

function openProtected(path) {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: path } })
    return
  }
  router.push(path)
}

function goLogin() {
  router.push({ path: '/login', query: { redirect: '/my' } })
}

onMounted(() => {
  if (userStore.isLoggedIn && !userStore.initialized) {
    userStore.fetchUserInfo().catch(() => {})
  }
})
</script>

<template>
  <div class="page my-page">
    <van-nav-bar title="我的" />

    <main class="my-content">
      <button
        class="user-card"
        :class="{ 'user-card--clickable': userStore.isLoggedIn }"
        type="button"
        :disabled="!userStore.isLoggedIn"
        @click="router.push('/profile')"
      >
        <van-image class="user-avatar" round :src="userStore.avatar">
          <template #error>
            <div class="avatar-fallback">
              <van-icon name="user-o" size="30" />
            </div>
          </template>
        </van-image>

        <div class="user-copy">
          <h1>{{ userStore.isLoggedIn ? userStore.displayName : '未登录' }}</h1>
          <p>
            {{
              userStore.isLoggedIn
                ? userStore.userInfo?.bio || '这个人很懒，什么都没留下'
                : '登录后收藏新闻、同步浏览记录'
            }}
          </p>
        </div>

        <van-icon
          v-if="userStore.isLoggedIn"
          name="arrow"
          size="18"
          class="user-arrow"
        />
      </button>

      <div v-if="!userStore.isLoggedIn" class="auth-actions">
        <van-button type="primary" round block @click="goLogin">去登录</van-button>
        <van-button plain round block @click="router.push('/register')">去注册</van-button>
      </div>

      <section class="menu-section" aria-label="个人功能">
        <van-cell-group inset class="menu-group">
          <van-cell
            title="我的收藏"
            is-link
            @click="openProtected('/favorites')"
          >
            <template #icon>
              <van-icon name="star-o" size="20" class="menu-icon" />
            </template>
          </van-cell>
          <van-cell
            title="浏览历史"
            is-link
            @click="openProtected('/history')"
          >
            <template #icon>
              <van-icon name="clock-o" size="20" class="menu-icon" />
            </template>
          </van-cell>
        </van-cell-group>

        <van-cell-group inset class="menu-group">
          <van-cell title="设置" is-link @click="router.push('/settings')">
            <template #icon>
              <van-icon name="setting-o" size="20" class="menu-icon" />
            </template>
          </van-cell>
        </van-cell-group>
      </section>
    </main>
  </div>
</template>

<style scoped>
.my-page {
  background: var(--app-bg);
}

.my-content {
  padding: 16px 0 28px;
}

.user-card {
  display: flex;
  width: calc(100% - 32px);
  min-height: 132px;
  align-items: center;
  gap: 12px;
  margin: 0 16px;
  padding: 20px 16px;
  border: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, #1989fa, #0877e8);
  color: #ffffff;
  text-align: left;
  box-shadow: 0 10px 24px rgb(25 137 250 / 22%);
}

.user-card:disabled {
  opacity: 1;
}

.user-card--clickable {
  cursor: pointer;
}

.user-avatar {
  width: 64px;
  height: 64px;
  flex: 0 0 64px;
  overflow: hidden;
  border: 3px solid rgb(255 255 255 / 72%);
  border-radius: 50%;
  background: rgb(255 255 255 / 20%);
}

.user-avatar :deep(img) {
  width: 100%;
  height: 100%;
}

.avatar-fallback {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  background: rgb(255 255 255 / 24%);
  color: #ffffff;
}

.user-copy {
  min-width: 0;
  flex: 1;
}

.user-copy h1 {
  overflow: hidden;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy p {
  display: -webkit-box;
  overflow: hidden;
  margin: 8px 0 0;
  color: rgb(255 255 255 / 82%);
  font-size: 13px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.user-arrow {
  flex: 0 0 auto;
  color: rgb(255 255 255 / 68%);
}

.auth-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px;
}

.auth-actions :deep(.van-button--plain) {
  border-color: #ffffff;
  background: #ffffff;
  color: var(--van-primary-color);
}

.menu-section {
  margin-top: 4px;
}

.menu-group {
  margin-bottom: 16px;
  overflow: hidden;
  border-radius: 8px;
}

.menu-icon {
  margin-right: 12px;
  color: var(--van-primary-color);
}

@media (prefers-reduced-motion: reduce) {
  .user-card {
    box-shadow: none;
  }
}
</style>

