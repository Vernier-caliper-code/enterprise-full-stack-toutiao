<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { showToast } from 'vant'
import { useRoute, useRouter } from 'vue-router'

import NewsItem from '../components/NewsItem.vue'
import { useNewsStore } from '../store/modules/news'

const route = useRoute()
const router = useRouter()
const newsStore = useNewsStore()
const categoryScroll = ref(null)
const refreshing = ref(false)
const listLoading = ref(false)
const switchingCategoryId = ref(null)
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

const finished = computed(() => !newsStore.hasMore)
const showInitialLoading = computed(
  () => (newsStore.categoriesLoading || newsStore.loading) && !newsStore.list.length,
)
const initialError = computed(() => newsStore.categoriesError || newsStore.error)

function validCategoryId(value) {
  const id = Number(value)
  return newsStore.categories.some((category) => category.id === id) ? id : null
}

async function scrollActiveCategoryIntoView() {
  await nextTick()
  const activeId = newsStore.activeCategoryId
  if (!activeId || !categoryScroll.value) return

  const activeTab = categoryScroll.value.querySelector(`[data-category-id="${activeId}"]`)
  activeTab?.scrollIntoView({
    block: 'nearest',
    inline: 'center',
    behavior: reduceMotion ? 'auto' : 'smooth',
  })
}

async function loadInitialData() {
  try {
    if (!newsStore.categories.length) await newsStore.fetchCategories()
    if (!newsStore.categories.length) return

    const queryId = validCategoryId(route.query.categoryId)
    const desiredId = queryId || newsStore.activeCategoryId || newsStore.categories[0].id
    const categoryChanged = newsStore.activeCategoryId !== desiredId

    if (categoryChanged) newsStore.activeCategoryId = desiredId
    if (categoryChanged || !newsStore.list.length) {
      await newsStore.fetchNews({ reset: true })
    }
    await scrollActiveCategoryIntoView()
  } catch {
    // The page renders the store error with a retry action.
  }
}

async function chooseCategory(categoryId) {
  if (categoryId === newsStore.activeCategoryId) return

  newsStore.activeCategoryId = categoryId
  switchingCategoryId.value = categoryId
  try {
    await Promise.all([
      router.replace({ path: '/', query: { categoryId } }),
      newsStore.fetchNews({ reset: true }),
    ])
  } catch (error) {
    showToast(error.message)
  } finally {
    if (switchingCategoryId.value === categoryId) switchingCategoryId.value = null
  }
}

async function loadMore() {
  if (!newsStore.hasMore || newsStore.loading) {
    listLoading.value = false
    return
  }

  listLoading.value = true
  try {
    await newsStore.fetchNews()
  } catch (error) {
    showToast(error.message)
  } finally {
    listLoading.value = false
  }
}

async function refresh() {
  try {
    await newsStore.fetchNews({ reset: true })
  } catch (error) {
    showToast(error.message)
  } finally {
    refreshing.value = false
  }
}

function openNews(news) {
  router.push(`/news/${news.id}`)
}

onMounted(loadInitialData)

watch(
  () => newsStore.activeCategoryId,
  scrollActiveCategoryIntoView,
)

watch(
  () => route.query.categoryId,
  (value) => {
    const id = validCategoryId(value)
    if (!id || id === newsStore.activeCategoryId) return
    newsStore.activeCategoryId = id
    newsStore.fetchNews({ reset: true }).catch((error) => showToast(error.message))
  },
)
</script>

