<template>
  <view class="operation-form pf-page-content">
    <view class="form-item">
      <view class="field-group">
        <text class="field-label">地块 <text class="field-required">*</text></text>
        <view
          class="select-shell plot-select"
          :class="{ 'select-shell--disabled': !plotSelectable }"
          @tap="handlePlotSelect"
        >
          <view v-if="plot" class="plot-select__copy">
            <text class="plot-select__name">{{ plot.name }}</text>
            <text class="plot-select__meta">{{ plotMeta(plot) }}</text>
          </view>
          <text v-else class="select-placeholder">请选择地块</text>
          <PfRowChevron v-if="plotSelectable" />
        </view>
      </view>
    </view>

    <view class="form-item">
      <view class="field-group">
        <text class="field-label">农事类型 <text class="field-required">*</text></text>
        <view class="select-shell" @tap="emit('select-operation-type')">
          <text :class="{ 'select-placeholder': !selectedOperationType }">
            {{ selectedOperationType?.name || "请选择农事类型" }}
          </text>
          <PfRowChevron />
        </view>
      </view>
    </view>

    <view class="form-item">
      <view class="field-group">
        <text class="field-label">关联种养 <text class="field-optional">选填</text></text>
        <view class="select-shell" :class="{ 'select-shell--disabled': !hasPlot }" @tap="handleSelectProduction">
          <text :class="{ 'select-placeholder': !selectedProduction && !hasPlot }">
            {{ selectedProduction ? productionLabel(selectedProduction) : hasPlot ? "暂不关联种养" : "请先选择地块" }}
          </text>
          <PfRowChevron v-if="hasPlot" />
        </view>
      </view>
    </view>

    <view class="form-item">
      <view class="field-group">
        <text class="field-label">作业方式 <text class="field-required">*</text></text>
        <picker mode="selector" :range="workMethodLabels" :value="workMethodIndex" @change="handleWorkMethodChange">
          <view class="select-shell">
            <text>{{ workMethodLabels[workMethodIndex] }}</text>
            <uv-icon name="arrow-down" size="16" color="#748178" />
          </view>
        </picker>
      </view>
    </view>

    <view class="form-item">
      <view class="field-group">
        <text class="field-label">作业日期 <text class="field-required">*</text></text>
        <picker mode="date" :value="form.operatedDate" :start="selectedProduction?.startedOn" :end="today" @change="handleDateChange">
          <view class="select-shell">
            <text>{{ form.operatedDate }}</text>
            <uv-icon name="calendar" size="17" color="#748178" />
          </view>
        </picker>
      </view>
    </view>

    <view class="form-item">
      <view class="field-group">
        <text class="field-label">作业时间 <text class="field-required">*</text></text>
        <picker mode="time" :value="form.operatedTime" @change="handleTimeChange">
          <view class="select-shell">
            <text>{{ form.operatedTime }}</text>
            <uv-icon name="clock" size="17" color="#748178" />
          </view>
        </picker>
      </view>
    </view>

    <view class="form-item">
      <view class="field-group">
        <text class="field-label">操作人 <text class="field-required">*</text></text>
        <picker mode="selector" :range="operatorLabels" :value="operatorIndex" @change="handleOperatorChange">
          <view class="select-shell">
            <text>{{ operatorLabels[operatorIndex] }}</text>
            <uv-icon name="arrow-down" size="16" color="#748178" />
          </view>
        </picker>
      </view>
    </view>

    <view class="optional-section">
      <view
        class="optional-section__header"
        hover-class="optional-section__header--pressed"
        @tap="toggleOptionalSection"
      >
        <view class="optional-section__heading">
          <view class="optional-section__marker" />
          <text class="optional-section__title">备注</text>
        </view>
        <uv-icon :name="optionalExpanded ? 'arrow-up' : 'arrow-down'" size="16" color="#748178" />
      </view>

      <view v-if="optionalExpanded" class="optional-fields">
        <view class="field-group">
          <view class="textarea-shell">
            <textarea v-model="form.remark" maxlength="1000" auto-height placeholder="补充说明" placeholder-class="textarea-placeholder" />
          </view>
        </view>
      </view>
    </view>

    <uv-button
      type="primary"
      size="large"
      shape="square"
      :loading="submitting"
      :loading-text="loadingText"
      custom-style="height: 96rpx; margin-top: 40rpx; border-radius: 16rpx;"
      @click="handleSubmit"
    >
      {{ submitLabel }}
    </uv-button>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { FarmMember } from "../services/farm";
