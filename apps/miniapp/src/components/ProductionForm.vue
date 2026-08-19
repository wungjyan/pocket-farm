<template>
  <view class="form-card pf-card">
    <template v-if="species">
      <view class="field-group">
        <text class="field-label">种类</text>
        <view class="species-summary">
          <view>
            <text class="species-summary__name">{{ species.name }}</text>
            <text class="species-summary__industry">{{ industryLabel(species.industry) }}</text>
          </view>
          <uv-icon name="checkmark-circle" size="19" color="#2F7D4A" />
        </view>
      </view>

      <template v-if="isPlantingIndustry">
        <view class="field-group">
          <text class="field-label">种植标准 <text class="field-required">*</text></text>
          <picker
            mode="selector"
            :range="plantingStandardLabels"
            :value="plantingStandardIndex"
            @change="handlePlantingStandardChange"
          >
            <view class="select-shell">
              <text>{{ plantingStandardLabels[plantingStandardIndex] }}</text>
              <uv-icon name="arrow-down" size="16" color="#929A93" />
            </view>
          </picker>
        </view>

        <view class="field-group">
          <text class="field-label">种植方式 <text class="field-required">*</text></text>
          <picker
            mode="selector"
            :range="plantingMethodLabels"
            :value="plantingMethodIndex"
            @change="handlePlantingMethodChange"
          >
            <view class="select-shell">
              <text>{{ plantingMethodLabels[plantingMethodIndex] }}</text>
              <uv-icon name="arrow-down" size="16" color="#929A93" />
            </view>
          </picker>
        </view>
      </template>

      <view class="field-group">
        <text class="field-label">{{ startedOnLabel }} <text class="field-required">*</text></text>
        <picker mode="date" :value="form.startedOn" :end="today" @change="handleStartedOnChange">
          <view class="select-shell">
            <text>{{ form.startedOn }}</text>
            <uv-icon name="calendar" size="17" color="#929A93" />
          </view>
        </picker>
      </view>

      <FixedUnitNumberField
        v-if="isLivestock"
        label="入栏日龄"
        unit="日"
        placeholder="填写入栏日龄"
        :required="true"
        :value="form.entryAgeDays"
        @change="handleEntryAgeChange"
      />

      <FixedUnitNumberField
        v-if="showInitialQuantity"
        :label="initialQuantityLabel"
        :unit="individualUnitLabel(species.individualUnit)"
        :placeholder="`填写${initialQuantityLabel}`"
        :required="initialQuantityRequired"
        :value="form.initialQuantity"
        @change="handleInitialQuantityChange"
      />

      <view v-if="showWorkMethod" class="field-group">
        <text class="field-label">作业方式 <text class="field-required">*</text></text>
        <picker mode="selector" :range="workMethodLabels" :value="workMethodIndex" @change="handleWorkMethodChange">
          <view class="select-shell">
            <text>{{ workMethodLabels[workMethodIndex] }}</text>
            <uv-icon name="arrow-down" size="16" color="#929A93" />
          </view>
        </picker>
      </view>

      <template v-if="isPlantingIndustry">
        <view class="field-group">
          <text class="field-label">预计采收时间 <text class="field-optional">选填</text></text>
          <picker mode="date" :value="form.expectedHarvestOn" :start="form.startedOn" @change="handleExpectedHarvestChange">
            <view class="select-shell">
              <text :class="{ 'select-placeholder': !form.expectedHarvestOn }">
                {{ form.expectedHarvestOn || "请选择预计采收时间" }}
              </text>
              <uv-icon name="calendar" size="17" color="#929A93" />
            </view>
          </picker>
        </view>

        <FixedUnitNumberField
          v-if="isAgriculture"
          label="预计亩产"
          unit="公斤/亩"
          placeholder="填写预计亩产"
          :value="form.expectedYieldPerMu"
          @change="handleExpectedYieldChange"
        />

        <FixedUnitNumberField
          label="株间距"
          unit="厘米"
          placeholder="填写株间距"
          :value="form.plantSpacingCm"
          @change="handlePlantSpacingChange"
        />
      </template>

      <view class="field-group">
        <text class="field-label">备注 <text class="field-optional">选填</text></text>
        <view class="textarea-shell">
          <textarea
            v-model="form.remark"
            maxlength="1000"
            auto-height
            placeholder="补充说明"
            placeholder-class="textarea-placeholder"
            @input="notifyChange"
          />
        </view>
      </view>
    </template>

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
import { computed, reactive, ref, watch } from "vue";
import FixedUnitNumberField from "./FixedUnitNumberField.vue";
import type {
  PlantingMethod,
  PlantingStandard,
  Production,
  ProductionInput,
  WorkMethod,
} from "../services/production";
import type { IndividualUnit, Industry, Species } from "../services/species";
import { formatNumber } from "../utils/number";

