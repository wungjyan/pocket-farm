<template>
  <view class="pf-page mine-page">
    <PfPageHeader title="我的" variant="tab" />

    <view class="pf-page-content">
      <view class="profile-bar">
        <view class="profile-avatar"><text>{{ avatarText }}</text></view>
        <view class="profile-copy">
          <text class="profile-name">{{ displayName }}</text>
          <text class="profile-phone">{{ maskedPhone }}</text>
        </view>
        <view class="profile-settings pf-tappable" @tap="openSettings">
          <uv-icon name="setting" size="26" color="#FFFFFF" />
        </view>
      </view>

      <view class="pf-section-heading">
        <text class="pf-section-title">农场</text>
      </view>
      <view class="menu-list">
        <view class="menu-row pf-tappable" @tap="openFarms">
          <view class="menu-icon"><uv-icon name="grid" size="20" color="#286B46" /></view>
          <text class="menu-title">我的农场</text>
          <text class="menu-value">{{ currentFarmName }}</text>
          <uv-icon name="arrow-right" size="17" color="#7F8B82" />
        </view>
        <view class="menu-divider" />
        <view class="menu-row pf-tappable" @tap="openFarmSettings">
          <view class="menu-icon"><uv-icon name="setting" size="20" color="#286B46" /></view>
          <text class="menu-title">当前农场管理</text>
          <text class="menu-value">{{ roleLabel }}</text>
          <uv-icon name="arrow-right" size="17" color="#7F8B82" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, type User } from "../../services/user";

const user = ref<User | null>(null);
const { currentFarm, refreshFromApi } = useFarmContext();
const displayName = computed(() => user.value?.nickname || maskPhone(user.value?.phoneNumber || "用户"));
const maskedPhone = computed(() => maskPhone(user.value?.phoneNumber || ""));
const avatarText = computed(() => displayName.value.slice(0, 1));
const currentFarmName = computed(() => currentFarm.value?.name || "未选择");
const roleLabel = computed(() => {
  const labels = { OWNER: "农场主", ADMIN: "管理员", MEMBER: "成员" } as const;
  return currentFarm.value?.role ? labels[currentFarm.value.role] : "未选择";
});

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function openSettings(): void {
  uni.navigateTo({ url: "/pages/settings/index" });
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

.profile-bar {
  display: flex;
  min-height: 152rpx;
  box-sizing: border-box;
  align-items: center;
  margin-top: $pf-space-3;
  padding: 24rpx;
  border-radius: 20rpx;
  background: $pf-color-primary;
}

.profile-avatar {
  display: flex;
  width: 80rpx;
  height: 80rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 1rpx solid rgba(255, 255, 255, 0.34);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  color: $pf-white;
  font-size: 30rpx;
  font-weight: 700;
}

.profile-copy {
  min-width: 0;
  flex: 1;
  margin-left: 20rpx;
}

.profile-name,
.profile-phone,
.menu-title,
.menu-value {
  display: block;
}

.profile-name {
  overflow: hidden;
  color: $pf-white;
  font-size: 32rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-phone {
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.72);
  font-size: 22rpx;
}

.profile-settings {
  display: flex;
  width: 88rpx;
  height: 88rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: flex-end;
}

.menu-list {
  overflow: hidden;
  border: 1rpx solid $pf-color-border;
  border-radius: 14rpx;
  background: $pf-color-surface;
}

.menu-row {
  display: flex;
  min-height: 104rpx;
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
  border-radius: 12rpx;
  background: $pf-color-primary-soft;
}

.menu-title {
  min-width: 0;
  flex: 1;
  margin-left: 16rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.menu-value {
  overflow: hidden;
  max-width: 220rpx;
  margin-right: 12rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-divider {
  height: 1rpx;
  margin-left: 90rpx;
  background: $pf-color-divider;
}
</style>
