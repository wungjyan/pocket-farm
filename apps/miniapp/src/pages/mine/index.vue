<template>
  <view class="pf-page mine-page">
    <PfPageHeader title="我的" variant="tab" />

    <view class="pf-page-content">
      <view class="profile-card pf-card pf-tappable" @tap="openSettings">
        <view class="profile-card__avatar"
          ><text>{{ avatarText }}</text></view
        >
        <view class="profile-card__copy">
          <text class="profile-card__name">{{ displayName }}</text>
          <text class="profile-card__phone">{{ maskedPhone }}</text>
        </view>
        <PfRowChevron />
      </view>

      <view class="pf-section-heading">
        <text class="pf-section-title">农场</text>
      </view>
      <view class="menu-list">
        <view class="menu-row pf-card pf-tappable" @tap="openFarms">
          <PfBusinessIcon name="land-plot" />
          <text class="menu-row__title">我的农场</text>
          <text class="menu-row__value">{{ currentFarmName }}</text>
          <PfRowChevron />
        </view>
        <view class="menu-row pf-card pf-tappable" @tap="openFarmSettings">
          <PfBusinessIcon name="settings" />
          <text class="menu-row__title">当前农场管理</text>
          <text class="menu-row__value">{{ roleLabel }}</text>
          <PfRowChevron />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfPageHeader from "../../components/PfPageHeader.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, type User } from "../../services/user";

const user = ref<User | null>(null);
const { currentFarm, refreshFromApi } = useFarmContext();
const displayName = computed(
  () => user.value?.nickname || maskPhone(user.value?.phoneNumber || "用户"),
);
const maskedPhone = computed(() => maskPhone(user.value?.phoneNumber || ""));
const avatarText = computed(() => displayName.value.slice(0, 1));
const currentFarmName = computed(() => currentFarm.value?.name || "未选择");
const roleLabel = computed(() => {
  const labels = { OWNER: "农场主", ADMIN: "管理员", MEMBER: "成员" } as const;
  return currentFarm.value?.role ? labels[currentFarm.value.role] : "未选择";
});

function maskPhone(phone: string): string {
  return phone.length === 11
    ? `${phone.slice(0, 3)}****${phone.slice(-4)}`
    : phone;
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
    const [currentUser] = await Promise.all([
      getCurrentUser(),
      refreshFromApi(),
    ]);
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
  min-height: 132rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 24rpx;
}

.profile-card__avatar {
  display: flex;
  width: 80rpx;
  height: 80rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 30rpx;
  font-weight: 700;
}

.profile-card__copy {
  min-width: 0;
  flex: 1;
  margin: 0 18rpx;
}

.profile-card__name,
.profile-card__phone {
  display: block;
}

.profile-card__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 32rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-card__phone {
  margin-top: 8rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.menu-row {
  display: flex;
  min-height: 112rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 24rpx;
}

.menu-row__title {
  min-width: 0;
  flex: 1;
  margin-left: 16rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 650;
}

.menu-row__value {
  overflow: hidden;
  max-width: 220rpx;
  margin-right: 12rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
