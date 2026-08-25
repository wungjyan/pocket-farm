<template>
  <view class="production-form pf-page-content">
    <template v-if="species">
      <view class="required-fields">
        <view class="form-item">
          <view class="field-group">
            <text class="field-label">种类</text>
            <view class="species-summary">
              <view>
                <text class="species-summary__name">{{ species.name }}</text>
                <text class="species-summary__industry">{{ industryLabel(species.industry) }}</text>
              </view>
            </view>
          </view>
        </view>

        <view v-if="showPlotField" class="form-item">
          <view class="field-group">
            <text class="field-label">地块 <text class="field-required">*</text></text>
            <view
              class="select-shell plot-select"
              :class="{ 'plot-select--disabled': !plotSelectable }"
              @tap="handlePlotSelect"
            >
              <view v-if="initialPlot" class="plot-select__copy">
                <text class="plot-select__name">{{ initialPlot.name }}</text>
                <text class="plot-select__meta">{{ plotMeta(initialPlot) }}</text>
              </view>
              <text v-else class="select-placeholder">请选择地块</text>
              <uv-icon v-if="plotSelectable" name="arrow-right" size="17" color="#7F8B82" />
            </view>
          </view>
        </view>

        <template v-if="isPlantingIndustry">
          <view class="form-item">
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
          </view>

          <view class="form-item">
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
          </view>
        </template>

        <view class="form-item">
          <view class="field-group">
            <text class="field-label">{{ startedOnLabel }} <text class="field-required">*</text></text>
            <picker mode="date" :value="form.startedOn" :end="today" @change="handleStartedOnChange">
              <view class="select-shell">
                <text>{{ form.startedOn }}</text>
                <uv-icon name="calendar" size="17" color="#929A93" />
              </view>
            </picker>
          </view>
        </view>

        <view v-if="isLivestock" class="form-item">
          <FixedUnitNumberField
            label="入栏日龄"
            unit="日"
            placeholder="填写入栏日龄"
            :required="true"
            :value="form.entryAgeDays"
            @change="handleEntryAgeChange"
          />
        </view>

        <view v-if="showInitialQuantity && initialQuantityRequired" class="form-item">
          <FixedUnitNumberField
            :label="initialQuantityLabel"
            :unit="individualUnitLabel(species.individualUnit)"
            :placeholder="`填写${initialQuantityLabel}`"
            :required="true"
            :value="form.initialQuantity"
            @change="handleInitialQuantityChange"
          />
        </view>

        <view v-if="showWorkMethod" class="form-item">
          <view class="field-group">
            <text class="field-label">作业方式 <text class="field-required">*</text></text>
            <picker mode="selector" :range="workMethodLabels" :value="workMethodIndex" @change="handleWorkMethodChange">
              <view class="select-shell">
                <text>{{ workMethodLabels[workMethodIndex] }}</text>
                <uv-icon name="arrow-down" size="16" color="#929A93" />
              </view>
            </picker>
          </view>
        </view>
      </view>

      <view class="optional-section">
        <view class="optional-section__trigger pf-tappable" @tap="toggleOptionalSection">
          <view class="optional-section__heading">
            <text class="optional-section__title">选填信息</text>
            <text v-if="filledOptionalCount" class="optional-section__count">{{ filledOptionalCount }}</text>
          </view>
          <uv-icon :name="optionalExpanded ? 'arrow-up' : 'arrow-down'" size="16" color="#7F8B82" />
        </view>

        <view v-if="optionalExpanded" class="optional-fields">
          <view class="form-item">
            <view class="field-group">
              <text class="field-label">品种</text>
              <view class="input-shell">
                <uv-input
                  v-model="form.variety"
                  maxlength="100"
                  clearable
                  border="none"
                  placeholder="填写品种"
                  placeholder-style="color: #7F8B82;"
                  color="#17231B"
                  @input="notifyChange"
                />
              </view>
            </view>
          </view>

          <view v-if="showInitialQuantity && !initialQuantityRequired" class="form-item">
            <FixedUnitNumberField
              :label="initialQuantityLabel"
              :unit="individualUnitLabel(species.individualUnit)"
              :placeholder="`填写${initialQuantityLabel}`"
              :value="form.initialQuantity"
              @change="handleInitialQuantityChange"
            />
          </view>

          <template v-if="isPlantingIndustry">
            <view class="form-item">
              <view class="field-group">
                <text class="field-label">预计采收时间</text>
                <picker mode="date" :value="form.expectedHarvestOn" :start="form.startedOn" @change="handleExpectedHarvestChange">
                  <view class="select-shell">
                    <text :class="{ 'select-placeholder': !form.expectedHarvestOn }">
                      {{ form.expectedHarvestOn || "请选择预计采收时间" }}
                    </text>
                    <uv-icon name="calendar" size="17" color="#929A93" />
                  </view>
                </picker>
              </view>
            </view>

            <view v-if="isAgriculture" class="form-item">
              <FixedUnitNumberField
                label="预计亩产"
                unit="公斤/亩"
                placeholder="填写预计亩产"
                :value="form.expectedYieldPerMu"
                @change="handleExpectedYieldChange"
              />
            </view>

            <view class="form-item">
              <FixedUnitNumberField
                label="株间距"
                unit="厘米"
                placeholder="填写株间距"
                :value="form.plantSpacingCm"
                @change="handlePlantSpacingChange"
              />
            </view>
          </template>

          <view class="form-item">
            <view class="field-group">
              <text class="field-label">备注</text>
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
          </view>
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
import type { Plot, PlotType } from "../services/plot";
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
    initialPlot?: Plot | null;
    showPlotField?: boolean;
    plotSelectable?: boolean;
    submitLabel?: string;
    loadingText?: string;
    submitting?: boolean;
  }>(),
  {
    initialProduction: null,
    initialSpecies: null,
    initialVariety: "",
    initialPlot: null,
    showPlotField: false,
    plotSelectable: false,
    submitLabel: "保存修改",
    loadingText: "保存中",
    submitting: false,
  },
);

