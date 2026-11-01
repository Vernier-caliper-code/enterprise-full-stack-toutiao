import { defineStore } from 'pinia'

import { newsApi } from '../../config/api'

let listRequestId = 0
let detailRequestId = 0

export const useNewsStore = defineStore('news', {
  state: () => ({
    categories: [],
    activeCategoryId: null,
    list: [],
    page: 0,
    pageSize: 10,
    total: 0,
    hasMore: true,
    loading: false,
    categoriesLoading: false,
    categoriesError: '',
    error: '',
    detail: null,
    detailLoading: false,
    detailError: '',
    detailErrorStatus: null,
  }),

  getters: {
    activeCategory: (state) => state.categories.find((item) => item.id === state.activeCategoryId) || null,
  },

  actions: {
    async fetchCategories() {
      if (this.categoriesLoading) return this.categories
      this.categoriesLoading = true
      this.categoriesError = ''
      try {
        const data = await newsApi.getCategories({ limit: 100 })
        this.categories = [...(data || [])].sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0))
        if (!this.activeCategoryId && this.categories.length) {
          this.activeCategoryId = this.categories[0].id
        }
        return this.categories
      } catch (error) {
        this.categoriesError = error.message
        throw error
      } finally {
        this.categoriesLoading = false
      }
    },

    async selectCategory(categoryId) {
      const id = Number(categoryId)
      if (!id || id === this.activeCategoryId) return
      this.activeCategoryId = id
      await this.fetchNews({ reset: true })
    },

    async fetchNews({ reset = false } = {}) {
      if (!this.activeCategoryId) return
      if (this.loading && !reset) return
      if (!reset && this.page > 0 && !this.hasMore) return

      const targetPage = reset ? 1 : this.page + 1
      const requestId = ++listRequestId

      if (reset) {
        this.list = []
        this.page = 0
        this.total = 0
        this.hasMore = true
        this.error = ''
      }

      this.loading = true
      try {
        const data = await newsApi.getList({
          categoryId: this.activeCategoryId,
          page: targetPage,
          pageSize: this.pageSize,
        })
        if (requestId !== listRequestId) return

        const nextList = data?.list || []
        this.list = reset ? nextList : [...this.list, ...nextList]
        this.page = targetPage
        this.total = Number(data?.total) || 0
        this.hasMore = Boolean(data?.hasMore)
      } catch (error) {
        if (requestId === listRequestId) this.error = error.message
        throw error
      } finally {
        if (requestId === listRequestId) this.loading = false
      }
    },

    async fetchNewsDetail(id) {
      const newsId = Number(id)
      if (!newsId) return
      const requestId = ++detailRequestId
      this.detailLoading = true
      this.detailError = ''
      this.detailErrorStatus = null
      this.detail = null

      try {
        const data = await newsApi.getDetail(newsId)
        if (requestId === detailRequestId) this.detail = data
        return data
      } catch (error) {
        if (requestId === detailRequestId) {
          this.detailError = error.message
          this.detailErrorStatus = error.status || null
        }
        throw error
      } finally {
        if (requestId === detailRequestId) this.detailLoading = false
      }
    },

    clearDetail() {
      detailRequestId += 1
      this.detail = null
      this.detailError = ''
      this.detailErrorStatus = null
      this.detailLoading = false
    },
  },
})