const industryLabels: Record<Industry, string> = {
  AGRICULTURE: "农业",
  FORESTRY: "林业",
  LIVESTOCK: "牧业",
  FISHERY: "渔业",
};
const individualUnitLabels: Record<IndividualUnit, string> = {
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只",
  PLANT: "株",
  TAIL: "尾",
};
const plantingStandardValues: PlantingStandard[] = ["NORMAL", "GREEN", "ORGANIC"];
const plantingStandardLabels = ["普通", "绿色", "有机"];
const plantingMethodValues: PlantingMethod[] = ["TRANSPLANT", "DIRECT_SEEDING"];
const plantingMethodLabels = ["移栽", "直播"];
const workMethodValues: WorkMethod[] = ["MANUAL", "MECHANICAL"];
const workMethodLabels = ["人工", "机械"];

const props = withDefaults(
  defineProps<{
    initialProduction?: Production | null;
    initialSpecies?: Species | null;
    initialVariety?: string;
    submitLabel?: string;
    loadingText?: string;
    submitting?: boolean;
  }>(),
  {
    initialProduction: null,
    initialSpecies: null,
    initialVariety: "",
    submitLabel: "保存修改",
    loadingText: "保存中",
    submitting: false,
  },
);

const emit = defineEmits<{
  submit: [input: ProductionInput];
  change: [];
}>();

const species = ref<Species | null>(null);
const today = formatToday();
const form = reactive({
  variety: "",
  startedOn: today,
  plantingStandard: "NORMAL" as PlantingStandard,
  plantingMethod: "TRANSPLANT" as PlantingMethod,
  workMethod: "MANUAL" as WorkMethod,
  expectedHarvestOn: "",
  expectedYieldPerMu: "",
  initialQuantity: "",
  plantSpacingCm: "",
  entryAgeDays: "",
  remark: "",
});
const isAgriculture = computed(() => species.value?.industry === "AGRICULTURE");
const isPlantingIndustry = computed(
  () => isAgriculture.value || species.value?.industry === "FORESTRY",
);
const isLivestock = computed(() => species.value?.industry === "LIVESTOCK");
const showInitialQuantity = computed(() => Boolean(species.value));
const initialQuantityRequired = computed(() => !isAgriculture.value);
const showWorkMethod = computed(
  () => isPlantingIndustry.value || species.value?.industry === "FISHERY",
);
const startedOnLabel = computed(() => {
  if (isPlantingIndustry.value) {
    return form.plantingMethod === "DIRECT_SEEDING" ? "播种时间" : "移栽时间";
  }
  return isLivestock.value ? "入栏时间" : "养殖时间";
});
const initialQuantityLabel = computed(() => {
  if (isPlantingIndustry.value) {
    return form.plantingMethod === "DIRECT_SEEDING" ? "播种数量" : "移栽数量";
  }
  return isLivestock.value ? "入栏数量" : "养殖数量";
});
const plantingStandardIndex = computed(() => plantingStandardValues.indexOf(form.plantingStandard));
const plantingMethodIndex = computed(() => plantingMethodValues.indexOf(form.plantingMethod));
const workMethodIndex = computed(() => workMethodValues.indexOf(form.workMethod));

watch(
  () => [props.initialProduction, props.initialSpecies, props.initialVariety] as const,
  ([production, initialSpecies, initialVariety]) => {
    species.value = production
      ? {
          id: production.speciesId,
          name: production.speciesName,
          industry: production.industry,
          individualUnit: production.individualUnit,
          createdAt: production.createdAt,
        }
      : initialSpecies;
    form.variety = production?.variety || initialVariety;
    form.startedOn = production?.startedOn || today;
    form.plantingStandard = production?.plantingStandard || "NORMAL";
    form.plantingMethod = production?.plantingMethod || "TRANSPLANT";
    form.workMethod = production?.workMethod || "MANUAL";
    form.expectedHarvestOn = production?.expectedHarvestOn || "";
    form.expectedYieldPerMu = formatNumber(production?.expectedYieldPerMu);
    form.initialQuantity = formatNumber(production?.initialQuantity);
    form.plantSpacingCm = formatNumber(production?.plantSpacingCm);
    form.entryAgeDays = production?.entryAgeDays?.toString() || "";
    form.remark = production?.remark || "";
  },
  { immediate: true },
);

function industryLabel(industry: Industry): string {
  return industryLabels[industry];
}

