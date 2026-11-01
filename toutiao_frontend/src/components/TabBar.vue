<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const active = computed(() => route.meta.activeTab || 'home')
</script>

<template>
  <van-tabbar
    :model-value="active"
    route
    fixed
    class="app-tabbar"
    safe-area-inset-bottom
  >
    <van-tabbar-item replace to="/" icon="home-o">首页</van-tabbar-item>
    <van-tabbar-item replace to="/ai-chat" icon="chat-o">AI问答</van-tabbar-item>
    <van-tabbar-item replace to="/my" icon="user-o">我的</van-tabbar-item>
  </van-tabbar>
</template>

<style scoped>
.app-tabbar {
  left: 50%;
  width: min(100%, 480px);
  transform: translateX(-50%);
  border-top: 1px solid var(--app-border);
  background: var(--app-surface);
  z-index: 100;
}

.app-tabbar :deep(.van-tabbar-item) {
  color: var(--app-text);
}

.app-tabbar :deep(.van-tabbar-item--active) {
  color: var(--van-primary-color);
}
</style>
