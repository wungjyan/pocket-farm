<template>
  <view class="pf-page farm-page">
    <PfPageHeader :title="currentFarmName" />

    <view class="pf-page-content">
      <template v-if="hasFarm">
        <view class="farm-summary">
          <view class="farm-summary__item">
            <text class="farm-summary__value">{{ plotCount }}</text>
            <text class="farm-summary__label">个地块</text>
          </view>
          <view class="farm-summary__divider" />
          <view class="farm-summary__item">
            <text class="farm-summary__value">{{ activeProductionCount }}</text>
            <text class="farm-summary__label">进行中种养</text>
          </view>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">地块</text>
          <text class="pf-section-action" @tap="showComingSoon">创建地块</text>
        </view>
        <view class="pf-card plot-placeholder">
          <uv-icon name="grid" size="22" color="#2F7D4A" />
          <text>地块列表将在接入农场接口后显示</text>
        </view>
      </template>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon">
          <uv-icon name="map" size="28" color="#2F7D4A" />
        </view>
        <text class="empty-state__title">先创建一个农场</text>
        <text class="empty-state__description">农场建立后，这里会成为你的生产现场。</text>
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
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { useFarmContext } from "../../services/farm-context";

const { currentFarmName, hasCurrentFarm, refreshFromApi } = useFarmContext();
const hasFarm = hasCurrentFarm;
const plotCount = ref(0);
const activeProductionCount = ref(0);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);

function showComingSoon(): void {
  toastRef.value?.show({ type: "default", message: "相关功能将在后续阶段开放" });
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

onShow(async () => {
  try {
    await refreshFromApi();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
    }
    // The farm page keeps its local context while a transient refresh fails.
  }
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.farm-summary {
  display: flex;
  align-items: center;
  margin-top: 28rpx;
  padding: 20rpx 4rpx;
  border-bottom: 1rpx solid $pf-color-divider;
}

.farm-summary__item {
  display: flex;
  align-items: baseline;
  flex: 1;
}

.farm-summary__value {
  color: $pf-color-text;
  font-size: 34rpx;
  font-weight: 700;
}

.farm-summary__label {
  margin-left: 8rpx;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}

.farm-summary__divider {
  width: 1rpx;
  height: 34rpx;
  margin: 0 24rpx;
  background: $pf-color-divider;
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

.plot-placeholder {
  display: flex;
  min-height: 104rpx;
  align-items: center;
  padding: 0 24rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
}

.plot-placeholder text {
  margin-left: 14rpx;
}
</style>
