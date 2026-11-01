<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { sendAiChat } from '../config/api'

const SYSTEM_PROMPT = '你是新闻资讯助手，请使用简洁中文回答问题。'
const chatBody = ref(null)
const input = ref('')
const sending = ref(false)
const keyboardOpen = ref(false)
let messageId = 0
let viewportFrame = 0

const messages = ref([
  {
    id: ++messageId,
    role: 'assistant',
    content: '你好！我是AI助手，有什么可以帮助你的吗？',
    status: 'success',
  },
])

function createMessage(role, content, status = 'success') {
  return { id: ++messageId, role, content, status }
}

async function scrollToBottom() {
  await nextTick()
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

function validConversation(history) {
  return history
    .filter((message) => message.status === 'success')
    .map(({ role, content }) => ({ role, content }))
}

async function requestReply(assistantMessage) {
  sending.value = true
  assistantMessage.status = 'loading'
  assistantMessage.content = '正在思考...'
  await scrollToBottom()

  try {
    const content = await sendAiChat([
      { role: 'system', content: SYSTEM_PROMPT },
      ...assistantMessage.conversation,
    ])
    assistantMessage.content = content
    assistantMessage.status = 'success'
  } catch (error) {
    assistantMessage.content = error.message
    assistantMessage.status = 'error'
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}

async function submit() {
  const content = input.value.trim()
  if (!content || sending.value) return

  const userMessage = createMessage('user', content)
  messages.value.push(userMessage)
  input.value = ''

  const conversation = validConversation(messages.value)
  const assistantMessage = createMessage('assistant', '正在思考...', 'loading')
  assistantMessage.conversation = conversation
  messages.value.push(assistantMessage)

  await requestReply(assistantMessage)
}

function retry(message) {
  if (sending.value) return
  requestReply(message)
}

function syncViewport() {
  if (viewportFrame) return
  viewportFrame = window.requestAnimationFrame(() => {
    viewportFrame = 0
    const viewport = window.visualViewport
    keyboardOpen.value = Boolean(viewport && viewport.height < window.innerHeight - 120)
    if (keyboardOpen.value) scrollToBottom()
  })
}

function onFocus() {
  window.setTimeout(syncViewport, 180)
}

function onBlur() {
  window.setTimeout(syncViewport, 180)
}

onMounted(() => {
  window.visualViewport?.addEventListener('resize', syncViewport)
  window.visualViewport?.addEventListener('scroll', syncViewport)
})

onBeforeUnmount(() => {
  window.visualViewport?.removeEventListener('resize', syncViewport)
  window.visualViewport?.removeEventListener('scroll', syncViewport)
  window.cancelAnimationFrame(viewportFrame)
})

function onKeydown(event) {
  if (event.isComposing || event.shiftKey) return
  event.preventDefault()
  submit()
}
</script>

<template>
  <div class="page ai-page" :class="{ 'ai-page--keyboard': keyboardOpen }">
    <van-nav-bar title="AI问答" />

    <div ref="chatBody" class="chat-body" role="log" aria-live="polite">
      <div
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="message.role === 'user' ? 'message-row--user' : 'message-row--assistant'"
      >
        <div
          class="message-bubble"
          :class="{
            'message-bubble--user': message.role === 'user',
            'message-bubble--error': message.status === 'error',
          }"
        >
          <template v-if="message.status === 'loading'">
            <span class="thinking">
              正在思考
              <span class="thinking-dots" aria-hidden="true"><i /><i /><i /></span>
            </span>
          </template>
          <template v-else>
            <div class="message-content">{{ message.content }}</div>
            <button
              v-if="message.status === 'error'"
              class="retry-button"
              type="button"
              :disabled="sending"
              @click="retry(message)"
            >
              <van-icon name="replay" size="14" />
              重试
            </button>
          </template>
        </div>
      </div>
    </div>

    <form class="composer" @submit.prevent="submit">
      <van-field
        v-model="input"
        class="composer-field"
        type="textarea"
        rows="1"
        autosize
        maxlength="1000"
        placeholder="输入你的问题..."
        :disabled="sending"
        @keydown.enter.exact="onKeydown"
        @focus="onFocus"
        @blur="onBlur"
      />
      <van-button
        class="send-button"
        type="primary"
        round
        size="small"
        :disabled="!input.trim() || sending"
        :loading="sending"
        loading-text=""
        @click="submit"
      >
        发送
      </van-button>
    </form>
  </div>
</template>

<style scoped>
.ai-page {
  display: flex;
  width: 100%;
  height: calc(100dvh - 50px - env(safe-area-inset-bottom));
  min-height: 0;
  flex-direction: column;
  overflow: hidden;
  background: var(--app-bg);
}

.ai-page :deep(.van-nav-bar) {
  flex: 0 0 auto;
}

.chat-body {
  min-height: 0;
  flex: 1 1 auto;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 16px 14px 24px;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-y;
  scrollbar-width: none;
}

.chat-body::-webkit-scrollbar {
  display: none;
}

.message-row {
  display: flex;
  margin-bottom: 14px;
}

.message-row--user {
  justify-content: flex-end;
}

.message-row--assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 82%;
  padding: 11px 14px;
  border: 1px solid var(--app-border);
  border-radius: 4px 14px 14px;
  background: var(--app-surface);
  color: var(--app-text);
  font-size: 15px;
  line-height: 1.65;
  box-shadow: 0 2px 8px rgb(17 24 39 / 4%);
}

.message-bubble--user {
  border-color: var(--van-primary-color);
  border-radius: 14px 4px 14px 14px;
  background: var(--van-primary-color);
  color: #ffffff;
}

.message-bubble--error {
  border-color: rgb(238 10 36 / 30%);
}

.message-content {
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.retry-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding: 4px 0;
  border: 0;
  background: transparent;
  color: var(--van-primary-color);
  font-size: 13px;
  cursor: pointer;
}

.thinking {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--app-text-secondary);
}

.thinking-dots {
  display: inline-flex;
  gap: 3px;
}

.thinking-dots i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--app-text-secondary);
  animation: thinking-bounce 1.1s infinite ease-in-out;
}

.thinking-dots i:nth-child(2) {
  animation-delay: 0.14s;
}

.thinking-dots i:nth-child(3) {
  animation-delay: 0.28s;
}

.composer {
  position: relative;
  z-index: 2;
  display: flex;
  flex: 0 0 auto;
  align-items: flex-end;
  gap: 10px;
  padding: 10px 12px calc(10px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--app-border);
  background: var(--app-surface);
}

.composer-field {
  min-width: 0;
  flex: 1;
  padding: 7px 12px;
  border-radius: 18px;
  background: var(--app-bg);
}

.composer-field :deep(.van-field__control) {
  max-height: 92px;
  line-height: 1.5;
}

.send-button {
  min-width: 64px;
  height: 36px;
  flex: 0 0 auto;
}

.ai-page--keyboard .composer {
  padding-bottom: 10px;
}
.ai-page--keyboard .chat-body {
  padding-bottom: 12px;
}

@supports (height: 100svh) {
  .ai-page {
    height: calc(100svh - 50px - env(safe-area-inset-bottom));
    min-height: 0;
  }
}

@keyframes thinking-bounce {
  0%,
  60%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-3px);
  }
}
</style>

