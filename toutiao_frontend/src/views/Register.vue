<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { DEFAULT_AVATAR } from '../config/api'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const confirmError = ref('')

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/login')
}

async function submit(values) {
  if (loading.value) return
  confirmError.value = ''
  errorMessage.value = ''

  if (values.password !== values.confirmPassword) {
    confirmError.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    await userStore.register({
      username: values.username.trim(),
      password: values.password,
    })
    router.replace('/my')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

function submitForm() {
  formRef.value?.submit()
}
</script>

<template>
  <div class="page auth-page">
    <van-nav-bar title="用户注册" left-arrow @click-left="goBack" />

    <main class="auth-main">
      <div class="brand-block">
        <img class="brand-avatar" :src="DEFAULT_AVATAR" alt="新闻资讯" />
        <h1>新闻资讯</h1>
        <p>创建账号，收藏你关注的内容</p>
      </div>

      <van-form ref="formRef" class="auth-card" @submit="submit">
        <van-field
          v-model="username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          autocomplete="username"
          :disabled="loading"
          :rules="[{ required: true, message: '请输入用户名' }]"
          @keyup.enter="submitForm"
        />
        <van-field
          v-model="password"
          name="password"
          label="密码"
          :type="showPassword ? 'text' : 'password'"
          placeholder="请输入密码"
          autocomplete="new-password"
          :disabled="loading"
          :right-icon="showPassword ? 'eye-o' : 'closed-eye'"
          :rules="[{ required: true, message: '请输入密码' }]"
          @click-right-icon="showPassword = !showPassword"
          @keyup.enter="submitForm"
        />
        <van-field
          v-model="confirmPassword"
          name="confirmPassword"
          label="确认密码"
          :type="showConfirmPassword ? 'text' : 'password'"
          placeholder="请再次输入密码"
          autocomplete="new-password"
          :disabled="loading"
          :error-message="confirmError"
          :right-icon="showConfirmPassword ? 'eye-o' : 'closed-eye'"
          :rules="[{ required: true, message: '请再次输入密码' }]"
          @update:model-value="confirmError = ''"
          @click-right-icon="showConfirmPassword = !showConfirmPassword"
          @keyup.enter="submitForm"
        />
      </van-form>

      <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>

      <van-button
        class="auth-submit"
        type="primary"
        round
        block
        native-type="submit"
        :loading="loading"
        loading-text="注册中..."
        @click="submitForm"
      >
        注册
      </van-button>

      <p class="auth-switch">
        已有账号？
        <button type="button" @click="router.push('/login')">去登录</button>
      </p>
    </main>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100dvh;
  background: var(--app-bg);
}

.auth-main {
  padding: 20px 0 40px;
}

.brand-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 16px 24px;
}

.brand-avatar {
  width: 76px;
  height: 76px;
  border: 3px solid var(--app-surface);
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 8px 22px rgb(17 24 39 / 12%);
}

.brand-block h1 {
  margin: 14px 0 0;
  color: var(--app-text);
  font-size: 24px;
  font-weight: 700;
}

.brand-block p {
  margin: 7px 0 0;
  color: var(--app-text-secondary);
  font-size: 13px;
}

.auth-card {
  width: calc(90% - 12px);
  max-width: 390px;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 12px;
  background: var(--app-surface);
  box-shadow: 0 8px 28px rgb(17 24 39 / 6%);
}

.auth-card :deep(.van-cell) {
  padding: 16px;
}

.auth-card :deep(.van-field__label) {
  width: 72px;
  font-weight: 500;
}

.form-error {
  width: calc(90% - 12px);
  max-width: 390px;
  margin: 10px auto 0;
  color: var(--app-danger);
  font-size: 13px;
  line-height: 1.5;
  text-align: center;
}

.auth-submit {
  width: calc(90% - 12px);
  max-width: 390px;
  height: 48px;
  margin: 20px auto 0;
  font-size: 16px;
}

.auth-switch {
  margin: 18px 0 0;
  color: var(--app-text-secondary);
  font-size: 13px;
  text-align: center;
}

.auth-switch button {
  padding: 4px;
  border: 0;
  background: transparent;
  color: var(--van-primary-color);
  cursor: pointer;
}

@media (prefers-reduced-motion: reduce) {
  .brand-avatar,
  .auth-card {
    box-shadow: none;
  }
}
</style>
