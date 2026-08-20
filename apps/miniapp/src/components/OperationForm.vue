<template>
  <view class="form-card pf-card">
    <view class="field-group">
      <text class="field-label">农事类型 <text class="field-required">*</text></text>
      <view class="select-shell" @click="emit('select-operation-type')">
        <text :class="{ 'select-placeholder': !selectedOperationType }">
          {{ selectedOperationType?.name || "请选择农事类型" }}
        </text>
        <uv-icon name="arrow-right" size="16" color="#929A93" />
      </view>
    </view>

    <view class="field-group">
      <text class="field-label">关联种养 <text class="field-optional">选填</text></text>
      <view class="select-shell" :class="{ 'select-shell--disabled': !hasPlot }" @click="handleSelectProduction">
        <text>{{ selectedProduction ? productionLabel(selectedProduction) : hasPlot ? "整个地块" : "请先选择地块" }}</text>
        <uv-icon name="arrow-right" size="16" color="#929A93" />
      </view>
      <text class="field-help">默认记录整个地块；需要追溯到具体批次时再关联。</text>
    </view>

    <view class="field-group">
      <text class="field-label">作业方式 <text class="field-required">*</text></text>
      <picker mode="selector" :range="workMethodLabels" :value="workMethodIndex" @change="handleWorkMethodChange">
        <view class="select-shell">
          <text>{{ workMethodLabels[workMethodIndex] }}</text>
          <uv-icon name="arrow-down" size="16" color="#929A93" />
        </view>
      </picker>
    </view>

    <view class="field-group">
      <text class="field-label">作业日期 <text class="field-required">*</text></text>
      <picker mode="date" :value="form.operatedDate" :start="selectedProduction?.startedOn" :end="today" @change="handleDateChange">
        <view class="select-shell">
          <text>{{ form.operatedDate }}</text>
          <uv-icon name="calendar" size="17" color="#929A93" />
        </view>
      </picker>
    </view>

    <view class="field-group">
      <text class="field-label">作业时间 <text class="field-required">*</text></text>
      <picker mode="time" :value="form.operatedTime" @change="handleTimeChange">
        <view class="select-shell">
          <text>{{ form.operatedTime }}</text>
          <uv-icon name="clock" size="17" color="#929A93" />
        </view>
      </picker>
    </view>

    <view class="field-group">
      <text class="field-label">操作人 <text class="field-required">*</text></text>
      <picker mode="selector" :range="operatorLabels" :value="operatorIndex" @change="handleOperatorChange">
        <view class="select-shell">
          <text>{{ operatorLabels[operatorIndex] }}</text>
          <uv-icon name="arrow-down" size="16" color="#929A93" />
        </view>
      </picker>
    </view>

    <view class="field-group">
      <text class="field-label">备注 <text class="field-optional">选填</text></text>
      <view class="textarea-shell">
        <textarea v-model="form.remark" maxlength="1000" auto-height placeholder="补充说明" placeholder-class="textarea-placeholder" />
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
import { computed, reactive, ref, watch } from "vue";
import type { FarmMember } from "../services/farm";
import type {
  FarmOperation,
  OperationInput,
  OperationType,
} from "../services/operation";
import type { Production, WorkMethod } from "../services/production";

const workMethodValues: WorkMethod[] = ["MANUAL", "MECHANICAL"];
const workMethodLabels = ["人工", "机械"];

const props = withDefaults(
  defineProps<{
    productions: Production[];
    members: FarmMember[];
    operationTypes: OperationType[];
    currentUserId: number;
    hasPlot?: boolean;
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
    hasPlot: false,
    submitLabel: "保存农事",
    loadingText: "保存中",
    submitting: false,
  },
);

const emit = defineEmits<{
  submit: [input: OperationInput];
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
  if (!props.hasPlot) {
    uni.showToast({ title: "请先选择地块", icon: "none" });
    return;
  }
  emit("select-production");
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
  if (!props.hasPlot) {
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

.field-required {
  margin-left: 6rpx;
  color: #c96a45;
}

.field-optional {
  margin-left: 8rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 400;
}

.field-help {
  display: block;
  margin-top: 10rpx;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  line-height: 1.45;
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
  min-height: 88rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 20rpx;
  color: $pf-color-text;
  font-size: 25rpx;
}

.select-placeholder,
.textarea-placeholder {
  color: $pf-color-text-muted;
}

.select-shell--disabled {
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
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
</style>
