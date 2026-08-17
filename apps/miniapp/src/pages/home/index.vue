<template>
  <view class="page home-page">
    <view class="custom-header" :style="headerStyle">
      <view class="custom-header__inner" :style="headerInnerStyle">
        <view class="header-context" @tap="showComingSoon">
          <uv-icon name="home" size="18" color="#2F7D4A" />
          <text>选择农场</text>
          <uv-icon name="arrow-down" size="14" color="#667068" />
        </view>
        <text class="header-title">首页</text>
      </view>
    </view>

    <view class="page-content">
      <view class="welcome-panel">
        <view class="welcome-copy">
          <text class="eyebrow">今日工作台</text>
          <text class="welcome-title">{{ displayName }}</text>
          <text class="welcome-description">把每一次种养和农事，留在自己的记录里。</text>
        </view>
        <view class="welcome-mark">
          <uv-icon name="home-fill" size="42" color="#2F7D4A" />
        </view>
      </view>

      <view class="section-heading">
        <text class="section-title">当前农场</text>
        <text class="section-action" @tap="showComingSoon">创建农场</text>
      </view>

      <view class="farm-card" @tap="showComingSoon">
        <view class="farm-card__icon">
          <uv-icon name="map" size="26" color="#2F7D4A" />
        </view>
        <view class="farm-card__copy">
          <text class="farm-card__title">还没有农场</text>
          <text class="farm-card__description">创建后，这里会展示地块和生产概览</text>
        </view>
        <uv-icon name="arrow-right" size="18" color="#929A93" />
      </view>

      <view class="section-heading quick-heading">
        <text class="section-title">快捷记录</text>
        <text class="section-note">准备好后随手记</text>
      </view>

      <view class="quick-grid">
        <view class="quick-action" @tap="showComingSoon">
          <view class="quick-action__icon quick-action__icon--green">
            <uv-icon name="plus" size="22" color="#2F7D4A" />
          </view>
          <text class="quick-action__title">开始种养</text>
          <text class="quick-action__description">从地块开始</text>
        </view>
        <view class="quick-action" @tap="showComingSoon">
          <view class="quick-action__icon quick-action__icon--blue">
            <uv-icon name="edit-pen" size="22" color="#4C91A0" />
          </view>
          <text class="quick-action__title">记农事</text>
          <text class="quick-action__description">记录今天的工作</text>
        </view>
        <view class="quick-action" @tap="showComingSoon">
          <view class="quick-action__icon quick-action__icon--gold">
            <uv-icon name="order" size="22" color="#C7862B" />
          </view>
          <text class="quick-action__title">收获</text>
          <text class="quick-action__description">留下产出记录</text>
        </view>
      </view>

      <view class="section-heading activity-heading">
        <text class="section-title">最近动态</text>
        <text class="section-note">暂无记录</text>
      </view>

      <view class="activity-card">
        <view class="activity-card__icon">
          <uv-icon name="clock" size="24" color="#929A93" />
        </view>
        <view class="activity-card__copy">
          <text class="activity-card__title">还没有生产动态</text>
          <text class="activity-card__description">创建农场并开始记录后，动态会显示在这里</text>
        </view>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { useCustomHeader } from "../../composables/useCustomHeader";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, type User } from "../../services/user";

const { headerStyle, headerInnerStyle } = useCustomHeader();
const user = ref<User | null>(null);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const displayName = computed(() => user.value?.nickname || maskPhone(user.value?.phoneNumber || "用户"));

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function showComingSoon(): void {
  toastRef.value?.show({ type: "default", message: "相关功能将在后续阶段开放" });
}

onShow(async () => {
  try {
    user.value = await getCurrentUser();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
    }
  }
});
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  box-sizing: border-box;
  background: #f7f8f3;
}

.custom-header {
  background: #f7f8f3;
}

.custom-header__inner {
  position: relative;
  display: flex;
  box-sizing: border-box;
  align-items: center;
  padding-left: 32rpx;
}

.header-title {
  position: absolute;
  top: 50%;
  left: 50%;
  color: #202821;
  font-size: 32rpx;
  font-weight: 600;
  line-height: 1;
  transform: translate(-50%, -50%);
}

.header-context {
  display: flex;
  align-items: center;
  color: #2f7d4a;
  font-size: 25rpx;
  white-space: nowrap;
}

.header-context > .uv-icon:first-child {
  margin-right: 8rpx;
}

.header-context > .uv-icon:last-child {
  margin-left: 8rpx;
}

.page-content {
  padding: 24rpx 32rpx 56rpx;
}

.welcome-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  border-radius: 24rpx;
  background: #eaf4ec;
}

.welcome-copy {
  min-width: 0;
}

.eyebrow,
.welcome-title,
.welcome-description {
  display: block;
}

.eyebrow {
  color: #2f7d4a;
  font-size: 24rpx;
  font-weight: 600;
}

.welcome-title {
  margin-top: 12rpx;
  color: #202821;
  font-size: 38rpx;
  font-weight: 700;
}

.welcome-description {
  max-width: 510rpx;
  margin-top: 12rpx;
  color: #667068;
  font-size: 24rpx;
  line-height: 1.5;
}

.welcome-mark {
  display: flex;
  width: 76rpx;
  height: 76rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-left: 20rpx;
  border-radius: 22rpx;
  background: #ffffff;
}

.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 40rpx 4rpx 16rpx;
}

.section-title {
  color: #202821;
  font-size: 30rpx;
  font-weight: 600;
}

.section-action {
  color: #2f7d4a;
  font-size: 25rpx;
}

.section-note {
  color: #929a93;
  font-size: 23rpx;
}

.farm-card,
.activity-card {
  display: flex;
  align-items: center;
  padding: 26rpx 24rpx;
  border: 1rpx solid #e2e6e0;
  border-radius: 20rpx;
  background: #ffffff;
}

.farm-card__icon,
.activity-card__icon {
  display: flex;
  width: 68rpx;
  height: 68rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  background: #eaf4ec;
}

.farm-card__copy,
.activity-card__copy {
  min-width: 0;
  flex: 1;
  margin: 0 20rpx;
}

.farm-card__title,
.farm-card__description,
.activity-card__title,
.activity-card__description {
  display: block;
}

.farm-card__title,
.activity-card__title {
  color: #202821;
  font-size: 28rpx;
  font-weight: 600;
}

.farm-card__description,
.activity-card__description {
  margin-top: 8rpx;
  color: #929a93;
  font-size: 23rpx;
  line-height: 1.45;
}

.quick-heading {
  margin-top: 44rpx;
}

.quick-grid {
  display: flex;
}

.quick-action + .quick-action {
  margin-left: 16rpx;
}

.quick-action {
  min-width: 0;
  flex: 1;
  padding: 22rpx 16rpx 20rpx;
  border: 1rpx solid #e2e6e0;
  border-radius: 20rpx;
  background: #ffffff;
}

.quick-action__icon {
  display: flex;
  width: 52rpx;
  height: 52rpx;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
}

.quick-action__icon--green {
  background: #eaf4ec;
}

.quick-action__icon--blue {
  background: #eaf4f5;
}

.quick-action__icon--gold {
  background: #fbf3e4;
}

.quick-action__title,
.quick-action__description {
  display: block;
}

.quick-action__title {
  margin-top: 18rpx;
  color: #202821;
  font-size: 26rpx;
  font-weight: 600;
}

.quick-action__description {
  margin-top: 8rpx;
  color: #929a93;
  font-size: 21rpx;
  line-height: 1.35;
}

.activity-heading {
  margin-top: 44rpx;
}

.activity-card__icon {
  background: #f3f5f1;
}
</style>
