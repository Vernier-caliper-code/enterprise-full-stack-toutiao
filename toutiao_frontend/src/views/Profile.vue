<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { showToast } from 'vant'
import { useRouter } from 'vue-router'

import { DEFAULT_AVATAR } from '../config/api'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const loadError = ref('')
const editorVisible = ref(false)
const editorType = ref('avatar')
const saving = ref(false)
const editorError = ref('')
const avatarDraft = ref('')
const bioDraft = ref('')
const passwordDraft = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const user = computed(() => userStore.userInfo)
const editorTitle = computed(() => {
  if (editorType.value === 'avatar') return '修改头像'
  if (editorType.value === 'bio') return '编辑个人简介'
  return '修改密码'
})

async function loadUser() {
  loadError.value = ''
  try {
    await userStore.fetchUserInfo()
  } catch (error) {
    loadError.value = error.message
  }
}

function goBack() {
  router.push('/my')
}

function openEditor(type) {
  editorType.value = type
  editorError.value = ''
  if (type === 'avatar') avatarDraft.value = user.value?.avatar || DEFAULT_AVATAR
  if (type === 'bio') bioDraft.value = user.value?.bio || ''
  if (type === 'password') {
    passwordDraft.oldPassword = ''
    passwordDraft.newPassword = ''
    passwordDraft.confirmPassword = ''
  }
  editorVisible.value = true
}

async function saveEditor() {
  if (saving.value) return
  editorError.value = ''

  if (editorType.value === 'avatar' && !avatarDraft.value.trim()) {
    editorError.value = '请输入头像 URL'
    return
  }
  if (editorType.value === 'password') {
    if (!passwordDraft.oldPassword || !passwordDraft.newPassword) {
      editorError.value = '请填写旧密码和新密码'
      return
    }
    if (passwordDraft.newPassword !== passwordDraft.confirmPassword) {
      editorError.value = '两次输入的新密码不一致'
      return
    }
  }

  saving.value = true
  try {
    if (editorType.value === 'avatar') {
      await userStore.updateProfile({ avatar: avatarDraft.value.trim() })
      showToast('头像更新成功')
    } else if (editorType.value === 'bio') {
      await userStore.updateProfile({ bio: bioDraft.value.trim() })
      showToast('个人简介更新成功')
    } else {
      await userStore.updatePassword({
        oldPassword: passwordDraft.oldPassword,
        newPassword: passwordDraft.newPassword,
      })
      showToast('密码修改成功')
    }
    editorVisible.value = false
  } catch (error) {
    editorError.value = error.message
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (!userStore.userInfo) loadUser()
})
</script>

