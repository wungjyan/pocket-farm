<template>
  <view class="pf-page conversations-page">
    <view class="pf-page-content">
      <view v-if="loading" class="conversations-state pf-card">
        <uv-loading-icon mode="circle" color="#006C49" />
        <text>正在加载对话</text>
      </view>

      <view v-else-if="loadError" class="conversations-state pf-card">
        <text>{{ loadError }}</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 24rpx; border-radius: 16rpx;"
          @click="loadConversations"
        >
          重试
        </uv-button>
      </view>

      <view v-else-if="conversations.length" class="conversation-content">
        <view class="conversation-list pf-card">
          <view
            v-for="conversation in conversations"
            :key="conversation.id"
            class="conversation-row pf-tappable"
            @tap="openConversation(conversation)"
          >
            <view class="conversation-row__copy">
              <text class="conversation-row__title">{{ conversation.title }}</text>
              <text class="conversation-row__meta">
                {{ conversation.farmName }} · {{ dateLabel(conversation.updatedAt) }}
              </text>
            </view>
            <view
              class="conversation-row__delete"
              hover-class="conversation-row__delete--pressed"
              @tap.stop="confirmDelete(conversation)"
            >
              <view class="conversation-row__delete-icon">
                <uv-icon name="trash" size="18" color="#A9433B" />
              </view>
            </view>
            <PfRowChevron />
          </view>
        </view>
        <uv-load-more
          v-if="hasMore() || loadingMore"
          :status="loadingMore ? 'loading' : 'nomore'"
          icon-color="#006C49"
          color="#748178"
        />
      </view>

      <view v-else class="conversations-empty">
        <view class="conversations-empty__icon">
          <image
            class="conversations-empty__icon-image"
            src="/static/icons/lucide/sparkles.svg"
            mode="aspectFit"
          />
        </view>
        <text class="conversations-empty__title">暂无对话</text>
        <uv-button
          type="primary"
          shape="square"
          custom-style="width: 208rpx; height: 80rpx; margin-top: 24rpx; border-radius: 16rpx;"
          @click="startNewConversation"
        >
          开始对话
        </uv-button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onReachBottom, onShow } from "@dcloudio/uni-app";
import PfRowChevron from "../../components/PfRowChevron.vue";
import {
  deleteAIConversation,
  getAIConversations,
  type AIConversation,
} from "../../services/ai";
import { useAIConversationContext } from "../../services/ai-conversation-context";
import { clearAuthToken } from "../../services/auth";
import { getFarm } from "../../services/farm";
import { toFarmSummary, useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";

const conversations = ref<AIConversation[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const loadError = ref("");
const page = ref(1);
const total = ref(0);
const { activeConversation, selectAIConversation, clearAIConversation } =
  useAIConversationContext();
const { currentFarm, selectFarmAndPersist } = useFarmContext();

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function dateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate(),
  ).padStart(2, "0")}`;
}

async function loadConversations(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    const result = await getAIConversations();
    conversations.value = result.items;
    page.value = result.page;
    total.value = result.total;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "对话加载失败";
  } finally {
    loading.value = false;
  }
}

const hasMore = () => conversations.value.length < total.value;

async function loadMoreConversations(): Promise<void> {
  if (loading.value || loadingMore.value || !hasMore() || loadError.value) return;
  loadingMore.value = true;
  try {
    const result = await getAIConversations(page.value + 1);
    conversations.value = [...conversations.value, ...result.items];
    page.value = result.page;
    total.value = result.total;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    uni.showToast({
      title: error instanceof ApiRequestError ? error.message : "更多对话加载失败",
      icon: "none",
    });
  } finally {
    loadingMore.value = false;
  }
}

async function openConversation(conversation: AIConversation): Promise<void> {
  try {
    if (currentFarm.value?.id !== conversation.farmId) {
      const farm = await getFarm(conversation.farmId);
      await selectFarmAndPersist(toFarmSummary(farm));
    }
    selectAIConversation(conversation);
    uni.switchTab({ url: "/pages/ai/index" });
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    uni.showToast({
      title: error instanceof ApiRequestError ? error.message : "打开对话失败",
      icon: "none",
    });
  }
}

function startNewConversation(): void {
  clearAIConversation();
  uni.switchTab({ url: "/pages/ai/index" });
}

function confirmDelete(conversation: AIConversation): void {
  uni.showModal({
    title: "删除对话",
    content: conversation.title,
    confirmColor: "#A9433B",
    success: (result) => {
      if (result.confirm) void removeConversation(conversation);
    },
  });
}

async function removeConversation(conversation: AIConversation): Promise<void> {
  try {
    await deleteAIConversation(conversation.id);
    conversations.value = conversations.value.filter((item) => item.id !== conversation.id);
    total.value -= 1;
    if (activeConversation.value?.id === conversation.id) clearAIConversation();
    uni.showToast({ title: "已删除", icon: "none" });
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    uni.showToast({
      title: error instanceof ApiRequestError ? error.message : "删除失败",
      icon: "none",
    });
  }
}

onShow(() => {
  void loadConversations();
});

onReachBottom(() => {
  void loadMoreConversations();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.conversation-list {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.conversation-row {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 $pf-space-3;
  border-bottom: 1rpx solid $pf-color-divider;
}

.conversation-row:last-child {
  border-bottom: 0;
}

.conversation-row__copy {
  min-width: 0;
  flex: 1;
}

.conversation-row__title,
.conversation-row__meta {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conversation-row__title {
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.conversation-row__meta {
  margin-top: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.conversation-row__delete {
  display: flex;
  width: 80rpx;
  height: 80rpx;
  align-items: center;
  justify-content: center;
}

.conversation-row__delete-icon {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  align-items: center;
  justify-content: center;
  border-radius: $pf-radius-control;
  background: $pf-color-danger-soft;
}

.conversation-row__delete--pressed {
  opacity: 0.55;
}

.conversation-row .pf-row-chevron {
  width: 32rpx;
  height: 32rpx;
  opacity: 0.5;
}

.conversation-content :deep(.uv-load-more) {
  margin-top: $pf-space-2;
}

.conversations-state {
  display: flex;
  min-height: 260rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  padding: $pf-space-4;
  font-size: $pf-font-size-body;
}

.conversations-empty {
  display: flex;
  min-height: 360rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $pf-space-6 $pf-space-4;
}

.conversations-empty__icon {
  display: flex;
  width: 72rpx;
  height: 72rpx;
  align-items: center;
  justify-content: center;
  border-radius: 22rpx;
  background: $pf-color-primary-soft;
}

.conversations-empty__icon-image {
  width: 40rpx;
  height: 40rpx;
}

.conversations-empty__title {
  margin-top: $pf-space-3;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-medium;
}
</style>
