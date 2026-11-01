import { defineStore } from 'pinia'

import { favoriteApi } from '../../config/api'

let requestId = 0

export const useFavoriteStore = defineStore('favorite', {
  state: () => ({
    list: [],
    page: 0,
    pageSize: 10,
    total: 0,
    hasMore: true,
    loading: false,
    error: '',
    statusMap: {},
  }),

  actions: {
    async fetchList({ reset = false } = {}) {
      if (this.loading && !reset) return
      if (!reset && this.page > 0 && !this.hasMore) return

      const targetPage = reset ? 1 : this.page + 1
      const currentRequestId = ++requestId
      if (reset) {
        this.list = []
        this.page = 0
        this.total = 0
        this.hasMore = true
        this.error = ''
      }

      this.loading = true
      try {
        const data = await favoriteApi.getList({ page: targetPage, pageSize: this.pageSize })
        if (currentRequestId !== requestId) return
        const nextList = data?.list || []
        this.list = reset ? nextList : [...this.list, ...nextList]
        this.page = targetPage
        this.total = Number(data?.total) || 0
        this.hasMore = Boolean(data?.hasMore)
        nextList.forEach((item) => {
          this.statusMap[item.newsId] = true
        })
      } catch (error) {
        if (currentRequestId === requestId) this.error = error.message
        throw error
      } finally {
        if (currentRequestId === requestId) this.loading = false
      }
    },

    async checkStatus(newsId) {
      const data = await favoriteApi.check(newsId)
      const isFavorite = Boolean(data?.isFavorite)
      this.statusMap[newsId] = isFavorite
      return isFavorite
    },

    async addFavorite(newsId) {
      await favoriteApi.add(newsId)
      this.statusMap[newsId] = true
      this.total += 1
    },

    async removeFavorite(newsId) {
      await favoriteApi.remove(newsId)
      this.statusMap[newsId] = false
      const beforeLength = this.list.length
      this.list = this.list.filter((item) => item.newsId !== newsId)
      if (this.list.length < beforeLength) this.total = Math.max(0, this.total - 1)
    },

    async clearFavorites() {
      const message = await favoriteApi.clear()
      this.list = []
      this.page = 0
      this.total = 0
      this.hasMore = false
      this.statusMap = {}
      return message
    },

    reset() {
      requestId += 1
      this.list = []
      this.page = 0
      this.total = 0
      this.hasMore = true
      this.loading = false
      this.error = ''
      this.statusMap = {}
    },
  },
})
