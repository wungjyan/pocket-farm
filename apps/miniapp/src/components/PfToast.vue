<template>
  <view
    v-if="visible"
    class="pf-toast-host"
    :class="`pf-toast-host--${position}`"
    role="status"
    aria-live="polite"
  >
    <view class="pf-toast" :class="`pf-toast--${type}`">
      <image class="pf-toast__icon" :src="iconPath" mode="aspectFit" />
      <text class="pf-toast__message">{{ message }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from "vue";

export type PfToastType = "info" | "error";
export type PfToastPosition = "top" | "upper" | "bottom";

export interface PfToastOptions {
  message: string;
  type?: PfToastType;
  position?: PfToastPosition;
  duration?: number;
}

const visible = ref(false);
const message = ref("");
const type = ref<PfToastType>("info");
const position = ref<PfToastPosition>("upper");
let hideTimer: ReturnType<typeof setTimeout> | null = null;

const iconPath = computed(() =>
  type.value === "error"
    ? "/static/icons/lucide/circle-alert.svg"
    : "/static/icons/lucide/info.svg",
);

function clearHideTimer(): void {
  if (hideTimer) {
    clearTimeout(hideTimer);
    hideTimer = null;
  }
}

function hide(): void {
  clearHideTimer();
  visible.value = false;
}

function show(options: PfToastOptions): void {
  clearHideTimer();
  message.value = options.message;
  type.value = options.type ?? "info";
  position.value = options.position ?? "upper";
  visible.value = true;
  hideTimer = setTimeout(hide, options.duration ?? 2400);
}

onUnmounted(clearHideTimer);

defineExpose({ show, hide });
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.pf-toast-host {
  position: fixed;
  z-index: 10090;
  right: $pf-space-page-x;
  left: $pf-space-page-x;
  display: flex;
  justify-content: center;
  pointer-events: none;
}

.pf-toast-host--top {
  top: $pf-space-3;
}

.pf-toast-host--upper {
  top: 36%;
}

.pf-toast-host--bottom {
  bottom: calc($pf-space-6 + env(safe-area-inset-bottom));
}

.pf-toast {
  display: flex;
  max-width: 100%;
  min-height: 72rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 16rpx $pf-space-3;
  border: 1rpx solid;
  border-radius: $pf-radius-control;
  box-shadow: $pf-shadow-raised;
  animation: pf-toast-enter $pf-duration-fast ease-out;
}

.pf-toast--info {
  border-color: $pf-mint-200;
  background: $pf-color-primary-soft;
  color: $pf-color-primary-strong;
}

.pf-toast--error {
  border-color: $pf-color-danger-disabled;
  background: $pf-color-danger-soft;
  color: $pf-color-danger;
}

.pf-toast__icon {
  display: block;
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

.pf-toast__message {
  min-width: 0;
  margin-left: $pf-space-2;
  color: inherit;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
  line-height: 1.45;
  word-break: break-word;
}

@keyframes pf-toast-enter {
  from {
    opacity: 0;
    transform: translateY(-8rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
