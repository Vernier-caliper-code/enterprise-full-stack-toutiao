<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { showToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'

import NewsItem from '../components/NewsItem.vue'
import { useFavoriteStore } from '../store/modules/favorite'
import { useHistoryStore } from '../store/modules/history'
import { useNewsStore } from '../store/modules/news'
import { useUserStore } from '../store/user'
import { formatDate, formatViews } from '../utils/format'

const route = useRoute()
const router = useRouter()
const newsStore = useNewsStore()
const userStore = useUserStore()
const favoriteStore = useFavoriteStore()
const historyStore = useHistoryStore()

const isFavorite = ref(false)
const favoriteLoading = ref(false)
const favoriteBurst = ref(false)
const imageFailed = ref(false)
const readingProgress = ref(0)
const showBackToTop = ref(false)
const detail = computed(() => newsStore.detail)
const loading = computed(() => newsStore.detailLoading)
const error = computed(() => newsStore.detailError)
const isNotFound = computed(() => newsStore.detailErrorStatus === 404)
const readingLabel = computed(() => `${Math.round(readingProgress.value * 100)}%`)

let progressFrame = 0
let burstTimer = 0

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

function updateReadingProgress() {
  if (progressFrame) return
  progressFrame = window.requestAnimationFrame(() => {
    progressFrame = 0
    const scrollTop = window.scrollY || document.documentElement.scrollTop
    const scrollRange = document.documentElement.scrollHeight - window.innerHeight
    readingProgress.value = scrollRange > 0 ? Math.min(1, Math.max(0, scrollTop / scrollRange)) : 0
    showBackToTop.value = scrollTop > 520
  })
}

function scrollToTop() {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' })
}

async function loadNews() {
  const id = Number(route.params.id)
  if (!id) return
  isFavorite.value = false
  imageFailed.value = false
  await nextTick()
  updateReadingProgress()

  try {
    await newsStore.fetchNewsDetail(id)
    if (!userStore.isLoggedIn || Number(route.params.id) !== id) return

    favoriteStore.checkStatus(id)
      .then((status) => {
        if (Number(route.params.id) === id) isFavorite.value = status
      })
      .catch(() => {
        if (Number(route.params.id) === id) isFavorite.value = false
      })

    historyStore.addHistory(id).catch(() => {})
  } catch {
    // The store error drives the page-level error state.
  }
}

async function toggleFavorite() {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  if (favoriteLoading.value) return

  const newsId = Number(route.params.id)
  favoriteLoading.value = true
  try {
    if (isFavorite.value) {
      await favoriteStore.removeFavorite(newsId)
      isFavorite.value = false
      showToast('已取消收藏')
    } else {
      await favoriteStore.addFavorite(newsId)
      isFavorite.value = true
      favoriteBurst.value = true
      window.clearTimeout(burstTimer)
      burstTimer = window.setTimeout(() => {
        favoriteBurst.value = false
      }, 420)
      showToast('收藏成功')
    }
  } catch (error) {
    showToast(error.message)
  } finally {
    favoriteLoading.value = false
  }
}

function openRelated(news) {
  router.push(`/news/${news.id}`)
}

watch(
  () => route.params.id,
  () => loadNews(),
  { immediate: true },
)

onMounted(() => window.addEventListener('scroll', updateReadingProgress, { passive: true }))

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateReadingProgress)
  window.cancelAnimationFrame(progressFrame)
  window.clearTimeout(burstTimer)
  newsStore.clearDetail()
})
</script>

