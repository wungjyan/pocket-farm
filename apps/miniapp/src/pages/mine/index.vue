<template>
  <view class="pf-page mine-page">
    <PfPageHeader title="我的" :show-title="false" />

    <view class="pf-page-content">
      <view class="profile-card" @tap="openProfile">
        <uv-avatar :text="avatarText" size="64" bg-color="#2F7D4A" color="#FFFFFF" />
        <view class="profile-copy">
          <text class="profile-eyebrow">个人账户</text>
          <text class="profile-name">{{ displayName }}</text>
          <text class="profile-phone">{{ maskedPhone }}</text>
        </view>
        <uv-icon name="arrow-right" size="18" color="#929A93" />
      </view>

      <view class="section-label">账户与农场</view>
      <view class="menu-card pf-card">
        <view class="menu-row" @tap="openFarms">
          <view class="menu-icon menu-icon--green">
            <uv-icon name="grid" size="20" color="#2F7D4A" />
          </view>
          <view class="menu-copy">
            <text class="menu-title">我的农场</text>
            <text class="menu-description">{{ currentFarmDescription }}</text>
          </view>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
        <view class="menu-divider" />
        <view class="menu-row" @tap="openFarmSettings">
          <view class="menu-icon menu-icon--green">
            <uv-icon name="setting" size="20" color="#2F7D4A" />
          </view>
          <view class="menu-copy">
            <text class="menu-title">当前农场管理</text>
            <text class="menu-description">农场信息、成员管理与退出农场</text>
          </view>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
        <view class="menu-divider" />
        <view class="menu-row" @tap="showComingSoon">
          <view class="menu-icon menu-icon--neutral">
            <uv-icon name="info-circle" size="20" color="#667068" />
          </view>
          <text class="menu-title">关于掌上农场</text>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
      </view>

      <view class="logout-row" @tap="handleLogout">
        <text>退出登录</text>
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
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm, hasCurrentFarm, refreshFromApi } = useFarmContext();
const displayName = computed(() => user.value?.nickname || maskPhone(user.value?.phoneNumber || "用户"));
const maskedPhone = computed(() => maskPhone(user.value?.phoneNumber || ""));
const avatarText = computed(() => displayName.value.slice(0, 1));
const currentFarmDescription = computed(() =>
  hasCurrentFarm.value ? `当前：${currentFarm.value?.name}` : "请选择当前农场",
);

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function openProfile(): void {
  uni.navigateTo({ url: "/pages/profile/edit" });
}

function openFarms(): void {
  uni.navigateTo({ url: "/pages/farms/index" });
}

function openFarmSettings(): void {
  if (!currentFarm.value) {
    openFarms();
    return;
  }
  uni.navigateTo({ url: `/pages/farms/detail?farmId=${currentFarm.value.id}` });
}

function showComingSoon(): void {
  toastRef.value?.show({ type: "default", message: "相关功能将在后续阶段开放" });
}

function handleLogout(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
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

.profile-card {
  display: flex;
  align-items: center;
  padding: 26rpx 24rpx;
  border-radius: $pf-radius-card;
  background: $pf-color-primary-soft;
}

.profile-copy {
  min-width: 0;
  flex: 1;
  margin: 0 18rpx;
}

.profile-eyebrow,
.profile-name,
.profile-phone {
  display: block;
}

.profile-eyebrow {
  color: $pf-color-primary;
  font-size: 22rpx;
  font-weight: 600;
}

.profile-name {
  margin-top: 6rpx;
  color: $pf-color-text;
  font-size: 34rpx;
  font-weight: 700;
}

.profile-phone {
  margin-top: 5rpx;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}

.section-label {
  margin: 38rpx 8rpx 14rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 600;
}

.menu-card {
  overflow: hidden;
}

.menu-row {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  padding: 0 22rpx;
}

.menu-icon {
  display: flex;
  width: 52rpx;
  height: 52rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
}

.menu-icon--green {
  background: $pf-color-primary-soft;
}

.menu-icon--neutral {
  background: $pf-color-surface-muted;
}

.menu-copy {
  min-width: 0;
  flex: 1;
  margin: 0 18rpx;
}

.menu-title,
.menu-description {
  display: block;
}

.menu-title {
  flex: 1;
  margin-left: 18rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 500;
}

.menu-copy .menu-title {
  margin-left: 0;
}

.menu-description {
  margin-top: 6rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.menu-divider {
  height: 1rpx;
  margin-left: 92rpx;
  background: $pf-color-divider;
}

.logout-row {
  padding: 40rpx 0 16rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  text-align: center;
}
</style>
