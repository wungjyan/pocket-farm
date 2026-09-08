<template>
  <view :class="rootClasses">
    <view class="pf-empty-state__icon">
      <image class="pf-empty-state__icon-image" :src="iconPath" mode="aspectFit" />
    </view>
    <text class="pf-empty-state__title">{{ title }}</text>
    <view
      v-if="actionText"
      :class="actionClasses"
      hover-class="pf-empty-state__action--pressed"
      role="button"
      :aria-label="actionText"
      @tap="emit('action')"
    >
      <text>{{ actionText }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

export type EmptyStateIcon =
  | "clock-3"
  | "land-plot"
  | "search-x"
  | "shopping-basket"
  | "shovel"
  | "sparkles"
  | "sprout";
export type EmptyStateVariant = "page" | "card" | "inline";
export type EmptyStateActionType = "primary" | "text";

const props = withDefaults(
  defineProps<{
    title: string;
    icon: EmptyStateIcon;
    variant?: EmptyStateVariant;
    actionText?: string;
    actionType?: EmptyStateActionType;
  }>(),
  {
    variant: "page",
    actionText: "",
    actionType: "primary",
  },
);

const emit = defineEmits<{
  action: [];
}>();

const iconPaths: Record<EmptyStateIcon, string> = {
  "clock-3": "/static/icons/lucide/clock-3.svg",
  "land-plot": "/static/icons/lucide/land-plot.svg",
  "search-x": "/static/icons/lucide/search-x.svg",
  "shopping-basket": "/static/icons/lucide/shopping-basket.svg",
  shovel: "/static/icons/lucide/shovel.svg",
  sparkles: "/static/icons/lucide/sparkles-empty.svg",
  sprout: "/static/icons/lucide/sprout.svg",
};

const iconPath = computed(() => iconPaths[props.icon]);
const rootClasses = computed(() => [
  "pf-empty-state",
  `pf-empty-state--${props.variant}`,
]);
const actionClasses = computed(() => [
  "pf-empty-state__action",
  `pf-empty-state__action--${props.actionType}`,
]);
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.pf-empty-state {
  display: flex;
  box-sizing: border-box;
  align-items: center;
  color: $pf-color-text-secondary;
}

.pf-empty-state--page,
.pf-empty-state--card {
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

.pf-empty-state--page {
  min-height: 360rpx;
  padding: $pf-space-6 $pf-space-4;
}

.pf-empty-state--card {
  min-height: 220rpx;
  padding: $pf-space-5 $pf-space-4;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.pf-empty-state--inline {
  min-height: 112rpx;
  padding: 0 $pf-space-3;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.pf-empty-state__icon {
  display: flex;
  width: 72rpx;
  height: 72rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 22rpx;
  background: $pf-color-primary-soft;
}

.pf-empty-state__icon-image {
  display: block;
  width: 40rpx;
  height: 40rpx;
}

.pf-empty-state__title {
  display: block;
  margin-top: $pf-space-3;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-medium;
}

.pf-empty-state--inline .pf-empty-state__icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: $pf-radius-control;
}

.pf-empty-state--inline .pf-empty-state__icon-image {
  width: 32rpx;
  height: 32rpx;
}

.pf-empty-state--inline .pf-empty-state__title {
  min-width: 0;
  flex: 1;
  margin-top: 0;
  margin-left: $pf-space-2;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  text-align: left;
}

.pf-empty-state__action {
  display: flex;
  min-height: 80rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  margin-top: $pf-space-3;
  padding: 0 $pf-space-4;
  border-radius: $pf-radius-control;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
}

.pf-empty-state__action--primary {
  min-width: 208rpx;
  background: $pf-color-primary;
  color: $pf-color-on-primary;
}

.pf-empty-state__action--text {
  color: $pf-color-primary;
}

.pf-empty-state--inline .pf-empty-state__action {
  min-width: auto;
  min-height: 72rpx;
  flex-shrink: 0;
  margin-top: 0;
  margin-left: $pf-space-2;
  padding: 0 $pf-space-2;
}

.pf-empty-state__action--pressed {
  opacity: 0.68;
}
</style>
