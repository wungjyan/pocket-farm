<template>
  <view class="form-card pf-card">
    <view class="field-group">
      <text class="field-label">地块名称</text>
      <view class="input-shell" :class="{ 'input-shell--focused': nameFocused }">
        <uv-input
          v-model="form.name"
          maxlength="100"
          clearable
          border="none"
          placeholder="例如：1号大棚"
          placeholder-style="color: #929A93;"
          color="#202821"
          @focus="nameFocused = true"
          @blur="nameFocused = false"
          @input="notifyChange"
        />
      </view>
    </view>

    <view class="field-group">
      <text class="field-label">地块类型 <text class="field-optional">选填</text></text>
      <picker mode="selector" :range="plotTypeLabels" :value="plotTypeIndex" @change="handleTypeChange">
        <view class="select-shell">
          <text :class="{ 'select-placeholder': !form.type }">{{ form.type ? plotTypeLabels[plotTypeIndex] : "请选择地块类型" }}</text>
          <uv-icon name="arrow-down" size="16" color="#929A93" />
        </view>
      </picker>
    </view>

    <view class="field-group">
      <text class="field-label">面积 <text class="field-optional">选填</text></text>
      <view class="area-row">
        <view class="input-shell area-input-shell" :class="{ 'input-shell--focused': areaFocused }">
          <uv-input
            v-model="form.areaValue"
            type="digit"
            maxlength="12"
            clearable
            border="none"
            placeholder="填写面积"
            placeholder-style="color: #929A93;"
            color="#202821"
            @focus="areaFocused = true"
            @blur="areaFocused = false"
            @input="notifyChange"
          />
        </view>
        <picker mode="selector" :range="areaUnitLabels" :value="areaUnitIndex" @change="handleUnitChange">
          <view class="select-shell unit-shell">
            <text :class="{ 'select-placeholder': !form.areaUnit }">{{ form.areaUnit ? areaUnitLabels[areaUnitIndex] : "单位" }}</text>
            <uv-icon name="arrow-down" size="16" color="#929A93" />
          </view>
        </picker>
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
import type { AreaUnit, PlotType } from "../services/plot";
import { formatNumber } from "../utils/number";

const plotTypeValues: PlotType[] = [
  "FIELD",
  "PADDY",
  "GREENHOUSE",
  "ORCHARD",
  "FOREST",
  "POND",
  "BARN",
  "OTHER",
];
const plotTypeLabels = ["大田", "水田", "大棚", "果园", "林地", "鱼塘", "栏舍", "其他"];
const areaUnitValues: AreaUnit[] = ["MU", "SQUARE_METER", "HECTARE"];
const areaUnitLabels = ["亩", "平方米", "公顷"];

const props = withDefaults(
  defineProps<{
    initialName?: string;
    initialType?: PlotType | null;
    initialAreaValue?: number | string | null;
    initialAreaUnit?: AreaUnit | null;
    submitLabel?: string;
    loadingText?: string;
    submitting?: boolean;
  }>(),
  {
    initialName: "",
    initialType: null,
    initialAreaValue: null,
    initialAreaUnit: null,
    submitLabel: "保存修改",
    loadingText: "保存中",
    submitting: false,
  },
);

const emit = defineEmits<{
  submit: [{ name: string; type: PlotType | null; areaValue: number | null; areaUnit: AreaUnit | null }];
  change: [];
}>();

const form = reactive<{ name: string; type: PlotType | null; areaValue: string; areaUnit: AreaUnit | null }>({
  name: "",
  type: null,
  areaValue: "",
  areaUnit: null,
});
const nameFocused = ref(false);
const areaFocused = ref(false);

const plotTypeIndex = ref(0);
const areaUnitIndex = ref(0);

watch(
  () => [props.initialName, props.initialType, props.initialAreaValue, props.initialAreaUnit],
  () => {
    form.name = props.initialName;
    form.type = props.initialType;
    form.areaValue = formatNumber(props.initialAreaValue);
    form.areaUnit = props.initialAreaUnit;
    plotTypeIndex.value = form.type ? plotTypeValues.indexOf(form.type) : 0;
    areaUnitIndex.value = form.areaUnit ? areaUnitValues.indexOf(form.areaUnit) : 0;
  },
  { immediate: true },
);

function handleTypeChange(event: { detail: { value: number | string } }): void {
  plotTypeIndex.value = Number(event.detail.value);
  form.type = plotTypeValues[plotTypeIndex.value] || null;
  notifyChange();
}

function handleUnitChange(event: { detail: { value: number | string } }): void {
  areaUnitIndex.value = Number(event.detail.value);
  form.areaUnit = areaUnitValues[areaUnitIndex.value] || null;
  notifyChange();
}

function notifyChange(): void {
  emit("change");
}

function handleSubmit(): void {
  const parsedArea = form.areaValue.trim() ? Number(form.areaValue) : null;
  emit("submit", {
    name: form.name.trim(),
    type: form.type,
    areaValue: parsedArea !== null && Number.isFinite(parsedArea) ? parsedArea : null,
    areaUnit: form.areaUnit,
  });
}
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.form-card {
  padding: 28rpx 24rpx;
}

.field-group + .field-group {
  margin-top: 32rpx;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.field-optional {
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 400;
}

.input-shell,
.select-shell {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.input-shell {
  padding: 0 20rpx;
}

.input-shell--focused {
  border-color: $pf-color-primary;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}

.select-shell {
  justify-content: space-between;
  padding: 0 20rpx;
  color: $pf-color-text;
  font-size: 25rpx;
}

.select-placeholder {
  color: $pf-color-text-muted;
}

.area-row {
  display: flex;
  align-items: center;
}

.area-input-shell {
  flex: 1;
}

.unit-shell {
  width: 190rpx;
  margin-left: 16rpx;
}
</style>
