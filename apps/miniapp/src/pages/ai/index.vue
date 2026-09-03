<template>
  <view class="pf-page ai-page">
    <PfPageHeader
      :title="hasFarm ? currentFarmName : '未选择农场'"
      variant="tab"
    />

    <view v-if="!hasFarm" class="ai-empty-farm pf-page-content">
      <view
        class="ai-empty-farm__action pf-card"
        hover-class="pf-card--pressed"
        @tap="openFarms"
      >
        <PfBusinessIcon name="map" />
        <text class="ai-empty-farm__title">选择农场</text>
        <PfRowChevron />
      </view>
    </view>

    <view v-else-if="loadingFarmStatus" class="ai-state">
      <uv-loading-icon mode="circle" color="#286B46" />
    </view>

    <view v-else-if="farmStatusError" class="ai-state pf-page-content">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text class="ai-state__title">{{ farmStatusError }}</text>
      <button class="ai-state__button" @tap="loadFarmStatus">重试</button>
    </view>

    <view v-else-if="!farmAIEnabled" class="ai-state pf-page-content">
      <PfBusinessIcon name="settings" size="empty" />
      <text class="ai-state__title">AI 已关闭</text>
      <button
        v-if="currentFarm?.role === 'OWNER'"
        class="ai-state__button"
        @tap="openFarmSettings"
      >
        前往设置
      </button>
    </view>

    <template v-else>
      <scroll-view
        class="ai-messages"
        scroll-y
        :scroll-into-view="scrollTarget"
        :scroll-with-animation="true"
        @scroll="handleMessageScroll"
        @scrolltoupper="loadOlderMessages"
        @scrolltolower="followMessages = true"
      >
        <view class="ai-messages__content pf-page-content">
          <view v-if="!messages.length" class="ai-suggestions">
            <view class="ai-read-only-notice">
              <text class="ai-read-only-notice__leading">目前仅支持查询</text>
              <text class="ai-read-only-notice__content"> · 新建和记录请使用原有功能</text>
            </view>
            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              class="ai-suggestion pf-tappable"
              @tap="askSuggestion(suggestion)"
            >
              {{ suggestion }}
            </button>
          </view>

          <view
            v-for="message in messages"
            :id="message.id"
            :key="message.id"
            class="ai-message"
            :class="`ai-message--${message.role}`"
          >
            <text class="ai-message__content">{{ message.content }}</text>

            <view
              v-if="message.references?.length"
              class="ai-message__references"
            >
              <view
                v-for="reference in message.references"
                :key="`${reference.kind}-${reference.id}`"
                class="ai-reference pf-tappable"
                @tap="openReference(reference)"
              >
                <text class="ai-reference__label">{{ reference.label }}</text>
                <PfRowChevron />
              </view>
            </view>

            <view
              v-if="message.candidates?.length"
              class="ai-message__candidates"
            >
              <button
                v-for="candidate in message.candidates"
                :key="`${candidate.kind}-${candidate.id}`"
                class="ai-candidate pf-tappable"
                @tap="selectCandidate(candidate)"
              >
                {{ candidate.label }}
              </button>
            </view>
          </view>

          <view v-if="isSending" id="ai-pending" class="ai-pending">
            <uv-loading-icon mode="circle" size="18" color="#286B46" />
          </view>

          <view v-if="loadingOlderMessages" class="ai-history-loading">
            <uv-loading-icon mode="circle" size="16" color="#286B46" />
          </view>

          <view v-if="lastFailedTurn" class="ai-retry">
            <button class="ai-retry__button" @tap="retryLastTurn">
              重新发送
            </button>
          </view>
        </view>
      </scroll-view>

      <view class="ai-composer">
        <textarea
          v-model="draft"
          class="ai-composer__input"
          :maxlength="MAX_MESSAGE_LENGTH"
          :disabled="isSending"
          auto-height
          confirm-type="send"
          placeholder="输入问题"
          placeholder-class="ai-composer__placeholder"
          @confirm="submitMessage"
        />
        <view
          class="ai-composer__new pf-tappable"
          :class="{ 'ai-composer__new--disabled': isSending }"
          :aria-disabled="isSending"
          @tap="startNewConversation"
        >
          <text>＋</text>
        </view>
        <view
          class="ai-composer__send"
          :class="{ 'ai-composer__send--disabled': !canSend }"
          :aria-disabled="!canSend"
          @tap="submitMessage"
        >
          <text>发送</text>
        </view>
      </view>
    </template>

    <view
      v-if="pendingDataNotice"
      class="ai-data-notice-mask"
      @touchmove.stop.prevent
    >
      <view class="ai-data-notice" role="dialog" aria-modal="true">
        <text class="ai-data-notice__title">使用 AI</text>
        <text class="ai-data-notice__content">
          使用 AI 时，你输入的问题，以及回答所需的当前农场业务数据会发送至 DeepSeek API 处理。请勿输入手机号、身份证等与农场管理无关的个人信息。
        </text>
        <view class="ai-data-notice__actions">
          <view
            class="ai-data-notice__action ai-data-notice__action--secondary"
            hover-class="ai-data-notice__action--pressed"
            @tap="cancelDataNotice"
          >
            <text>暂不使用</text>
          </view>
          <view
            class="ai-data-notice__action ai-data-notice__action--primary"
            hover-class="ai-data-notice__action--pressed"
            @tap="acceptDataNotice"
          >
            <text>同意并使用</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfPageHeader from "../../components/PfPageHeader.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import {
  createAIConversation,
  createAITurn,
  type AIReference,
  getAIMessages,
} from "../../services/ai";
import { useAIConversationContext } from "../../services/ai-conversation-context";
import { clearAuthToken } from "../../services/auth";
import { getFarm } from "../../services/farm";
import { toFarmSummary, useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import { useUserContext } from "../../services/user-context";

const AI_NOTICE_VERSION = "v1";
const MAX_MESSAGE_LENGTH = 1000;
const suggestions = ["现在有哪些种养？", "最近做了什么农事？", "有哪些地块？"];

type ChatMessageRole = "user" | "assistant" | "error";

interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
  references?: AIReference[];
  candidates?: AIReference[];
}

