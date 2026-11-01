import { defineStore } from 'pinia'

import { historyApi } from '../../config/api'

let requestId = 0

export const useHistoryStore = defineStore('history', {
  state: () => ({
    list: [],
    page: 0,
    pageSize: 10,
    total: 0,
    hasMore: true,
    loading: false,
    error: '',
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
        const data = await historyApi.getList({ page: targetPage, pageSize: this.pageSize })
        if (currentRequestId !== requestId) return
        const nextList = data?.list || []
        this.list = reset ? nextList : [...this.list, ...nextList]
        this.page = targetPage
        this.total = Number(data?.total) || 0
        this.hasMore = Boolean(data?.hasMore)
      } catch (error) {
        if (currentRequestId === requestId) this.error = error.message
        throw error
      } finally {
        if (currentRequestId === requestId) this.loading = false
      }
    },

    async addHistory(newsId) {
      await historyApi.add(newsId)
      this.page = 0
      this.list = []
      this.hasMore = true
    },

    async removeHistory(historyId) {
      await historyApi.remove(historyId)
      const beforeLength = this.list.length
      this.list = this.list.filter((item) => item.id !== historyId)
      if (this.list.length < beforeLength) this.total = Math.max(0, this.total - 1)
    },

    async clearHistory() {
      const message = await historyApi.clear()
      this.list = []
      this.page = 0
      this.total = 0
      this.hasMore = false
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
    },
  },
})
