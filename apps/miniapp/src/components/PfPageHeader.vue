<template>
  <view class="pf-page-header" :style="headerStyle">
    <view class="pf-page-header__inner" :style="headerInnerStyle">
      <view v-if="showBack" class="pf-page-header__back" @tap="handleBack">
        <uv-icon name="arrow-left" size="21" color="#202821" />
      </view>
      <text v-if="showTitle" class="pf-page-header__title">{{ title }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useCustomHeader } from "../composables/useCustomHeader";

withDefaults(
  defineProps<{
    title: string;
    showBack?: boolean;
    showTitle?: boolean;
  }>(),
  { showBack: false, showTitle: true },
);

const { headerStyle, headerInnerStyle } = useCustomHeader();

function handleBack(): void {
  uni.navigateBack();
}
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.pf-page-header {
  background: $pf-color-page;
}

.pf-page-header__inner {
  position: relative;
  display: flex;
  box-sizing: border-box;
  align-items: center;
  padding-left: $pf-space-page-x;
}

.pf-page-header__title {
  position: absolute;
  top: 50%;
  left: 50%;
  width: calc(100% - 240rpx);
  overflow: hidden;
  color: $pf-color-text;
  font-size: 32rpx;
  font-weight: 600;
  line-height: 1;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
  transform: translate(-50%, -50%);
}

.pf-page-header__back {
  display: flex;
  width: 64rpx;
  height: 64rpx;
  align-items: center;
  justify-content: flex-start;
}
</style>
