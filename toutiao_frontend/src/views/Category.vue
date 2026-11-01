<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useNewsStore } from '../store/modules/news'

const router = useRouter()
const newsStore = useNewsStore()
const loading = ref(false)

async function loadCategories() {
  loading.value = true
  try {
    await newsStore.fetchCategories()
  } catch {
    // The store error is rendered below.
  } finally {
    loading.value = false
  }
}

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}

function chooseCategory(category) {
  router.push({ path: '/', query: { categoryId: category.id } })
}

onMounted(() => {
  if (!newsStore.categories.length) loadCategories()
})
</script>

<template>
  <div class="page category-page">
    <van-nav-bar title="全部分类" left-arrow @click-left="goBack" />

    <main class="category-content">
      <div v-if="loading || (newsStore.categoriesLoading && !newsStore.categories.length)" class="category-grid">
        <div v-for="index in 9" :key="index" class="category-card category-card--loading">
          <van-skeleton :row="1" />
        </div>
      </div>

      <div v-else-if="newsStore.categoriesError && !newsStore.categories.length" class="state-panel state-panel--transparent">
        <van-icon name="warning-o" size="42" color="var(--app-text-weak)" />
        <h2 class="state-title">分类加载失败</h2>
        <p class="state-message">{{ newsStore.categoriesError }}</p>
        <van-button type="primary" round size="small" @click="loadCategories">重新加载</van-button>
      </div>

      <van-empty
        v-else-if="!newsStore.categories.length"
        description="暂无分类"
      />

      <div v-else class="category-grid">
        <button
          v-for="category in newsStore.categories"
          :key="category.id"
          class="category-card"
          type="button"
          @click="chooseCategory(category)"
        >
          <van-icon name="newspaper-o" size="28" color="var(--van-primary-color)" />
          <span>{{ category.name }}</span>
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.category-page {
  background: var(--app-bg);
}

.category-content {
  min-height: calc(100dvh - 47px - 50px - env(safe-area-inset-bottom));
  padding: 16px 16px 28px;
  background: var(--app-surface);
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.category-card {
  display: flex;
  min-height: 95px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 8px;
  border: 0;
  border-radius: 8px;
  background: var(--app-placeholder);
  color: var(--app-text);
  font-size: 15px;
  cursor: pointer;
}

.category-card:active {
  background: var(--app-pressed);
}

.category-card--loading {
  justify-content: center;
}

.category-card--loading :deep(.van-skeleton) {
  padding: 0;
}
</style>