interface FailedTurn {
  messageId: string;
  requestMessage: string;
  displayMessage: string;
}

interface PendingDataNotice {
  storageKey: string;
  requestMessage: string;
  displayMessage: string;
}

const { currentFarm, currentFarmName, hasCurrentFarm, selectFarm } =
  useFarmContext();
const { activeConversation, selectAIConversation, clearAIConversation } =
  useAIConversationContext();
const { ensureCurrentUser } = useUserContext();
const hasFarm = hasCurrentFarm;
const messages = ref<ChatMessage[]>([]);
const draft = ref("");
const isSending = ref(false);
const loadingFarmStatus = ref(false);
const farmStatusError = ref("");
const farmAIEnabled = ref(true);
const scrollTarget = ref("");
const lastFailedTurn = ref<FailedTurn | null>(null);
const followMessages = ref(true);
const pendingDataNotice = ref<PendingDataNotice | null>(null);
const conversationMessagePage = ref(1);
const conversationMessageTotal = ref(0);
const loadingOlderMessages = ref(false);
let activeTurn = 0;

const canSend = computed(
  () =>
    Boolean(draft.value.trim()) &&
    draft.value.trim().length <= MAX_MESSAGE_LENGTH &&
    !isSending.value,
);

watch(
  () => currentFarm.value?.id,
  (farmId, previousFarmId) => {
    if (farmId === previousFarmId) return;
    resetConversation();
    clearAIConversation();
    if (farmId) void initializePage();
  },
);

