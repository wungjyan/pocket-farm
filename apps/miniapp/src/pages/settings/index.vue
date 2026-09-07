<template>
  <view class="pf-page settings-page">
    <view class="pf-page-content">
      <text class="group-title">账号</text>
      <view class="settings-list">
        <view class="setting-row pf-tappable" @tap="openProfile">
          <text class="setting-label">昵称</text>
          <text class="setting-value">{{ nickname }}</text>
          <PfRowChevron />
        </view>
        <view class="setting-divider" />
        <view class="setting-row setting-row--readonly">
          <text class="setting-label">手机号</text>
          <text class="setting-value setting-value--readonly">{{ maskedPhone }}</text>
        </view>
      </view>

      <text class="group-title group-title--spaced">其他</text>
      <view class="settings-list">
        <view class="setting-row pf-tappable" @tap="showAbout">
          <text class="setting-label">关于掌农记</text>
          <PfRowChevron />
        </view>
      </view>

      <view class="logout-action pf-tappable" @tap="handleLogout">
        <text>退出登录</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, type User } from "../../services/user";

const user = ref<User | null>(null);
const { endFarmSession } = useFarmContext();
const nickname = computed(() => user.value?.nickname?.trim() || "未设置");
const maskedPhone = computed(() => maskPhone(user.value?.phoneNumber || ""));

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadUser(): Promise<void> {
  try {
    user.value = await getCurrentUser();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    }
  }
}

function openProfile(): void {
  uni.navigateTo({ url: "/pages/profile/edit" });
}

function showAbout(): void {
  uni.navigateTo({ url: "/pages/about/index" });
}

function handleLogout(): void {
  uni.showModal({
    title: "退出登录",
    content: "确定退出当前账号？",
    confirmText: "退出",
    confirmColor: "#A9433B",
    success: ({ confirm }) => {
      if (!confirm) return;
      endFarmSession();
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
    },
  });
}

onShow(loadUser);
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.settings-page .pf-page-content {
  padding-top: $pf-space-4;
}

.group-title {
  display: block;
  margin: 0 4rpx $pf-space-2;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.group-title--spaced {
  margin-top: $pf-space-5;
}

.settings-list {
  overflow: hidden;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.setting-row {
  display: flex;
  min-height: 108rpx;
  align-items: center;
  padding: 0 $pf-space-3;
}

.setting-label {
  min-width: 0;
  flex: 1;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-medium;
}

.setting-value {
  overflow: hidden;
  max-width: 360rpx;
  margin-right: 12rpx;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.setting-value--readonly {
  margin-right: 0;
  color: $pf-color-text-muted;
}

.setting-divider {
  height: 1rpx;
  margin-left: $pf-space-3;
  background: $pf-color-divider;
}

.logout-action {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  justify-content: center;
  margin-top: $pf-space-6;
  border: 1rpx solid $pf-color-danger-disabled;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  color: $pf-color-danger;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}
</style>
