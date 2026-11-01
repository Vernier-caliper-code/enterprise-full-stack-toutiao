<script setup>
import { computed, onMounted, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import { useRouter } from 'vue-router'

import { useFavoriteStore } from '../store/modules/favorite'
import { formatDate, formatViews } from '../utils/format'

const router = useRouter()
const favoriteStore = useFavoriteStore()
const listLoading = ref(false)
const clearing = ref(false)
const pendingRemoveIds = ref([])

const finished = computed(() => !favoriteStore.hasMore)
const hasItems = computed(() => favoriteStore.list.length > 0)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/my')
}

async function loadFirstPage() {
  try {
    await favoriteStore.fetchList({ reset: true })
  } catch {
    // Store error is rendered in the page.
  }
}

async function loadMore() {
  if (!favoriteStore.hasMore || favoriteStore.loading) {
    listLoading.value = false
    return
  }

  listLoading.value = true
  try {
    await favoriteStore.fetchList()
  } catch (error) {
    showToast(error.message)
  } finally {
    listLoading.value = false
  }
}

function openNews(item) {
  router.push(`/news/${item.newsId}`)
}

async function removeFavorite(item) {
  if (pendingRemoveIds.value.includes(item.id)) return
  try {
    await showConfirmDialog({
      title: '取消收藏',
      message: '确定取消收藏吗？',
      confirmButtonText: '取消收藏',
      confirmButtonColor: '#ee0a24',
    })
  } catch {
    return
  }

  pendingRemoveIds.value.push(item.id)
  const removedIndex = favoriteStore.list.findIndex((entry) => entry.id === item.id)
  const removedItem = favoriteStore.list[removedIndex]
  if (removedIndex >= 0) {
    favoriteStore.list.splice(removedIndex, 1)
    favoriteStore.total = Math.max(0, favoriteStore.total - 1)
  }

  try {
    await favoriteStore.removeFavorite(item.newsId)
    showToast('已取消收藏')
  } catch (error) {
    if (removedItem) {
      favoriteStore.list.splice(removedIndex, 0, removedItem)
      favoriteStore.total += 1
    }
    showToast(error.message)
  } finally {
    pendingRemoveIds.value = pendingRemoveIds.value.filter((id) => id !== item.id)
  }
}

async function clearAll() {
  if (!hasItems.value || clearing.value) return
  try {
    await showConfirmDialog({
      title: '清空收藏',
      message: '确定清空全部收藏吗？此操作无法撤销。',
      confirmButtonText: '清空',
      confirmButtonColor: '#ee0a24',
    })
  } catch {
    return
  }

  clearing.value = true
  try {
    await favoriteStore.clearFavorites()
    showToast('收藏已清空')
  } catch (error) {
    showToast(error.message)
  } finally {
    clearing.value = false
  }
}

onMounted(loadFirstPage)
</script>

<template>
  <div class="page activity-page">
    <van-nav-bar title="我的收藏" left-arrow @click-left="goBack">
      <template #right>
        <button
          class="nav-action"
          type="button"
          :disabled="!hasItems || clearing"
          @click="clearAll"
        >
          清空
        </button>
      </template>
    </van-nav-bar>

    <div v-if="favoriteStore.loading && !hasItems" class="list-loading">
      <van-loading size="28" vertical>正在加载收藏...</van-loading>
    </div>

    <div
      v-else-if="favoriteStore.error && !hasItems"
      class="state-panel state-panel--transparent"
    >
      <van-icon name="warning-o" size="42" color="var(--app-text-weak)" />
      <h2 class="state-title">加载失败</h2>
      <p class="state-message">{{ favoriteStore.error }}</p>
      <van-button type="primary" round size="small" @click="loadFirstPage">重新加载</van-button>
    </div>

    <van-empty
      v-else-if="!hasItems"
      image="search"
      description="暂无收藏"
    >
      <van-button class="empty-action" type="primary" round size="small" @click="router.push('/')">
        去首页看看
      </van-button>
    </van-empty>

    <div v-else class="activity-list">
      <van-list
        v-model:loading="listLoading"
        :finished="finished"
        finished-text="没有更多了"
        :immediate-check="false"
        @load="loadMore"
      >
        <article
          v-for="item in favoriteStore.list"
          :key="item.id"
          class="activity-card"
          role="button"
          tabindex="0"
          @click="openNews(item)"
          @keydown.enter="openNews(item)"
        >
          <div v-if="item.image" class="activity-image">
            <van-image :src="item.image" fit="cover">
              <template #error>
                <div class="image-fallback"><van-icon name="photo-o" size="24" /></div>
              </template>
            </van-image>
          </div>

          <div class="activity-copy">
            <h2>{{ item.title }}</h2>
            <p class="activity-meta">
              {{ item.author || '未知作者' }} · {{ formatDate(item.publishTime) }} ·
              {{ formatViews(item.views) }}
            </p>
            <p class="activity-time">收藏于 {{ formatDate(item.favoriteTime, true) }}</p>
          </div>

          <button
            class="delete-button"
            type="button"
            aria-label="取消收藏"
            :disabled="pendingRemoveIds.includes(item.id)"
            @click.stop="removeFavorite(item)"
          >
            <van-loading v-if="pendingRemoveIds.includes(item.id)" size="16" />
            <span v-else class="delete-circle"><van-icon name="cross" size="14" /></span>
          </button>
        </article>
      </van-list>
    </div>
  </div>
</template>

<style scoped>
.activity-page {
  min-height: 100dvh;
  background: var(--app-bg);
}

.nav-action {
  min-width: 44px;
  height: 44px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--app-danger);
  font-size: 14px;
  cursor: pointer;
}

.nav-action:disabled {
  color: var(--app-text-weak);
}

.list-loading {
  display: grid;
  min-height: 56vh;
  place-items: center;
}

.activity-list {
  padding: 8px 0 24px;
}

.activity-card {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
  padding: 14px 16px;
  background: var(--app-surface);
  cursor: pointer;
}

.activity-card:focus-visible {
  outline: 2px solid var(--van-primary-color);
  outline-offset: -2px;
}

.activity-image {
  width: 96px;
  height: 64px;
  flex: 0 0 96px;
  overflow: hidden;
  border-radius: 4px;
  background: var(--app-placeholder);
}

.activity-image :deep(.van-image),
.activity-image :deep(img) {
  width: 100%;
  height: 100%;
}

.image-fallback {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  color: var(--app-text-secondary);
  background: var(--app-placeholder);
}

.activity-copy {
  min-width: 0;
  flex: 1;
}

.activity-copy h2 {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--app-text);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.activity-meta,
.activity-time {
  overflow: hidden;
  margin: 6px 0 0;
  color: var(--app-text-secondary);
  font-size: 12px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-time {
  color: var(--app-text-weak);
}

.delete-button {
  display: grid;
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  place-items: center;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.delete-circle {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 50%;
  background: var(--app-danger);
  color: #ffffff;
}

.delete-button:disabled {
  opacity: 0.55;
}
</style>