function createMessageId(): string {
  return `ai-message-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function resetConversation(): void {
  activeTurn += 1;
  messages.value = [];
  draft.value = "";
  isSending.value = false;
  lastFailedTurn.value = null;
  pendingDataNotice.value = null;
  conversationMessagePage.value = 1;
  conversationMessageTotal.value = 0;
  loadingOlderMessages.value = false;
  scrollTarget.value = "";
  followMessages.value = true;
}

function startNewConversation(): void {
  if (isSending.value) {
    return;
  }
  if (!activeConversation.value && !messages.value.length) {
    showToast("已经是新对话");
    return;
  }
  resetConversation();
  clearAIConversation();
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function showToast(title: string): void {
  uni.showToast({ title, icon: "none" });
}

function errorText(error: unknown): string {
  if (!(error instanceof ApiRequestError)) return "发送失败，请稍后重试";
  if (error.code === "AI_QUOTA_EXCEEDED") return "今日 AI 提问次数已用完";
  if (error.code === "AI_UPSTREAM_TIMEOUT") return "AI 响应超时，请重试";
  if (error.code === "AI_UPSTREAM_UNAVAILABLE")
    return "AI 服务暂不可用，请稍后重试";
  if (error.code === "AI_NOT_CONFIGURED") return "AI 暂未配置";
  return error.message || "发送失败，请稍后重试";
}

function canRetryTurn(error: unknown): boolean {
  if (!(error instanceof ApiRequestError)) return true;
  if (
    error.code === "AI_QUOTA_EXCEEDED" ||
    error.code === "AI_NOT_CONFIGURED"
  ) {
    return false;
  }
  return (
    error.code === "AI_UPSTREAM_TIMEOUT" ||
    error.code === "AI_UPSTREAM_UNAVAILABLE" ||
    error.statusCode === 0 ||
    error.statusCode >= 500
  );
}

async function loadFarmStatus(): Promise<void> {
  const farmId = currentFarm.value?.id;
  if (!farmId) return;

  loadingFarmStatus.value = true;
  farmStatusError.value = "";
  try {
    const farm = await getFarm(farmId);
    if (currentFarm.value?.id !== farmId) return;
    farmAIEnabled.value = farm.aiEnabled;
    selectFarm(toFarmSummary(farm));
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    farmStatusError.value =
      error instanceof ApiRequestError ? error.message : "农场状态加载失败";
  } finally {
    if (currentFarm.value?.id === farmId) loadingFarmStatus.value = false;
  }
}

function openFarms(): void {
  uni.navigateTo({ url: "/pages/farms/index" });
}

function openFarmSettings(): void {
  if (!currentFarm.value) return;
  uni.navigateTo({ url: `/pages/farms/detail?farmId=${currentFarm.value.id}` });
}

function noticeStorageKey(userId: number): string {
  return `pocket_farm_ai_notice_${userId}_${AI_NOTICE_VERSION}`;
}

async function confirmDataNotice(
  requestMessage: string,
  displayMessage = requestMessage,
): Promise<boolean> {
  try {
    const user = await ensureCurrentUser();
    if (!user) {
      handleUnauthorized();
      return false;
    }
    const storageKey = noticeStorageKey(user.id);
    if (uni.getStorageSync(storageKey) === "accepted") return true;
    pendingDataNotice.value = { storageKey, requestMessage, displayMessage };
    return false;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401)
      handleUnauthorized();
    else showToast("用户信息加载失败，请稍后重试");
    return false;
  }
}

function cancelDataNotice(): void {
  pendingDataNotice.value = null;
}

function acceptDataNotice(): void {
  const pendingNotice = pendingDataNotice.value;
  if (!pendingNotice) return;

  uni.setStorageSync(pendingNotice.storageKey, "accepted");
  pendingDataNotice.value = null;
  if (draft.value.trim() === pendingNotice.displayMessage)
    draft.value = "";
  void sendTurn(pendingNotice.requestMessage, pendingNotice.displayMessage);
}

async function loadActiveConversation(): Promise<void> {
  const conversation = activeConversation.value;
  const farm = currentFarm.value;
  if (!conversation || !farm || conversation.farmId !== farm.id) return;

  try {
    const page = await getAIMessages(conversation.id);
    if (activeConversation.value?.id !== conversation.id) return;
    messages.value = page.items.map((item) => ({
      id: `ai-message-${item.id}`,
      role: item.role,
      content: item.content,
      references: item.references,
      candidates: item.candidates,
    }));
    conversationMessagePage.value = page.page;
    conversationMessageTotal.value = page.total;
    lastFailedTurn.value = null;
    followMessages.value = true;
    const lastMessage = messages.value.at(-1);
    if (lastMessage) scrollToMessage(lastMessage.id);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    showToast(error instanceof ApiRequestError ? error.message : "对话加载失败");
  }
}

async function loadOlderMessages(): Promise<void> {
  const conversation = activeConversation.value;
  if (
    !conversation ||
    loadingOlderMessages.value ||
    messages.value.length >= conversationMessageTotal.value
  ) {
    return;
  }
  loadingOlderMessages.value = true;
  try {
    const page = await getAIMessages(conversation.id, conversationMessagePage.value + 1);
    if (activeConversation.value?.id !== conversation.id) return;
    messages.value = [
      ...page.items.map((item) => ({
        id: `ai-message-${item.id}`,
        role: item.role,
        content: item.content,
        references: item.references,
        candidates: item.candidates,
      })),
      ...messages.value,
    ];
    conversationMessagePage.value = page.page;
    conversationMessageTotal.value = page.total;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    showToast(error instanceof ApiRequestError ? error.message : "更多对话加载失败");
  } finally {
    loadingOlderMessages.value = false;
  }
}

async function ensureConversation(farmId: number): Promise<number> {
  const active = activeConversation.value;
  if (active?.farmId === farmId) return active.id;
  const conversation = await createAIConversation(farmId);
  selectAIConversation(conversation);
  return conversation.id;
}

async function initializePage(): Promise<void> {
  await loadFarmStatus();
  await loadActiveConversation();
}

function scrollToMessage(messageId: string): void {
  if (!followMessages.value) return;
  nextTick(() => {
    scrollTarget.value = messageId;
  });
}

function handleMessageScroll(event: { detail: { deltaY?: number } }): void {
  if ((event.detail.deltaY || 0) < 0) followMessages.value = false;
}

async function sendTurn(
  requestMessage: string,
  displayMessage = requestMessage,
  existingMessageId?: string,
): Promise<void> {
  const farm = currentFarm.value;
  if (!farm || !farmAIEnabled.value || isSending.value) return;

  const turn = ++activeTurn;
  let messageId = existingMessageId;
  let conversationId: number;
  try {
    conversationId = await ensureConversation(farm.id);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    showToast(error instanceof ApiRequestError ? error.message : "新建对话失败");
    return;
  }
  if (turn !== activeTurn || currentFarm.value?.id !== farm.id) return;
  if (!messageId) {
    messageId = createMessageId();
    messages.value.push({
      id: messageId,
      role: "user",
      content: displayMessage,
    });
  }
  lastFailedTurn.value = null;
  followMessages.value = true;
  scrollToMessage(messageId);
  isSending.value = true;

  try {
    const result = await createAITurn({
      conversationId,
      message: requestMessage,
    });
    if (turn !== activeTurn || currentFarm.value?.id !== farm.id) return;
    const responseId = createMessageId();
    messages.value.push({
      id: responseId,
      role: "assistant",
      content: result.answer,
      references: result.references,
      candidates: result.candidates,
    });
    conversationMessageTotal.value += 2;
    scrollToMessage(responseId);
  } catch (error) {
    if (turn !== activeTurn || currentFarm.value?.id !== farm.id) return;
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    if (error instanceof ApiRequestError && error.code === "AI_NOT_ENABLED") {
      farmAIEnabled.value = false;
      return;
    }
    const errorId = createMessageId();
    messages.value.push({
      id: errorId,
      role: "error",
      content: errorText(error),
    });
    if (canRetryTurn(error)) {
      lastFailedTurn.value = { messageId, requestMessage, displayMessage };
    }
    scrollToMessage(errorId);
  } finally {
    if (turn === activeTurn && currentFarm.value?.id === farm.id)
      isSending.value = false;
  }
}

async function submitMessage(): Promise<void> {
  const message = draft.value.trim();
  if (!message || message.length > MAX_MESSAGE_LENGTH || isSending.value)
    return;
  if (!(await confirmDataNotice(message))) return;
  draft.value = "";
  await sendTurn(message);
}

async function askSuggestion(suggestion: string): Promise<void> {
  if (isSending.value || !(await confirmDataNotice(suggestion))) return;
  await sendTurn(suggestion);
}

async function retryLastTurn(): Promise<void> {
  const failedTurn = lastFailedTurn.value;
  if (!failedTurn || isSending.value) return;
  await sendTurn(
    failedTurn.requestMessage,
    failedTurn.displayMessage,
    failedTurn.messageId,
  );
}

async function selectCandidate(candidate: AIReference): Promise<void> {
  if (isSending.value) return;
  const requestMessage = `我选择“${candidate.label}”（ID：${candidate.id}）。请继续查询。`;
  await sendTurn(requestMessage, `选择：${candidate.label}`);
}

function openReference(reference: AIReference): void {
  uni.navigateTo({ url: reference.route });
}

onShow(() => {
  void initializePage();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.ai-page {
  display: flex;
  height: 100vh;
  min-height: 0;
  flex-direction: column;
  overflow: hidden;
}
.ai-messages {
  min-height: 0;
  flex: 1;
}
.ai-messages__content {
  display: flex;
  min-height: 100%;
  box-sizing: border-box;
  flex-direction: column;
}
.ai-suggestions {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
  padding-top: $pf-space-3;
}
.ai-read-only-notice {
  min-height: 48rpx;
  box-sizing: border-box;
  padding: 8rpx 0;
  font-size: 24rpx;
  line-height: 1.5;
}
.ai-read-only-notice__leading {
  color: $pf-color-primary;
  font-weight: 600;
}
.ai-read-only-notice__content {
  color: $pf-color-text-muted;
}
.ai-suggestion,
.ai-candidate,
.ai-state__button,
.ai-retry__button {
  margin: 0;
  border: 0;
  background: $pf-color-surface;
  color: $pf-color-primary;
  font-size: 26rpx;
  font-weight: 600;
  line-height: 1.4;
}
.ai-suggestion {
  padding: 24rpx;
  border: 0;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  text-align: left;
}
.ai-suggestion::after {
  border: 0;
}
.ai-message {
  display: flex;
  max-width: 86%;
  box-sizing: border-box;
  flex-direction: column;
  margin-top: $pf-space-3;
}
.ai-message--user {
  align-self: flex-end;
  margin-left: auto;
}
.ai-message--assistant,
.ai-message--error {
  align-self: flex-start;
}
.ai-message__content {
  display: block;
  padding: 22rpx 24rpx;
  border-radius: $pf-radius-control;
  color: $pf-color-text;
  font-size: 27rpx;
  line-height: 1.55;
  white-space: pre-wrap;
}
.ai-message--user .ai-message__content {
  background: $pf-color-primary;
  color: $pf-color-surface;
}
.ai-message--assistant .ai-message__content {
  background: $pf-color-surface;
}
.ai-message--error .ai-message__content {
  background: $pf-color-danger-soft;
  color: $pf-color-danger;
}
.ai-message__references,
.ai-message__candidates {
  display: flex;
  flex-direction: column;
  gap: $pf-space-1;
  margin-top: $pf-space-2;
}
.ai-reference {
  display: flex;
  min-height: 72rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 18rpx;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}
.ai-reference__label {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ai-reference .pf-row-chevron {
  width: 28rpx;
  height: 28rpx;
  margin-left: 10rpx;
  opacity: 0.5;
}
.ai-candidate {
  min-height: 72rpx;
  padding: 0 18rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  text-align: left;
}
.ai-pending {
  display: flex;
  width: 80rpx;
  height: 64rpx;
  align-items: center;
  justify-content: center;
  margin-top: $pf-space-3;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}
.ai-history-loading {
  display: flex;
  height: 48rpx;
  align-items: center;
  justify-content: center;
}
.ai-retry {
  margin-top: $pf-space-2;
}
.ai-retry__button {
  padding: 12rpx 4rpx;
}
.ai-composer {
  display: flex;
  box-sizing: border-box;
  align-items: flex-end;
  padding: $pf-space-2 $pf-space-page-x
    calc($pf-space-2 + env(safe-area-inset-bottom));
  border-top: 1rpx solid $pf-color-divider;
  background: $pf-color-surface;
}
.ai-composer__input {
  display: block;
  min-width: 0;
  min-height: 48rpx;
  flex: 1;
  padding: 14rpx 0;
  color: $pf-color-text;
  font-size: 27rpx;
  line-height: 1.45;
}
.ai-composer__placeholder {
  color: $pf-color-text-muted;
}
.ai-composer__new {
  display: flex;
  width: 64rpx;
  height: 64rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-left: $pf-space-2;
  color: $pf-color-primary;
  font-size: 38rpx;
  font-weight: 400;
  line-height: 1;
}
.ai-composer__new--disabled {
  color: $pf-color-text-muted;
}
.ai-composer__send {
  position: relative;
  z-index: 1;
  display: flex;
  min-width: 104rpx;
  height: 64rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin: 0 0 0 $pf-space-2;
  border-radius: $pf-radius-control;
  background: $pf-color-primary;
  color: $pf-color-surface;
  font-size: 25rpx;
  font-weight: 650;
}
.ai-composer__send--disabled {
  background: $pf-color-border;
  color: $pf-color-text-muted;
  opacity: 1;
}
.ai-state {
  display: flex;
  min-height: 300rpx;
  box-sizing: border-box;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.ai-state__title {
  display: block;
  margin-top: $pf-space-3;
  color: $pf-color-text;
  font-size: 30rpx;
  font-weight: 650;
}
.ai-state__button {
  min-width: 200rpx;
  min-height: 72rpx;
  margin-top: $pf-space-4;
  border: 1rpx solid $pf-color-primary;
  border-radius: $pf-radius-control;
}
.ai-empty-farm {
  padding-top: $pf-space-3;
}
.ai-empty-farm__action {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 $pf-space-4;
}
.ai-empty-farm__title {
  flex: 1;
  margin-left: $pf-space-3;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 600;
}
.ai-data-notice-mask {
  position: fixed;
  z-index: 10;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $pf-space-6;
  background: rgba(23, 35, 27, 0.38);
}
.ai-data-notice {
  width: 100%;
  max-width: 620rpx;
  overflow: hidden;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-raised;
}
.ai-data-notice__title {
  display: block;
  padding: $pf-space-5 $pf-space-5 0;
  color: $pf-color-text;
  font-size: 32rpx;
  font-weight: 650;
  text-align: center;
}
.ai-data-notice__content {
  display: block;
  padding: $pf-space-3 $pf-space-5 $pf-space-5;
  color: $pf-color-text-secondary;
  font-size: 27rpx;
  line-height: 1.65;
}
.ai-data-notice__actions {
  display: flex;
  min-height: 92rpx;
  border-top: 1rpx solid $pf-color-divider;
}
.ai-data-notice__action {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: 28rpx;
  font-weight: 600;
}
.ai-data-notice__action--primary {
  border-left: 1rpx solid $pf-color-divider;
  color: $pf-color-primary;
}
.ai-data-notice__action--pressed {
  background: $pf-color-surface-muted;
}
</style>
