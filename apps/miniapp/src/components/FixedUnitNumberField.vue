<template>
  <view class="field-group">
    <text class="field-label">
      {{ label }}
      <text v-if="required" class="field-required">*</text>
      <text v-else class="field-optional">选填</text>
    </text>
    <view class="input-shell">
      <uv-input
        :model-value="value"
        type="digit"
        maxlength="12"
        clearable
        border="none"
        :placeholder="placeholder"
        placeholder-style="color: #748178;"
        color="#17261F"
        @input="handleChange"
      />
      <text class="input-unit">{{ unit }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string;
    unit: string;
    placeholder?: string;
    required?: boolean;
    value?: string;
  }>(),
  {
    placeholder: "填写数量",
    required: false,
    value: "",
  },
);

const emit = defineEmits<{
  change: [value: string];
}>();

function handleChange(value: string): void {
  emit("change", value);
}
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.field-group + .field-group {
  margin-top: 32rpx;
}

.field-label {
  display: block;
  margin-bottom: 12rpx;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.field-optional {
  margin-left: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  font-weight: $pf-font-weight-medium;
}

.field-required {
  margin-left: $pf-space-1;
  color: $pf-color-danger;
}

.input-shell {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 $pf-space-3;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.input-shell :deep(.uv-input) {
  flex: 1;
}

.input-unit {
  flex-shrink: 0;
  margin-left: $pf-space-2;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
}
</style>
