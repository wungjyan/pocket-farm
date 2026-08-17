<template>
  <view class="page mine-page">
    <view class="custom-header" :style="headerStyle">
      <view class="custom-header__inner" :style="headerInnerStyle">
        <text class="header-title">我的</text>
      </view>
    </view>

    <view class="page-content">
      <view class="profile-card" @tap="openProfile">
        <uv-avatar :text="avatarText" size="76" bg-color="#2F7D4A" color="#FFFFFF" />
        <view class="profile-copy">
          <text class="profile-eyebrow">个人账户</text>
          <text class="profile-name">{{ displayName }}</text>
          <text class="profile-phone">{{ maskedPhone }}</text>
        </view>
        <uv-icon name="arrow-right" size="18" color="#929A93" />
      </view>

      <view class="section-label">账号</view>
      <view class="menu-card">
        <view class="menu-row" @tap="openProfile">
          <view class="menu-icon menu-icon--green">
            <uv-icon name="account" size="20" color="#2F7D4A" />
          </view>
          <text class="menu-title">个人资料</text>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
      </view>

      <view class="section-label">我的空间</view>
      <view class="menu-card">
        <view class="menu-row" @tap="showComingSoon">
          <view class="menu-icon menu-icon--blue">
            <uv-icon name="grid" size="20" color="#4C91A0" />
          </view>
          <view class="menu-copy">
            <text class="menu-title">我的农场</text>
            <text class="menu-description">管理拥有和加入的农场</text>
          </view>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
      </view>

      <view class="section-label">更多</view>
      <view class="menu-card">
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
import { useCustomHeader } from "../../composables/useCustomHeader";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, type User } from "../../services/user";

const { headerStyle, headerInnerStyle } = useCustomHeader();
const user = ref<User | null>(null);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const displayName = computed(() => user.value?.nickname || maskPhone(user.value?.phoneNumber || "用户"));
const maskedPhone = computed(() => maskPhone(user.value?.phoneNumber || ""));
const avatarText = computed(() => displayName.value.slice(0, 1));

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function openProfile(): void {
  uni.navigateTo({ url: "/pages/profile/edit" });
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

.page-content {
  padding: 24rpx 32rpx 64rpx;
}

.profile-card {
  display: flex;
  align-items: center;
  padding: 28rpx 24rpx;
  border-radius: 24rpx;
  background: #eaf4ec;
}

.profile-copy {
  min-width: 0;
  flex: 1;
  margin: 0 20rpx;
}

.profile-eyebrow,
.profile-name,
.profile-phone {
  display: block;
}

.profile-eyebrow {
  color: #2f7d4a;
  font-size: 23rpx;
  font-weight: 600;
}

.profile-name {
  margin-top: 7rpx;
  color: #202821;
  font-size: 34rpx;
  font-weight: 700;
}

.profile-phone {
  margin-top: 6rpx;
  color: #667068;
  font-size: 23rpx;
}

.section-label {
  margin: 38rpx 8rpx 14rpx;
  color: #929a93;
  font-size: 23rpx;
  font-weight: 600;
}

.menu-card {
  overflow: hidden;
  border: 1rpx solid #e2e6e0;
  border-radius: 20rpx;
  background: #ffffff;
}

.menu-row {
  display: flex;
  min-height: 100rpx;
  align-items: center;
  padding: 0 22rpx;
}

.menu-icon {
  display: flex;
  width: 54rpx;
  height: 54rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
}

.menu-icon--green {
  background: #eaf4ec;
}

.menu-icon--blue {
  background: #eaf4f5;
}

.menu-icon--neutral {
  background: #f3f5f1;
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
  color: #202821;
  font-size: 27rpx;
  font-weight: 500;
}

.menu-description {
  margin-top: 6rpx;
  color: #929a93;
  font-size: 22rpx;
}

.logout-row {
  padding: 40rpx 0 16rpx;
  color: #929a93;
  font-size: 23rpx;
  text-align: center;
}
</style>
