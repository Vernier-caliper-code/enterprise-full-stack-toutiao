import { createRouter, createWebHistory } from 'vue-router'

import { useUserStore } from '../store/user'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页', showTabBar: true, activeTab: 'home' },
  },
  {
    path: '/category',
    name: 'category',
    component: () => import('../views/Category.vue'),
    meta: { title: '全部分类', showTabBar: true, activeTab: 'home' },
  },
  {
    path: '/ai-chat',
    name: 'ai-chat',
    component: () => import('../views/AIChat.vue'),
    meta: { title: 'AI问答', showTabBar: true, activeTab: 'ai' },
  },
  {
    path: '/my',
    name: 'my',
    component: () => import('../views/My.vue'),
    meta: { title: '我的', showTabBar: true, activeTab: 'my' },
  },
  {
    path: '/news/:id',
    name: 'news-detail',
    component: () => import('../views/NewsDetail.vue'),
    meta: { title: '新闻详情', showTabBar: false },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { title: '用户登录', showTabBar: false },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue'),
    meta: { title: '用户注册', showTabBar: false },
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: () => import('../views/Favorite.vue'),
    meta: { title: '我的收藏', requiresAuth: true, showTabBar: false },
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('../views/History.vue'),
    meta: { title: '浏览历史', requiresAuth: true, showTabBar: false },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '个人信息', requiresAuth: true, showTabBar: false },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/Settings.vue'),
    meta: { title: '设置', showTabBar: false },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
    return '/my'
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - 新闻资讯` : '新闻资讯'
})

export default router
