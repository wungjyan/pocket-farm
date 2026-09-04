<template>
  <view class="pf-page mine-page">
    <PfPageHeader title="我的" variant="tab" />

    <view class="pf-page-content">
      <view class="profile-card pf-tappable" @tap="openSettings">
        <view class="profile-card__avatar"><text>{{ avatarText }}</text></view>
        <view class="profile-card__copy">
          <text class="profile-card__name">{{ displayName }}</text>
          <text class="profile-card__phone">{{ maskedPhone }}</text>
        </view>
        <PfRowChevron />
      </view>

      <view class="pf-section-heading mine-section-heading">
        <text class="pf-section-title">农场服务</text>
      </view>
      <view class="menu-group">
        <view class="menu-row pf-tappable" @tap="openFarms">
          <PfBusinessIcon name="land-plot" />
          <text class="menu-row__title">我的农场</text>
          <text class="menu-row__value menu-row__value--farm">{{ currentFarmName }}</text>
          <PfRowChevron />
        </view>
        <view class="menu-list-divider" />
        <view class="menu-row pf-tappable" @tap="openFarmSettings">
          <PfBusinessIcon name="settings" />
          <text class="menu-row__title">当前农场管理</text>
          <text class="menu-row__value menu-row__value--role">{{ roleLabel }}</text>
          <PfRowChevron />
        </view>
      </view>

      <view class="pf-section-heading mine-section-heading">
        <text class="pf-section-title">智能助手</text>
      </view>
      <view class="menu-group">
        <view class="menu-row pf-tappable" @tap="openAIConversations">
          <PfBusinessIcon name="list" />
          <text class="menu-row__title">AI 对话</text>
          <PfRowChevron />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfPageHeader from "../../components/PfPageHeader.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { useFarmContext } from "../../services/farm-context";
import { useUserContext } from "../../services/user-context";

const { currentUser } = useUserContext();
const { currentFarm } = useFarmContext();
const displayName = computed(
  () => currentUser.value?.nickname || maskPhone(currentUser.value?.phoneNumber || "用户"),
);
const maskedPhone = computed(() => maskPhone(currentUser.value?.phoneNumber || ""));
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

function openAIConversations(): void {
  uni.navigateTo({ url: "/pages/ai/conversations" });
}

// 本页只读展示：用户与农场信息均由共享上下文维护，无需在展示时请求。
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.mine-page {
  background: $pf-color-page;
}

.mine-page .pf-section-title {
  color: $pf-color-text;
  font-size: 30rpx;
  font-weight: 720;
}

.mine-section-heading {
  margin-top: 40rpx;
}

.profile-card {
  display: flex;
  min-height: 136rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 24rpx;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
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

.profile-card .pf-row-chevron,
.menu-row .pf-row-chevron {
  width: 28rpx;
  height: 28rpx;
  opacity: 0.42;
}

.menu-group {
  overflow: hidden;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
}

.menu-row {
  display: flex;
  min-height: 104rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 22rpx;
}

.menu-list-divider {
  height: 1rpx;
  margin-left: 94rpx;
  background: $pf-color-divider;
}

.menu-row :deep(.pf-business-icon) {
  width: 56rpx;
  height: 56rpx;
  border-radius: 16rpx;
  background: $pf-color-primary-soft;
}

.menu-row :deep(.pf-business-icon__image) {
  width: 32rpx;
  height: 32rpx;
}

.menu-row__title {
  min-width: 0;
  flex: 1;
  margin-left: 16rpx;
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 650;
}

.menu-row__value {
  display: block;
  overflow: hidden;
  max-width: 220rpx;
  margin-right: 14rpx;
  padding: 5rpx 12rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-row__value--farm {
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
}

.menu-row__value--role {
  background: $pf-color-surface-muted;
  color: $pf-color-text-secondary;
}
</style>
