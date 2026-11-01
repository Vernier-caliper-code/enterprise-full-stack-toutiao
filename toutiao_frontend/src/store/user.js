import { defineStore } from 'pinia'

import { DEFAULT_AVATAR, TOKEN_KEY, userApi } from '../config/api'
import { useFavoriteStore } from './modules/favorite'
import { useHistoryStore } from './modules/history'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    userInfo: null,
    initialized: false,
    loading: false,
  }),

  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    displayName: (state) => state.userInfo?.nickname || state.userInfo?.username || '未登录',
    avatar: (state) => state.userInfo?.avatar || DEFAULT_AVATAR,
  },

  actions: {
    setSession(payload) {
      this.token = payload.token
      this.userInfo = payload.userInfo
      this.initialized = true
      localStorage.setItem(TOKEN_KEY, payload.token)
    },

    async login(payload) {
      const data = await userApi.login(payload)
      this.setSession(data)
      return data
    },

    async register(payload) {
      const data = await userApi.register(payload)
      this.setSession(data)
      return data
    },

    async fetchUserInfo() {
      if (!this.token) {
        this.initialized = true
        return null
      }
      if (this.loading) return this.userInfo

      this.loading = true
      try {
        this.userInfo = await userApi.getInfo()
        return this.userInfo
      } finally {
        this.loading = false
        this.initialized = true
      }
    },

    async updateProfile(payload) {
      const data = await userApi.update(payload)
      this.userInfo = data
      return data
    },

    async updatePassword(payload) {
      return userApi.updatePassword(payload)
    },

    clearAuth() {
      this.token = ''
      this.userInfo = null
      this.initialized = true
      localStorage.removeItem(TOKEN_KEY)
      useFavoriteStore().reset()
      useHistoryStore().reset()
    },

    logout() {
      this.clearAuth()
    },
  },
})