<template>
  <div class="page detail-page">
    <div class="reading-progress" aria-hidden="true">
      <span :style="{ transform: `scaleX(${readingProgress})` }" />
    </div>

    <van-nav-bar
      title="新闻详情"
      left-arrow
      fixed
      placeholder
      @click-left="goBack"
    >
      <template #right>
        <button
          class="favorite-button"
          :class="{ 'favorite-button--burst': favoriteBurst }"
          type="button"
          :disabled="favoriteLoading"
          :aria-pressed="isFavorite"
          :aria-label="isFavorite ? '取消收藏' : '收藏新闻'"
          @click="toggleFavorite"
        >
          <van-loading v-if="favoriteLoading" size="18" />
          <van-icon
            v-else
            :name="isFavorite ? 'star' : 'star-o'"
            size="22"
            :color="isFavorite ? '#f7b500' : 'var(--app-text)'"
          />
        </button>
      </template>
    </van-nav-bar>

    <div v-if="loading" class="detail-skeleton" aria-label="正在加载新闻详情">
      <van-skeleton title :row="1" />
      <van-skeleton :row="6" />
      <div class="skeleton-cover" />
      <van-skeleton :row="5" />
    </div>

    <div v-else-if="error" class="state-panel state-panel--transparent">
      <van-icon name="warning-o" size="42" color="var(--app-text-weak)" />
      <h2 class="state-title">{{ isNotFound ? '新闻不存在' : '加载失败' }}</h2>
      <p class="state-message">{{ isNotFound ? '这条新闻可能已被删除或移动' : error }}</p>
      <van-button v-if="isNotFound" type="primary" round size="small" @click="router.push('/')">
        返回首页
      </van-button>
      <van-button v-else type="primary" round size="small" @click="loadNews">重新加载</van-button>
    </div>

    <article v-else-if="detail" class="article">
      <h1 class="article-title">{{ detail.title }}</h1>
      <div class="article-meta">
        <span>{{ detail.author || '未知作者' }}</span>
        <span>{{ formatDate(detail.publishTime) }}</span>
        <span>{{ formatViews(detail.views) }}</span>
      </div>

      <img
        v-if="detail.image && !imageFailed"
        class="article-cover"
        :src="detail.image"
        :alt="detail.title"
        @error="imageFailed = true"
      />

      <div class="article-content">{{ detail.content || '暂无正文内容' }}</div>

      <section v-if="detail.relatedNews?.length" class="related-section">
        <h2 class="related-title">相关推荐</h2>
        <div
          v-for="news in detail.relatedNews"
          :key="news.id"
          class="related-row"
        >
          <NewsItem :news="news" compact @click="openRelated" />
        </div>
      </section>
    </article>

    <transition name="back-top">
      <button
        v-if="showBackToTop"
        class="back-to-top"
        type="button"
        :aria-label="`回到顶部，当前阅读进度 ${readingLabel}`"
        @click="scrollToTop"
      >
        <van-icon name="back-top" size="18" />
        <span>{{ readingLabel }}</span>
      </button>
    </transition>
  </div>
</template>

<style scoped>
.detail-page {
  background: var(--app-surface);
}

.reading-progress {
  position: fixed;
  top: 46px;
  right: max(0px, calc((100vw - 480px) / 2));
  left: max(0px, calc((100vw - 480px) / 2));
  z-index: 101;
  height: 2px;
  background: transparent;
  pointer-events: none;
}

.reading-progress span {
  display: block;
  width: 100%;
  height: 100%;
  background: var(--van-primary-color);
  transform-origin: left center;
  transition: transform 0.08s linear;
}

.favorite-button {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.favorite-button:disabled {
  opacity: 0.65;
}

.favorite-button--burst :deep(.van-icon) {
  animation: favorite-pop 0.42s cubic-bezier(0.2, 0.85, 0.35, 1.35);
}

.detail-skeleton {
  padding: 22px 16px;
  background: var(--app-surface);
}

.detail-skeleton > * + * {
  margin-top: 22px;
}

.skeleton-cover {
  width: 100%;
  height: 190px;
  border-radius: 8px;
  background: var(--app-placeholder);
  animation: skeleton-pulse 1.4s ease-in-out infinite;
}

.article {
  min-height: 70vh;
  padding-bottom: 88px;
  background: var(--app-surface);
}

.article-title {
  margin: 0;
  padding: 22px 16px 0;
  color: var(--app-text);
  font-size: 23px;
  font-weight: 700;
  line-height: 1.42;
}

.article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  padding: 12px 16px 0;
  color: var(--app-text-secondary);
  font-size: 12px;
}

.article-cover {
  display: block;
  width: calc(100% - 32px);
  max-height: 280px;
  margin: 18px 16px 0;
  border-radius: 8px;
  object-fit: cover;
  background: var(--app-placeholder);
}

.article-content {
  padding: 20px 16px 8px;
  color: var(--app-text);
  font-size: 16px;
  line-height: 1.78;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.related-section {
  margin-top: 20px;
  padding-top: 8px;
  border-top: 8px solid var(--app-bg);
}

.related-title {
  margin: 0;
  padding: 12px 16px 4px;
  color: var(--app-text);
  font-size: 17px;
  font-weight: 600;
}

.related-row + .related-row {
  border-top: 1px solid var(--app-border);
}

.back-to-top {
  position: fixed;
  right: max(16px, calc((100vw - 480px) / 2 + 16px));
  bottom: calc(22px + env(safe-area-inset-bottom));
  z-index: 90;
  display: inline-flex;
  width: 48px;
  height: 48px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid var(--app-border);
  border-radius: 50%;
  background: var(--app-surface);
  color: var(--app-text-secondary);
  font-size: 9px;
  box-shadow: 0 8px 22px rgb(17 24 39 / 13%);
  cursor: pointer;
}

.back-to-top span {
  color: var(--app-text-secondary);
  line-height: 1;
}

.back-top-enter-active,
.back-top-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.back-top-enter-from,
.back-top-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.92);
}

@keyframes favorite-pop {
  0% {
    transform: scale(0.72) rotate(-12deg);
  }
  55% {
    transform: scale(1.28) rotate(5deg);
  }
  100% {
    transform: scale(1) rotate(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .reading-progress span,
  .favorite-button--burst :deep(.van-icon),
  .back-top-enter-active,
  .back-top-leave-active {
    transition: none;
    animation: none;
  }
}
</style>
