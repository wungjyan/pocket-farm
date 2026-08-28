<template>
  <view class="pf-empty-state">
    <PfBusinessIcon :name="icon" size="empty" />
    <text class="pf-empty-state__text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
import PfBusinessIcon from "./PfBusinessIcon.vue";
import type { BusinessIconName } from "./PfBusinessIcon.vue";

withDefaults(
  defineProps<{
    text?: string;
    icon?: BusinessIconName;
  }>(),
  {
    text: "暂无数据",
    icon: "clock-3",
  },
);
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.pf-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 200rpx 28rpx 36rpx;
  text-align: center;
}

.pf-empty-state__text {
  margin-top: 20rpx;
  color: $pf-color-text-muted;
  font-size: 26rpx;
  font-weight: 500;
}
</style>
