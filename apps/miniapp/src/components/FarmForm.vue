<template>
  <view class="farm-form" :class="{ 'farm-form--card pf-card': framed }">
    <view class="field-group">
      <text class="field-label">农场名称<text class="field-required"> *</text></text>
      <view class="input-shell" :class="{ 'input-shell--focused': nameFocused }">
        <uv-input
          v-model="form.name"
          maxlength="100"
          clearable
          border="none"
          placeholder="例如：开心农场"
          placeholder-style="color: #929A93;"
          color="#202821"
          @focus="nameFocused = true"
          @blur="nameFocused = false"
          @input="notifyChange"
        />
      </view>
    </view>

    <view class="field-group field-group--region">
      <text class="field-label">所在地区 <text class="field-optional">选填</text></text>
      <view class="input-shell" :class="{ 'input-shell--focused': regionFocused }">
        <uv-input
          v-model="form.region"
          maxlength="100"
          clearable
          border="none"
          placeholder="例如：上海市浦东新区"
          placeholder-style="color: #929A93;"
          color="#202821"
          @focus="regionFocused = true"
          @blur="regionFocused = false"
          @input="notifyChange"
        />
      </view>
    </view>

    <uv-button
      type="primary"
      size="large"
      shape="square"
      :loading="submitting"
      :loading-text="loadingText"
      custom-style="height: 88rpx; margin-top: 42rpx; border-radius: 16rpx;"
      @click="handleSubmit"
    >
      {{ submitLabel }}
    </uv-button>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    initialName?: string;
    initialRegion?: string | null;
    framed?: boolean;
    submitLabel?: string;
    loadingText?: string;
    submitting?: boolean;
  }>(),
  {
    initialName: "",
    initialRegion: "",
    framed: true,
    submitLabel: "保存修改",
    loadingText: "保存中",
    submitting: false,
  },
);

const emit = defineEmits<{
  submit: [{ name: string; region: string | null }];
  change: [{ name: string; region: string | null }];
}>();

const form = reactive({ name: "", region: "" });
const nameFocused = ref(false);
const regionFocused = ref(false);

watch(
  () => [props.initialName, props.initialRegion],
  () => {
    form.name = props.initialName;
    form.region = props.initialRegion || "";
  },
  { immediate: true },
);

function handleSubmit(): void {
  emit("submit", {
    name: form.name.trim(),
    region: form.region.trim() || null,
  });
}

function notifyChange(): void {
  emit("change", {
    name: form.name,
    region: form.region || null,
  });
}
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.farm-form--card {
  padding: 28rpx 24rpx;
}

.field-group--region {
  margin-top: 32rpx;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.field-required {
  color: $pf-color-danger;
}

.field-optional {
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 400;
}

.input-shell {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 20rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.input-shell--focused {
  border-color: $pf-color-primary;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}
</style>