const emit = defineEmits<{
  submit: [input: ProductionInput];
  change: [];
  "select-plot": [];
}>();

const species = ref<Species | null>(null);
const today = formatToday();
const optionalExpanded = ref(false);
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
const filledOptionalCount = computed(() => {
  const optionalValues = [form.variety, form.remark];
  if (!initialQuantityRequired.value) optionalValues.push(form.initialQuantity);
  if (isPlantingIndustry.value) {
    optionalValues.push(form.expectedHarvestOn, form.plantSpacingCm);
  }
  if (isAgriculture.value) optionalValues.push(form.expectedYieldPerMu);
  return optionalValues.filter((value) => value.trim()).length;
});

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
    optionalExpanded.value = filledOptionalCount.value > 0;
  },
  { immediate: true },
);

function industryLabel(industry: Industry): string {
  return industryLabels[industry];
}

const plotTypeLabels: Record<PlotType, string> = {
  FIELD: "大田",
  PADDY: "水田",
  GREENHOUSE: "大棚",
  ORCHARD: "果园",
  FOREST: "林地",
  POND: "鱼塘",
  BARN: "栏舍",
  OTHER: "其他",
};

function plotMeta(plot: Plot): string {
  const type = plot.type ? plotTypeLabels[plot.type] : "未分类";
  if (plot.areaValue === null || plot.areaValue === undefined || !plot.areaUnit) return type;
  const units: Record<string, string> = { MU: "亩", SQUARE_METER: "平方米", HECTARE: "公顷" };
  return `${type} · ${formatNumber(plot.areaValue)}${units[plot.areaUnit] || ""}`;
}

function handlePlotSelect(): void {
  if (props.plotSelectable) emit("select-plot");
}

function toggleOptionalSection(): void {
  optionalExpanded.value = !optionalExpanded.value;
}

function showOptionalSection(): void {
  optionalExpanded.value = true;
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
  if (props.showPlotField && !props.initialPlot) {
    uni.showToast({ title: "请选择地块", icon: "none" });
    return;
  }
  if (!species.value) {
    uni.showToast({ title: "请选择种类", icon: "none" });
    return;
  }
  const initialQuantity = parsePositiveNumber(form.initialQuantity);
  const expectedYieldPerMu = parsePositiveNumber(form.expectedYieldPerMu);
  const plantSpacingCm = parsePositiveNumber(form.plantSpacingCm);
  const entryAgeDays = parseEntryAge(form.entryAgeDays);
  if (form.initialQuantity.trim() && (initialQuantity === null || !Number.isInteger(initialQuantity))) {
    if (!initialQuantityRequired.value) showOptionalSection();
    uni.showToast({ title: `${initialQuantityLabel.value}需为正整数`, icon: "none" });
    return;
  }
  if (form.expectedYieldPerMu.trim() && expectedYieldPerMu === null) {
    showOptionalSection();
    uni.showToast({ title: "预计亩产需大于 0", icon: "none" });
    return;
  }
  if (form.plantSpacingCm.trim() && plantSpacingCm === null) {
    showOptionalSection();
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

.production-form {
  padding-bottom: 0;
}

.form-item + .form-item {
  margin-top: $pf-space-5;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.field-required {
  margin-left: 6rpx;
  color: $pf-color-danger;
}

.select-shell,
.input-shell,
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

.input-shell {
  padding: 0 20rpx;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}

.plot-select--disabled {
  background: $pf-color-surface-muted;
}

.plot-select__copy,
.plot-select__name,
.plot-select__meta {
  display: block;
}

.plot-select__name {
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 650;
}

.plot-select__meta {
  margin-top: 5rpx;
  color: $pf-color-text-muted;
  font-size: 21rpx;
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

.optional-section {
  margin-top: $pf-space-6;
}

.optional-section__trigger {
  display: flex;
  min-height: 56rpx;
  align-items: center;
  justify-content: space-between;
}

.optional-section__heading {
  display: flex;
  align-items: baseline;
}

.optional-section__title {
  color: $pf-color-text-secondary;
  font-size: 26rpx;
  font-weight: 600;
}

.optional-section__count {
  margin-left: 10rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
}

.optional-fields {
  margin-top: $pf-space-4;
}
</style>
