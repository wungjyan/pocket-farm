<template>
  <view class="pf-page farms-page">
    <view class="pf-page-content">
      <view class="page-intro">
        <text class="page-intro__description">选择一个农场作为首页和生产现场的工作上下文。</text>
      </view>

      <view v-if="farms.length" class="farm-list">
        <view
          v-for="farm in farms"
          :key="farm.id"
          class="farm-row pf-card"
          @tap="handleSelectFarm(farm)"
        >
          <view class="farm-row__copy">
            <text class="farm-row__name">{{ farm.name }}</text>
            <text class="farm-row__meta">{{ roleLabel(farm.role) }}</text>
          </view>
          <uv-icon
            v-if="currentFarm?.id === farm.id"
            name="checkmark-circle-fill"
            size="22"
            color="#2F7D4A"
          />
          <uv-icon v-else name="arrow-right" size="18" color="#929A93" />
        </view>
      </view>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon">
          <uv-icon name="grid" size="28" color="#2F7D4A" />
        </view>
        <text class="empty-state__title">还没有可用农场</text>
        <text class="empty-state__description">创建农场后，可在这里切换当前工作农场。</text>
        <uv-button
          type="primary"
          shape="square"
          custom-style="width: 100%; height: 84rpx; margin-top: 28rpx; border-radius: 16rpx;"
          @click="showComingSoon"
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
import { useFarmContext, type FarmSummary } from "../../services/farm-context";

const farms = ref<FarmSummary[]>([]);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm, selectFarm } = useFarmContext();

function handleSelectFarm(farm: FarmSummary): void {
  selectFarm(farm);
  uni.navigateBack();
}

function roleLabel(role?: FarmSummary["role"]): string {
  if (role === "OWNER") return "农场主";
  if (role === "ADMIN") return "管理员";
  return "成员";
}

function showComingSoon(): void {
  toastRef.value?.show({ type: "default", message: "农场管理将在后续阶段开放" });
}

</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.page-intro__description {
  display: block;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  line-height: 1.5;
}

.farm-list {
  margin-top: 24rpx;
}

.farm-row {
  display: flex;
  min-height: 108rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 24rpx;
}

.farm-row + .farm-row {
  margin-top: 12rpx;
}

.farm-row__copy {
  min-width: 0;
}

.farm-row__name,
.farm-row__meta {
  display: block;
}

.farm-row__name {
  color: $pf-color-text;
  font-size: 29rpx;
  font-weight: 600;
}

.farm-row__meta {
  margin-top: 8rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
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
</style>