<template>
  <div class="page home-page">
    <van-nav-bar title="新闻资讯" />

    <div v-if="newsStore.categories.length" class="category-bar">
      <div ref="categoryScroll" class="category-scroll" role="tablist" aria-label="新闻分类">
        <button
          v-for="category in newsStore.categories"
          :key="category.id"
          class="category-tab"
          :class="{ 'category-tab--active': category.id === newsStore.activeCategoryId }"
          type="button"
          role="tab"
          :data-category-id="category.id"
          :aria-selected="category.id === newsStore.activeCategoryId"
          :aria-busy="switchingCategoryId === category.id"
          @click="chooseCategory(category.id)"
        >
          <span
            v-if="switchingCategoryId === category.id"
            class="tab-switch-spinner"
            aria-hidden="true"
          />
          {{ category.name }}
        </button>
      </div>
      <button class="more-button" type="button" @click="router.push('/category')">
        更多
        <van-icon name="arrow" size="12" />
      </button>
    </div>

    <div
      v-if="switchingCategoryId"
      class="category-switch-progress"
      role="status"
      aria-label="正在切换分类"
    >
      <span />
    </div>

    <main class="news-stream" :aria-busy="Boolean(switchingCategoryId)">
      <div v-if="showInitialLoading" class="skeleton-list" aria-label="正在加载新闻">
        <div v-for="index in 4" :key="index" class="skeleton-card">
          <div class="skeleton-copy">
            <van-skeleton title :row="2" />
          </div>
          <div class="skeleton-image" />
        </div>
      </div>

      <div v-else-if="initialError && !newsStore.list.length" class="state-panel">
        <van-icon name="warning-o" size="42" color="var(--app-text-weak)" />
        <h2 class="state-title">加载失败</h2>
        <p class="state-message">{{ initialError }}</p>
        <van-button type="primary" round size="small" @click="loadInitialData">重新加载</van-button>
      </div>

      <van-empty
        v-else-if="!newsStore.list.length"
        image="search"
        description="暂无新闻"
      >
        <van-button class="empty-action" type="primary" round size="small" @click="loadInitialData">
          刷新看看
        </van-button>
      </van-empty>

      <van-pull-refresh
        v-else
        v-model="refreshing"
        success-text="刷新成功"
        @refresh="refresh"
      >
        <van-list
          v-model:loading="listLoading"
          :finished="finished"
          finished-text="没有更多了"
          :immediate-check="false"
          @load="loadMore"
        >
          <div
            v-for="news in newsStore.list"
            :key="news.id"
            class="news-row"
          >
            <NewsItem :news="news" @click="openNews" />
          </div>
        </van-list>
      </van-pull-refresh>
    </main>
  </div>
</template>

<style scoped>
.home-page {
  background: var(--app-surface);
}

.category-bar {
  display: flex;
  height: 48px;
  align-items: stretch;
  border-bottom: 1px solid var(--app-border);
  background: var(--app-surface);
}

.category-scroll {
  display: flex;
  min-width: 0;
  flex: 1;
  overflow-x: auto;
  scroll-behavior: smooth;
  scrollbar-width: none;
}

.category-scroll::-webkit-scrollbar {
  display: none;
}

.category-tab {
  position: relative;
  display: inline-flex;
  min-width: 64px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 12px;
  border: 0;
  background: transparent;
  color: var(--app-text-secondary);
  font-size: 15px;
  cursor: pointer;
  touch-action: manipulation;
}

.category-tab--active {
  color: var(--van-primary-color);
  font-weight: 600;
}

.category-tab--active::after {
  position: absolute;
  right: 20px;
  bottom: 0;
  left: 20px;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: var(--van-primary-color);
  content: '';
}

.tab-switch-spinner {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: switch-pulse 0.8s ease-in-out infinite alternate;
}

.category-switch-progress {
  height: 2px;
  overflow: hidden;
  background: color-mix(in srgb, var(--van-primary-color) 12%, transparent);
}

.category-switch-progress span {
  display: block;
  width: 38%;
  height: 100%;
  border-radius: 999px;
  background: var(--van-primary-color);
  animation: switch-progress 0.9s ease-in-out infinite;
}

.more-button {
  display: flex;
  min-width: 64px;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 0 10px;
  border: 0;
  border-left: 1px solid var(--app-border);
  background: var(--app-surface);
  color: var(--app-text-secondary);
  font-size: 13px;
  cursor: pointer;
  touch-action: manipulation;
}

.news-stream {
  min-height: calc(100dvh - 95px);
  background: var(--app-surface);
  transition: opacity 0.16s ease;
}

.news-stream[aria-busy='true'] {
  opacity: 0.72;
}

.news-row + .news-row {
  border-top: 1px solid var(--app-border);
}

.skeleton-list {
  background: var(--app-surface);
}

.skeleton-card + .skeleton-card {
  border-top: 1px solid var(--app-border);
}

@keyframes switch-progress {
  from {
    transform: translateX(-110%);
  }
  to {
    transform: translateX(290%);
  }
}

@keyframes switch-pulse {
  from {
    opacity: 0.35;
    transform: scale(0.75);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .category-scroll {
    scroll-behavior: auto;
  }

  .news-stream {
    transition: none;
  }

  .category-switch-progress span,
  .tab-switch-spinner {
    animation: none;
  }
}
</style>