import type {
  FarmOperation,
  OperationInput,
  OperationType,
} from "../services/operation";
import type { Production, WorkMethod } from "../services/production";
import type { Plot, PlotType } from "../services/plot";
import { formatNumber } from "../utils/number";
import PfRowChevron from "./PfRowChevron.vue";

const workMethodValues: WorkMethod[] = ["MANUAL", "MECHANICAL"];
const workMethodLabels = ["人工", "机械"];

const props = withDefaults(
  defineProps<{
    productions: Production[];
    members: FarmMember[];
    operationTypes: OperationType[];
    currentUserId: number;
    plot?: Plot | null;
    plotSelectable?: boolean;
    selectedOperationTypeId?: number;
    selectedProductionId?: number | null;
    initialOperation?: FarmOperation | null;
    submitLabel?: string;
    loadingText?: string;
    submitting?: boolean;
  }>(),
  {
    initialOperation: null,
    selectedOperationTypeId: 0,
    selectedProductionId: null,
    plot: null,
    plotSelectable: false,
    submitLabel: "保存农事",
    loadingText: "保存中",
    submitting: false,
  },
);

const emit = defineEmits<{
  submit: [input: OperationInput];
  "select-plot": [];
  "select-operation-type": [];
  "select-production": [];
}>();

const today = formatDate(new Date());
const form = reactive({
  operationTypeId: 0,
  productionId: null as number | null,
  workMethod: "MANUAL" as WorkMethod,
  operatedDate: today,
  operatedTime: formatTime(new Date()),
  operatorId: 0,
  remark: "",
});
const selectedProduction = computed(
  () => props.productions.find((production) => production.id === form.productionId) || null,
);
const hasPlot = computed(() => Boolean(props.plot));
const selectedOperationType = computed(
  () =>
    props.operationTypes.find((operationType) => operationType.id === form.operationTypeId) ||
    (props.initialOperation?.operationType.id === form.operationTypeId
      ? props.initialOperation.operationType
      : null),
);
const workMethodIndex = computed(() => workMethodValues.indexOf(form.workMethod));
const operatorLabels = computed(() => props.members.map(displayMemberName));
const operatorIndex = computed(() => {
  const index = props.members.findIndex((member) => member.userId === form.operatorId);
  return index >= 0 ? index : 0;
});
const initialized = ref(false);
const optionalExpanded = ref(false);

watch(
  () =>
    [
      props.initialOperation,
      props.members,
      props.currentUserId,
    ] as const,
  ([operation, members, currentUserId]) => {
    if (operation) {
      const operatedAt = new Date(operation.operatedAt);
      form.operationTypeId = operation.operationType.id;
      form.productionId = operation.productionId;
      form.workMethod = operation.workMethod;
      form.operatedDate = formatDate(operatedAt);
      form.operatedTime = formatTime(operatedAt);
      form.operatorId = members.some((member) => member.userId === operation.operatorId)
        ? operation.operatorId
        : currentUserId;
      form.remark = operation.remark || "";
      optionalExpanded.value = Boolean(form.remark);
      initialized.value = true;
      return;
    }
    if (initialized.value || !members.length) return;
    form.operationTypeId = props.selectedOperationTypeId;
    form.productionId = props.selectedProductionId;
    form.workMethod = "MANUAL";
    form.operatedDate = today;
    form.operatedTime = formatTime(new Date());
    form.operatorId = members.some((member) => member.userId === currentUserId)
      ? currentUserId
      : members[0]?.userId || 0;
    form.remark = "";
    optionalExpanded.value = false;
    initialized.value = true;
  },
  { immediate: true },
);

watch(
  () => props.selectedOperationTypeId,
  (operationTypeId) => {
    if (operationTypeId) form.operationTypeId = operationTypeId;
  },
);

watch(
  () => props.selectedProductionId,
  (productionId) => {
    form.productionId = productionId;
    if (selectedProduction.value && form.operatedDate < selectedProduction.value.startedOn) {
      form.operatedDate = selectedProduction.value.startedOn;
    }
  },
);

function displayMemberName(member: FarmMember): string {
  return member.nickname?.trim() || "未设置昵称";
}

