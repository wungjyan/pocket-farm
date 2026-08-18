<template>
  <view class="pf-page home-page">
    <PfPageHeader :title="currentFarmName" />

    <view class="pf-page-content">
      <view class="welcome-panel">
        <text class="eyebrow">今日工作台</text>
        <text class="welcome-title">{{ greeting }}，{{ displayName }}</text>
        <text class="welcome-description">记录今天的种养和农事，让生产过程清清楚楚。</text>
      </view>

      <template v-if="hasFarm">
        <view class="pf-section-heading">
          <text class="pf-section-title">当前种养</text>
          <text class="pf-section-action" @tap="showComingSoon">查看全部</text>
        </view>
        <view class="pf-card content-placeholder">
          <uv-icon name="list" size="22" color="#2F7D4A" />
          <text>当前种养数据将在接入农场接口后显示</text>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">快捷记录</text>
          <text class="pf-section-note">随手记下今天的工作</text>
        </view>
        <view class="quick-actions">
          <view class="quick-action" @tap="showComingSoon">
            <uv-icon name="plus" size="20" color="#2F7D4A" />
            <text>开始种养</text>
          </view>
          <view class="quick-action" @tap="showComingSoon">
            <uv-icon name="edit-pen" size="20" color="#2F7D4A" />
            <text>记农事</text>
          </view>
          <view class="quick-action" @tap="showComingSoon">
            <uv-icon name="order" size="20" color="#2F7D4A" />
            <text>收获</text>
          </view>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">最近动态</text>
          <text class="pf-section-note">暂无记录</text>
        </view>
        <view class="pf-card content-placeholder">
          <uv-icon name="clock" size="22" color="#929A93" />
          <text>完成第一条记录后，动态会显示在这里</text>
        </view>
      </template>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon">
          <uv-icon name="map" size="28" color="#2F7D4A" />
        </view>
        <text class="empty-state__title">还没有农场</text>
        <text class="empty-state__description">创建一个农场，开始记录你的生产现场。</text>
        <uv-button
          type="primary"
          shape="square"
          custom-style="width: 100%; height: 84rpx; margin-top: 28rpx; border-radius: 16rpx;"
          @click="openCreateFarm"
        >
          创建农场
        </uv-button>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, type User } from "../../services/user";
import { useFarmContext } from "../../services/farm-context";

const user = ref<User | null>(null);
const { currentFarmName, hasCurrentFarm, refreshFromApi } = useFarmContext();
const hasFarm = hasCurrentFarm;
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const displayName = computed(() => user.value?.nickname || maskPhone(user.value?.phoneNumber || "用户"));
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 11) return "早上好";
  if (hour < 13) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
});

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function showComingSoon(): void {
  toastRef.value?.show({ type: "default", message: "相关功能将在后续阶段开放" });
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

onShow(async () => {
  try {
    const [currentUser] = await Promise.all([getCurrentUser(), refreshFromApi()]);
    user.value = currentUser;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
    }
  }
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.welcome-panel {
  padding: 28rpx 4rpx 4rpx;
}

.eyebrow,
.welcome-title,
.welcome-description {
  display: block;
}

.eyebrow {
  color: $pf-color-primary;
  font-size: 24rpx;
  font-weight: 600;
}

.welcome-title {
  margin-top: 10rpx;
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
}

.welcome-description {
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  line-height: 1.5;
}

.empty-state {
  margin-top: 32rpx;
  padding: 32rpx 28rpx 28rpx;
  text-align: center;
}

.empty-state__icon {
  display: flex;
  width: 68rpx;
  height: 68rpx;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  border-radius: 18rpx;
  background: $pf-color-primary-soft;
}

.empty-state__title,
.empty-state__description {
  display: block;
}

.empty-state__title {
  margin-top: 22rpx;
  color: $pf-color-text;
  font-size: 30rpx;
  font-weight: 600;
}

.empty-state__description {
  margin-top: 8rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  line-height: 1.5;
}

.content-placeholder {
  display: flex;
  min-height: 104rpx;
  align-items: center;
  padding: 0 24rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
}

.content-placeholder text {
  margin-left: 14rpx;
}

.quick-actions {
  display: flex;
}

.quick-action {
  display: flex;
  min-height: 84rpx;
  flex: 1;
  align-items: center;
  padding: 0 16rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-list;
  background: $pf-color-surface;
  color: $pf-color-text;
  font-size: 24rpx;
}

.quick-action + .quick-action {
  margin-left: 12rpx;
}

.quick-action text {
  margin-left: 8rpx;
}
</style>
