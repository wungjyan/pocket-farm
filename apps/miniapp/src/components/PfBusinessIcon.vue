<template>
  <view :class="iconClasses">
    <image class="pf-business-icon__image" :src="iconPath" mode="aspectFit" />
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

export type BusinessIconName =
  | "sprout"
  | "shovel"
  | "shopping-basket"
  | "land-plot"
  | "list"
  | "clock-3"
  | "settings"
  | "map";

type BusinessIconSize = "normal" | "empty" | "compact";
type BusinessIconVariant = "contained" | "plain";

const props = withDefaults(
  defineProps<{
    name: BusinessIconName;
    size?: BusinessIconSize;
    variant?: BusinessIconVariant;
    muted?: boolean;
  }>(),
  {
    size: "normal",
    variant: "contained",
    muted: false,
  },
);

const iconPath = computed(() => `/static/icons/business/${props.name}.png`);
const iconClasses = computed(() => [
  "pf-business-icon",
  `pf-business-icon--${props.size}`,
  `pf-business-icon--${props.variant}`,
  { "pf-business-icon--muted": props.muted },
]);
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.pf-business-icon {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  background: $pf-color-primary-soft;
  border-radius: $pf-radius-control;
}

.pf-business-icon--normal {
  width: 56rpx;
  height: 56rpx;
}

.pf-business-icon--empty {
  width: 72rpx;
  height: 72rpx;
  border-radius: 22rpx;
}

.pf-business-icon--compact {
  width: 40rpx;
  height: 40rpx;
  border-radius: 12rpx;
}

.pf-business-icon--plain {
  background: transparent;
  border-radius: 0;
}

.pf-business-icon__image {
  display: block;
  width: 32rpx;
  height: 32rpx;
}

.pf-business-icon--empty .pf-business-icon__image {
  width: 40rpx;
  height: 40rpx;
}

.pf-business-icon--compact .pf-business-icon__image {
  width: 36rpx;
  height: 36rpx;
}

.pf-business-icon--muted .pf-business-icon__image {
  opacity: 0.35;
}
</style>
