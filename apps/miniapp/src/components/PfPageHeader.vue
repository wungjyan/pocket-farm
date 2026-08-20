<template>
  <view class="pf-page-header" :class="`pf-page-header--${variant}`">
    <view class="pf-page-header__spacer" :style="headerStyle">
      <view :style="headerInnerStyle" />
    </view>
    <view class="pf-page-header__fixed" :style="headerStyle">
      <view class="pf-page-header__inner" :style="headerInnerStyle">
        <view v-if="showBack" class="pf-page-header__back" hover-class="pf-page-header__back--pressed" @tap="handleBack">
          <uv-icon name="arrow-left" size="21" color="#17231B" />
        </view>
        <view v-if="showTitle" class="pf-page-header__copy">
          <text class="pf-page-header__title">{{ title }}</text>
          <text v-if="subtitle" class="pf-page-header__subtitle">{{ subtitle }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useCustomHeader } from "../composables/useCustomHeader";

const props = withDefaults(
  defineProps<{
    title: string;
    subtitle?: string;
    variant?: "center" | "tab";
    showBack?: boolean;
    showTitle?: boolean;
    backHandler?: () => void;
  }>(),
  { subtitle: "", variant: "center", showBack: false, showTitle: true, backHandler: undefined },
);

const { headerStyle, headerInnerStyle } = useCustomHeader();

function handleBack(): void {
  if (props.backHandler) {
    props.backHandler();
    return;
  }
  uni.navigateBack();
}
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.pf-page-header__fixed {
  position: fixed;
  z-index: 100;
  top: 0;
  right: 0;
  left: 0;
  background: $pf-color-page;
}

.pf-page-header__spacer {
  box-sizing: border-box;
}

.pf-page-header__inner {
  position: relative;
  display: flex;
  box-sizing: border-box;
  align-items: center;
  padding-left: $pf-space-page-x;
}

.pf-page-header__copy {
  position: absolute;
  top: 50%;
  left: 50%;
  width: calc(100% - 240rpx);
  transform: translate(-50%, -50%);
}

.pf-page-header__title,
.pf-page-header__subtitle {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pf-page-header__title {
  color: $pf-color-text;
  font-size: 32rpx;
  font-weight: 650;
  line-height: 1;
  text-align: center;
}

.pf-page-header__subtitle {
  margin-top: 7rpx;
  color: $pf-color-text-muted;
  font-size: 20rpx;
  line-height: 1;
  text-align: center;
}

.pf-page-header--tab .pf-page-header__copy {
  right: 190rpx;
  left: $pf-space-page-x;
  width: auto;
  transform: translateY(-50%);
}

.pf-page-header--tab .pf-page-header__title,
.pf-page-header--tab .pf-page-header__subtitle {
  text-align: left;
}

.pf-page-header--tab .pf-page-header__title {
  font-size: 35rpx;
}

.pf-page-header__back {
  display: flex;
  width: 64rpx;
  height: 64rpx;
  align-items: center;
  justify-content: flex-start;
}

.pf-page-header__back--pressed {
  opacity: 0.55;
}
</style>
