<script setup>
import { computed } from 'vue'

import { formatDate, formatViews } from '../utils/format'

const props = defineProps({
  news: {
    type: Object,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['click'])
const hasImage = computed(() => Boolean(props.news?.image))

function openNews() {
  emit('click', props.news)
}

function onKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openNews()
  }
}
</script>

<template>
  <article
    class="news-item"
    :class="{ 'news-item--compact': compact, 'news-item--no-image': !hasImage }"
    role="button"
    tabindex="0"
    @click="openNews"
    @keydown="onKeydown"
  >
    <div v-if="compact && hasImage" class="news-image news-image--compact">
      <van-image :src="news.image" fit="cover">
        <template #error>
          <div class="image-fallback"><van-icon name="photo-o" size="22" /></div>
        </template>
      </van-image>
    </div>

    <div class="news-copy">
      <h2 class="news-title">{{ news.title || '无标题新闻' }}</h2>
      <p v-if="!compact && news.description" class="news-description">{{ news.description }}</p>
      <div class="news-meta">
        <span>{{ news.author || '未知作者' }}</span>
        <span>{{ formatViews(news.views) }}</span>
        <span v-if="compact">{{ formatDate(news.publishTime) }}</span>
      </div>
    </div>

    <div v-if="!compact && hasImage" class="news-image">
      <van-image :src="news.image" fit="cover">
        <template #error>
          <div class="image-fallback"><van-icon name="photo-o" size="22" /></div>
        </template>
      </van-image>
    </div>
  </article>
</template>

<style scoped>
.news-item {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 16px;
  background: var(--app-surface);
  cursor: pointer;
  outline: none;
  touch-action: manipulation;
  transition: background-color 0.16s ease, transform 0.16s ease;
}

.news-item:active {
  background: var(--app-pressed);
  transform: scale(0.988);
}

.news-item:focus-visible {
  box-shadow: inset 0 0 0 2px var(--van-primary-color);
}

.news-copy {
  min-width: 0;
  flex: 1;
}

.news-title {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--app-text);
  font-size: 17px;
  font-weight: 600;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.news-description {
  display: -webkit-box;
  overflow: hidden;
  margin: 7px 0 0;
  color: var(--app-text-secondary);
  font-size: 13px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: auto;
  padding-top: 10px;
  color: var(--app-text-secondary);
  font-size: 12px;
  line-height: 1.3;
}

.news-image {
  width: 80px;
  height: 60px;
  flex: 0 0 80px;
  overflow: hidden;
  border-radius: 4px;
  background: var(--app-placeholder);
}

.news-image :deep(.van-image),
.news-image :deep(img) {
  width: 100%;
  height: 100%;
}

.news-image :deep(img) {
  transition: transform 0.2s ease;
}

.news-item:active .news-image :deep(img) {
  transform: scale(1.04);
}

.image-fallback {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  color: var(--app-text-secondary);
  background: var(--app-placeholder);
}

.news-item--compact {
  align-items: center;
  padding: 12px 16px;
}

.news-item--compact .news-title {
  font-size: 15px;
  line-height: 1.5;
}

.news-item--compact .news-meta {
  gap: 10px;
  margin-top: 6px;
  padding-top: 0;
}

.news-image--compact {
  width: 96px;
  height: 64px;
  flex-basis: 96px;
}

@media (prefers-reduced-motion: reduce) {
  .news-item,
  .news-image :deep(img) {
    transition: none;
  }

  .news-item:active,
  .news-item:active .news-image :deep(img) {
    transform: none;
  }
}
</style>