function individualUnitLabel(unit: IndividualUnit): string {
  return individualUnitLabels[unit];
}

function formatToday(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function handleStartedOnChange(event: { detail: { value: string } }): void {
  form.startedOn = event.detail.value;
  notifyChange();
}

function handleExpectedHarvestChange(event: { detail: { value: string } }): void {
  form.expectedHarvestOn = event.detail.value;
  notifyChange();
}

function handlePlantingStandardChange(event: { detail: { value: number | string } }): void {
  form.plantingStandard = plantingStandardValues[Number(event.detail.value)] || "NORMAL";
  notifyChange();
}

function handlePlantingMethodChange(event: { detail: { value: number | string } }): void {
  form.plantingMethod = plantingMethodValues[Number(event.detail.value)] || "TRANSPLANT";
  notifyChange();
}

function handleWorkMethodChange(event: { detail: { value: number | string } }): void {
  form.workMethod = workMethodValues[Number(event.detail.value)] || "MANUAL";
  notifyChange();
}

function handleExpectedYieldChange(value: string): void {
  form.expectedYieldPerMu = value;
  notifyChange();
}

function handleInitialQuantityChange(value: string): void {
  form.initialQuantity = value;
  notifyChange();
}

function handlePlantSpacingChange(value: string): void {
  form.plantSpacingCm = value;
  notifyChange();
}

function handleEntryAgeChange(value: string): void {
  form.entryAgeDays = value;
  notifyChange();
}

function notifyChange(): void {
  emit("change");
}

function parsePositiveNumber(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function parseEntryAge(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : null;
}

function handleSubmit(): void {
  if (!species.value) {
    uni.showToast({ title: "请选择种类", icon: "none" });
    return;
  }
  const initialQuantity = parsePositiveNumber(form.initialQuantity);
  const expectedYieldPerMu = parsePositiveNumber(form.expectedYieldPerMu);
  const plantSpacingCm = parsePositiveNumber(form.plantSpacingCm);
  const entryAgeDays = parseEntryAge(form.entryAgeDays);
  if (form.initialQuantity.trim() && (initialQuantity === null || !Number.isInteger(initialQuantity))) {
    uni.showToast({ title: `${initialQuantityLabel.value}需为正整数`, icon: "none" });
    return;
  }
  if (form.expectedYieldPerMu.trim() && expectedYieldPerMu === null) {
    uni.showToast({ title: "预计亩产需大于 0", icon: "none" });
    return;
  }
  if (form.plantSpacingCm.trim() && plantSpacingCm === null) {
    uni.showToast({ title: "株间距需大于 0", icon: "none" });
    return;
  }
  if (isLivestock.value && entryAgeDays === null) {
    uni.showToast({ title: "请填写入栏日龄", icon: "none" });
    return;
  }
  if (form.entryAgeDays.trim() && entryAgeDays === null) {
    uni.showToast({ title: "入栏日龄需为非负整数", icon: "none" });
    return;
  }
  if (initialQuantityRequired.value && initialQuantity === null) {
    uni.showToast({ title: `请填写${initialQuantityLabel.value}`, icon: "none" });
    return;
  }
  emit("submit", {
    speciesId: species.value.id,
    variety: form.variety.trim() || null,
    startedOn: form.startedOn,
    plantingStandard: isPlantingIndustry.value ? form.plantingStandard : null,
    plantingMethod: isPlantingIndustry.value ? form.plantingMethod : null,
    workMethod: showWorkMethod.value ? form.workMethod : null,
    expectedHarvestOn: isPlantingIndustry.value ? form.expectedHarvestOn || null : null,
    expectedYieldPerMu: isAgriculture.value ? expectedYieldPerMu : null,
    initialQuantity,
    plantSpacingCm: isPlantingIndustry.value ? plantSpacingCm : null,
    entryAgeDays: isLivestock.value ? entryAgeDays : null,
    remark: form.remark.trim() || null,
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
  margin-left: 8rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 400;
}

.field-required {
  margin-left: 6rpx;
  color: #c96a45;
}

.select-shell,
.textarea-shell {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
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

.species-summary {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  padding: 0 20rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface-muted;
}

.species-summary__name,
.species-summary__industry {
  display: block;
}

.species-summary__name {
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 600;
}

.species-summary__industry {
  margin-top: 4rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.textarea-shell {
  min-height: 160rpx;
  align-items: flex-start;
  padding: 18rpx 20rpx;
}

.textarea-shell textarea {
  width: 100%;
  min-height: 110rpx;
  color: $pf-color-text;
  font-size: 25rpx;
  line-height: 1.5;
}

.textarea-placeholder {
  color: $pf-color-text-muted;
}
</style>