<template>
  <div class="page profile-page">
    <van-nav-bar title="个人信息" left-arrow @click-left="goBack" />

    <main class="profile-content">
      <div v-if="userStore.loading && !user" class="profile-loading">
        <van-loading size="28" vertical>正在加载资料...</van-loading>
      </div>

      <div v-else-if="loadError && !user" class="state-panel state-panel--transparent">
        <van-icon name="warning-o" size="42" color="var(--app-text-weak)" />
        <h2 class="state-title">资料加载失败</h2>
        <p class="state-message">{{ loadError }}</p>
        <van-button type="primary" round size="small" @click="loadUser">重新加载</van-button>
      </div>

      <template v-else-if="user">
        <section class="profile-group">
          <van-cell-group>
            <van-cell center is-link @click="openEditor('avatar')">
              <template #title>
                <span class="cell-label">头像</span>
              </template>
              <template #value>
                <van-image class="profile-avatar" round :src="user.avatar || DEFAULT_AVATAR">
                  <template #error>
                    <div class="avatar-fallback"><van-icon name="user-o" size="24" /></div>
                  </template>
                </van-image>
              </template>
            </van-cell>
          </van-cell-group>
        </section>

        <section class="profile-group">
          <van-cell-group>
            <van-cell title="用户名" :value="user.username" />
            <van-cell title="账号 ID" :value="`ID: ${user.id}`" />
            <van-cell
              title="个人简介"
              :label="user.bio || '这个人很懒，什么都没留下'"
              is-link
              center
              @click="openEditor('bio')"
            />
          </van-cell-group>
        </section>

        <section class="profile-group">
          <van-cell-group>
            <van-cell title="修改密码" is-link @click="openEditor('password')" />
          </van-cell-group>
        </section>
      </template>
    </main>

    <van-popup
      v-model:show="editorVisible"
      position="bottom"
      round
      closeable
      class="editor-popup"
    >
      <div class="editor-panel">
        <h2 class="editor-title">{{ editorTitle }}</h2>

        <div v-if="editorType === 'avatar'" class="avatar-editor">
          <img class="avatar-preview" :src="avatarDraft || DEFAULT_AVATAR" alt="头像预览" />
          <button class="default-avatar-button" type="button" @click="avatarDraft = DEFAULT_AVATAR">
            使用默认猫头像
          </button>
          <van-field
            v-model="avatarDraft"
            label="头像 URL"
            placeholder="https://example.com/avatar.jpg"
            clearable
          />
        </div>

        <van-field
          v-else-if="editorType === 'bio'"
          v-model="bioDraft"
          type="textarea"
          rows="4"
          autosize
          maxlength="200"
          show-word-limit
          placeholder="介绍一下自己"
          class="bio-field"
        />

        <div v-else class="password-editor">
          <van-field
            v-model="passwordDraft.oldPassword"
            type="password"
            label="旧密码"
            placeholder="请输入当前密码"
            autocomplete="current-password"
          />
          <van-field
            v-model="passwordDraft.newPassword"
            type="password"
            label="新密码"
            placeholder="请输入新密码"
            autocomplete="new-password"
          />
          <van-field
            v-model="passwordDraft.confirmPassword"
            type="password"
            label="确认密码"
            placeholder="请再次输入新密码"
            autocomplete="new-password"
          />
        </div>

        <p v-if="editorError" class="editor-error" role="alert">{{ editorError }}</p>

        <van-button
          class="save-button"
          type="primary"
          round
          block
          :loading="saving"
          :disabled="saving"
          @click="saveEditor"
        >
          保存
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100dvh;
  background: var(--app-bg);
}

.profile-content {
  padding: 16px 0 32px;
}

.profile-loading {
  display: grid;
  min-height: 50vh;
  place-items: center;
}

.profile-group {
  margin-bottom: 16px;
  overflow: hidden;
}

.profile-group :deep(.van-cell-group) {
  width: calc(100% - 32px);
  margin: 0 16px;
  overflow: hidden;
  border-radius: 8px;
}

.profile-group :deep(.van-cell) {
  min-height: 56px;
  align-items: center;
}

.cell-label {
  color: var(--app-text);
  font-size: 15px;
}

.profile-avatar {
  width: 56px;
  height: 56px;
  overflow: hidden;
  vertical-align: middle;
  border-radius: 50%;
  background: var(--app-placeholder);
}

.profile-avatar :deep(img) {
  width: 100%;
  height: 100%;
}

.avatar-fallback {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  background: var(--app-placeholder);
  color: var(--app-text-secondary);
}

.editor-popup {
  left: 50%;
  right: auto;
  width: min(100vw, 480px);
  margin-left: -240px;
}

.editor-panel {
  padding: 24px 16px calc(20px + env(safe-area-inset-bottom));
}

.editor-title {
  margin: 0 0 20px;
  padding: 0 12px;
  color: var(--app-text);
  font-size: 18px;
  font-weight: 600;
}

.avatar-editor {
  padding: 0 12px;
}

.avatar-preview {
  display: block;
  width: 80px;
  height: 80px;
  margin: 0 auto 14px;
  border-radius: 50%;
  object-fit: cover;
  background: var(--app-placeholder);
}

.default-avatar-button {
  display: block;
  margin: 0 auto 18px;
  padding: 6px 10px;
  border: 0;
  background: transparent;
  color: var(--van-primary-color);
  font-size: 13px;
  cursor: pointer;
}

.avatar-editor :deep(.van-cell),
.password-editor :deep(.van-cell),
.bio-field {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: var(--app-bg);
}

.password-editor {
  display: grid;
  gap: 10px;
}

.bio-field {
  margin: 0 12px;
  width: calc(100% - 24px);
}

.editor-error {
  margin: 12px 12px 0;
  color: var(--app-danger);
  font-size: 13px;
  line-height: 1.5;
}

.save-button {
  width: calc(100% - 24px);
  height: 46px;
  margin: 18px 12px 0;
}

@media (max-width: 520px) {
  .editor-popup {
    width: 100vw;
    margin-left: -50vw;
  }
}
</style>

