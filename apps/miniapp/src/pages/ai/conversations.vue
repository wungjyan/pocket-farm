<template>
  <view class="pf-page conversations-page">
    <view class="pf-page-content">
      <view v-if="loading" class="conversations-state">
        <uv-loading-icon mode="circle" color="#286B46" />
      </view>

      <view v-else-if="loadError" class="conversations-state">
        <text>{{ loadError }}</text>
        <view class="conversations-state__action pf-tappable" @tap="loadConversations">
          <text>重试</text>
        </view>
      </view>

      <view v-else-if="conversations.length" class="conversation-list">
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
            <uv-icon name="trash" size="20" color="#A9433B" />
          </view>
          <PfRowChevron />
        </view>
        <uv-load-more
          v-if="hasMore() || loadingMore"
          :status="loadingMore ? 'loading' : 'nomore'"
          icon-color="#286B46"
          color="#7F8B82"
        />
      </view>

      <view v-else class="conversations-state">
        <view class="conversations-state__action pf-tappable" @tap="startNewConversation">
          <text>新对话</text>
        </view>
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
const { selectAIConversation, clearAIConversation } = useAIConversationContext();
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
}
.conversation-row {
  display: flex;
  min-height: 124rpx;
  align-items: center;
  border-bottom: 1rpx solid $pf-color-divider;
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
  font-size: 28rpx;
  font-weight: 600;
}
.conversation-row__meta {
  margin-top: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: 23rpx;
}
.conversation-row__delete {
  display: flex;
  width: 72rpx;
  height: 72rpx;
  align-items: center;
  justify-content: center;
}
.conversation-row__delete--pressed {
  opacity: 0.55;
}
.conversation-row .pf-row-chevron {
  width: 32rpx;
  height: 32rpx;
  opacity: 0.5;
}
.conversations-state {
  display: flex;
  min-height: 260rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: 27rpx;
}
.conversations-state__action {
  display: flex;
  min-height: 72rpx;
  align-items: center;
  margin-top: $pf-space-3;
  color: $pf-color-primary;
  font-size: 27rpx;
  font-weight: 600;
}
</style>
