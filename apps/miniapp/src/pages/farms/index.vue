<template>
  <view class="pf-page farms-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#2F7D4A" />
        <text>正在加载农场</text>
      </view>

      <view v-else-if="loadError" class="state-card pf-card">
        <uv-icon name="warning" size="28" color="#C96A45" />
        <text>{{ loadError }}</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 22rpx; border-radius: 12rpx;"
          @click="loadFarms"
        >
          重试
        </uv-button>
      </view>

      <view v-else-if="farms.length" class="farm-list">
        <view
          v-for="farm in farms"
          :key="farm.id"
          class="farm-row pf-card"
          @tap="openSettings(farm)"
        >
          <view class="farm-row__main">
            <view class="farm-row__copy">
              <view class="farm-row__name-line">
                <text class="farm-row__name">{{ farm.name }}</text>
                <text v-if="currentFarm?.id === farm.id" class="current-badge">当前</text>
              </view>
              <text class="farm-row__meta">{{ roleLabel(farm.myRole) }}</text>
            </view>
            <uv-icon name="arrow-right" size="17" color="#929A93" />
          </view>

          <view class="farm-row__actions">
            <view
              v-if="currentFarm?.id !== farm.id"
              class="set-current-button"
              @tap.stop="setCurrentFarm(farm)"
            >
              <text>切换</text>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon">
          <uv-icon name="grid" size="28" color="#2F7D4A" />
        </view>
        <text class="empty-state__title">还没有可用农场</text>
      </view>

      <view
        v-if="!loading && !loadError"
        class="create-action"
        @click="openCreateFarm"
      >
        <text>＋ 创建农场</text>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { getMyFarms, type Farm } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import { toFarmSummary, useFarmContext } from "../../services/farm-context";

const farms = ref<Farm[]>([]);
const loading = ref(false);
const loadError = ref("");
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm, selectFarm, syncAvailableFarms } = useFarmContext();

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadFarms(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    const page = await getMyFarms();
    farms.value = page.items;
    syncAvailableFarms(page.items.map(toFarmSummary));
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "农场加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function setCurrentFarm(farm: Farm): void {
  selectFarm(toFarmSummary(farm));
  toastRef.value?.show({ type: "success", message: `已切换到${farm.name}` });
}

function openSettings(farm: Farm): void {
  uni.navigateTo({ url: `/pages/farms/detail?farmId=${farm.id}` });
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

function roleLabel(role?: Farm["myRole"]): string {
  if (role === "OWNER") return "农场主";
  if (role === "ADMIN") return "管理员";
  return "成员";
}

onShow(loadFarms);
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.farm-list {
  margin-top: 8rpx;
}

.farm-row {
  padding: 22rpx 24rpx 18rpx;
}

.farm-row + .farm-row {
  margin-top: 12rpx;
}

.farm-row__main,
.farm-row__name-line,
.farm-row__actions,
.set-current-button {
  display: flex;
  align-items: center;
}

.farm-row__main {
  justify-content: space-between;
}

.farm-row__copy {
  min-width: 0;
}

.farm-row__name-line {
  min-width: 0;
}

.farm-row__name {
  max-width: 390rpx;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 29rpx;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.current-badge {
  margin-left: 10rpx;
  padding: 4rpx 10rpx;
  border-radius: 8rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 20rpx;
}

.farm-row__meta {
  display: block;
  margin-top: 8rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
}

.farm-row__actions {
  justify-content: flex-end;
  margin-top: 8rpx;
}

.set-current-button {
  padding: 6rpx 16rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: 999rpx;
  color: $pf-color-primary;
  font-size: 22rpx;
}

.create-action {
  display: flex;
  min-height: 72rpx;
  align-items: center;
  justify-content: center;
  margin-top: 20rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  color: $pf-color-primary;
  font-size: 24rpx;
}

.empty-state {
  margin-top: 28rpx;
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

.empty-state__title {
  display: block;
}

.empty-state__title {
  margin-top: 22rpx;
  color: $pf-color-text;
  font-size: 30rpx;
  font-weight: 600;
}

.state-card {
  display: flex;
  min-height: 180rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 28rpx;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