function formatDate(value: Date): string {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

function formatTime(value: Date): string {
  return `${String(value.getHours()).padStart(2, "0")}:${String(value.getMinutes()).padStart(2, "0")}`;
}

function handleWorkMethodChange(event: { detail: { value: number | string } }): void {
  form.workMethod = workMethodValues[Number(event.detail.value)] || "MANUAL";
}

function handleSelectProduction(): void {
  if (!hasPlot.value) {
    uni.showToast({ title: "请先选择地块", icon: "none" });
    return;
  }
  emit("select-production");
}

function handlePlotSelect(): void {
  if (props.plotSelectable) emit("select-plot");
}

function toggleOptionalSection(): void {
  optionalExpanded.value = !optionalExpanded.value;
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

function plotMeta(value: Plot): string {
  const type = value.type ? plotTypeLabels[value.type] : "未分类";
  if (value.areaValue === null || value.areaValue === undefined || !value.areaUnit) return type;
  const units: Record<string, string> = { MU: "亩", SQUARE_METER: "平方米", HECTARE: "公顷" };
  return `${type} · ${formatNumber(value.areaValue)}${units[value.areaUnit] || ""}`;
}

function productionLabel(production: Production): string {
  const variety = production.variety ? ` · ${production.variety}` : "";
  return `${production.speciesName}${variety} · ${production.startedOn}`;
}

function handleDateChange(event: { detail: { value: string } }): void {
  form.operatedDate = event.detail.value;
}

function handleTimeChange(event: { detail: { value: string } }): void {
  form.operatedTime = event.detail.value;
}

function handleOperatorChange(event: { detail: { value: number | string } }): void {
  form.operatorId = props.members[Number(event.detail.value)]?.userId || 0;
}

function handleSubmit(): void {
  if (!hasPlot.value) {
    uni.showToast({ title: "请选择地块", icon: "none" });
    return;
  }
  if (!form.operationTypeId) {
    uni.showToast({ title: "请选择农事类型", icon: "none" });
    return;
  }
  if (!form.operatorId) {
    uni.showToast({ title: "请选择操作人", icon: "none" });
    return;
  }
  if (selectedProduction.value && form.operatedDate < selectedProduction.value.startedOn) {
    uni.showToast({ title: "作业日期不能早于开始日期", icon: "none" });
    return;
  }
  const operatedAt = new Date(`${form.operatedDate}T${form.operatedTime}:00`);
  if (Number.isNaN(operatedAt.getTime()) || operatedAt.getTime() > Date.now()) {
    uni.showToast({ title: "作业时间不能晚于当前时间", icon: "none" });
    return;
  }
  emit("submit", {
    productionId: form.productionId,
    operationTypeId: form.operationTypeId,
    workMethod: form.workMethod,
    operatedAt: operatedAt.toISOString(),
    operatorId: form.operatorId,
    remark: form.remark.trim() || null,
  });
}
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.operation-form {
  padding-top: $pf-space-4;
  padding-bottom: $pf-space-8;
}

.form-item + .form-item {
  margin-top: $pf-space-4;
}

.field-label {
  display: block;
  margin-bottom: 12rpx;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.field-required {
  margin-left: 6rpx;
  color: $pf-color-danger;
}

.field-optional {
  margin-left: 8rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  font-weight: $pf-font-weight-medium;
}

.select-shell,
.textarea-shell {
  display: flex;
  box-sizing: border-box;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.select-shell {
  min-height: 96rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 $pf-space-2 0 $pf-space-3;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
}

.select-placeholder,
.textarea-placeholder {
  color: $pf-color-text-muted;
}

.select-shell--disabled {
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
}

.select-shell:active {
  background: $pf-color-surface-muted;
}

.plot-select__copy,
.plot-select__name,
.plot-select__meta {
  display: block;
}

.plot-select__name {
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.plot-select__meta {
  margin-top: 5rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.textarea-shell {
  min-height: 176rpx;
  align-items: flex-start;
  padding: $pf-space-3;
}

.textarea-shell textarea {
  width: 100%;
  min-height: 128rpx;
  color: $pf-color-text;
  font-size: $pf-font-size-body;
  line-height: 1.5;
}

.optional-section {
  margin-top: $pf-space-6;
}

.optional-section__header,
.optional-section__heading {
  display: flex;
  align-items: center;
}

.optional-section__header {
  min-height: 64rpx;
  justify-content: space-between;
  padding: 0 4rpx;
}

.optional-section__header--pressed {
  opacity: 0.68;
}

.optional-section__heading {
  gap: 12rpx;
}

.optional-section__marker {
  width: 6rpx;
  height: 26rpx;
  border-radius: $pf-radius-pill;
  background: $pf-color-primary;
}

.optional-section__title {
  color: $pf-color-text;
  font-size: $pf-font-size-section;
  font-weight: $pf-font-weight-semibold;
}

.optional-fields {
  margin-top: $pf-space-2;
}
</style>
