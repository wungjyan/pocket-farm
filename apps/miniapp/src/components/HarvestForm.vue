<template>
  <view class="harvest-form pf-page-content">
    <view class="required-fields">
      <view class="form-item">
        <view class="field-group">
          <text class="field-label">种养 <text class="field-required">*</text></text>
          <view
            class="select-shell"
            :class="{ 'select-shell--disabled': !productionSelectable }"
            @tap="handleProductionSelect"
          >
            <text :class="{ 'select-placeholder': !production }">{{ productionName }}</text>
            <uv-icon v-if="productionSelectable" name="arrow-right" size="16" color="#929A93" />
          </view>
        </view>
      </view>

      <view class="form-item">
        <view class="field-group">
          <text class="field-label">{{ quantityFieldLabel }} <text class="field-required">*</text></text>
          <view class="quantity-shell">
            <uv-input
              v-model="form.quantity"
              type="digit"
              maxlength="15"
              clearable
              border="none"
              :placeholder="quantityPlaceholder"
              placeholder-style="color: #929A93;"
              color="#202821"
            />
            <view class="unit-label" :class="{ 'unit-label--empty': !quantityUnit }">
              {{ selectedUnitLabel }}
            </view>
          </view>
        </view>
      </view>

      <view class="form-item">
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

      <view class="form-item">
        <view class="field-group">
          <text class="field-label">{{ actionLabel }}日期 <text class="field-required">*</text></text>
          <picker mode="date" :value="form.harvestedDate" :start="production?.startedOn" :end="today" @change="handleDateChange">
            <view class="select-shell">
              <text>{{ form.harvestedDate }}</text>
              <uv-icon name="calendar" size="17" color="#929A93" />
            </view>
          </picker>
        </view>
      </view>

      <view class="form-item">
        <view class="field-group">
          <text class="field-label">{{ actionLabel }}时间 <text class="field-required">*</text></text>
          <picker mode="time" :value="form.harvestedTime" @change="handleTimeChange">
            <view class="select-shell">
              <text>{{ form.harvestedTime }}</text>
              <uv-icon name="clock" size="17" color="#929A93" />
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
              <uv-icon name="arrow-down" size="16" color="#929A93" />
            </view>
          </picker>
        </view>
      </view>
    </view>

    <view class="optional-section">
      <view class="optional-section__trigger pf-tappable" @tap="toggleOptionalSection">
        <text class="optional-section__title">选填信息</text>
        <uv-icon :name="optionalExpanded ? 'arrow-up' : 'arrow-down'" size="16" color="#7F8B82" />
      </view>

      <view v-if="optionalExpanded" class="optional-fields">
        <view class="form-item">
          <view class="field-group">
            <text class="field-label">产品名称</text>
            <view class="input-shell">
              <uv-input v-model="form.productName" maxlength="100" border="none" placeholder="默认使用种养名称" placeholder-style="color: #929A93;" color="#202821" />
            </view>
          </view>
        </view>

        <view class="form-item">
          <view class="field-group">
            <text class="field-label">等级</text>
            <view class="input-shell">
              <uv-input v-model="form.grade" maxlength="100" border="none" placeholder="如一级、二级" placeholder-style="color: #929A93;" color="#202821" />
            </view>
          </view>
        </view>

        <view class="form-item">
          <view class="field-group">
            <text class="field-label">备注</text>
            <view class="textarea-shell">
              <textarea v-model="form.remark" maxlength="1000" auto-height placeholder="补充说明" placeholder-class="textarea-placeholder" />
            </view>
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
import type { HarvestInput, HarvestRecord, QuantityUnit } from "../services/harvest";
import type { Production, WorkMethod } from "../services/production";
import { formatNumber } from "../utils/number";

const unitLabels: Record<QuantityUnit, string> = {
  KG: "公斤",
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只/个",
  PLANT: "株",
  TAIL: "尾",
};
const integerUnits = new Set<QuantityUnit>(["HEAD", "FEATHER", "PIECE", "PLANT", "TAIL"]);
const workMethodValues: WorkMethod[] = ["MANUAL", "MECHANICAL"];
const workMethodLabels = ["人工", "机械"];

const props = withDefaults(
  defineProps<{
    production?: Production | null;
    productionSelectable?: boolean;
    members: FarmMember[];
    currentUserId: number;
    initialHarvest?: HarvestRecord | null;
    submitLabel?: string;
    loadingText?: string;
    submitting?: boolean;
  }>(),
  {
    production: null,
    productionSelectable: true,
    initialHarvest: null,
    submitLabel: "保存记录",
    loadingText: "保存中",
    submitting: false,
  },
);

const emit = defineEmits<{
  submit: [input: HarvestInput];
  "select-production": [];
}>();
const today = formatDate(new Date());
const initialized = ref(false);
const optionalExpanded = ref(false);
const form = reactive({
  quantity: "",
  workMethod: "MANUAL" as WorkMethod,
  harvestedDate: today,
  harvestedTime: formatTime(new Date()),
  operatorId: 0,
  productName: "",
  grade: "",
  remark: "",
});
const actionLabel = computed(() => {
  if (props.production?.industry === "LIVESTOCK") return "出栏";
  if (props.production?.industry === "FISHERY") return "捕捞";
  return props.production ? "采收" : "收获";
});
const quantityFieldLabel = computed(() => {
  if (props.production?.industry === "AGRICULTURE") return "采收重量";
  if (props.production?.industry === "FISHERY") return "捕捞重量";
  if (props.production?.industry === "FORESTRY") return "采收数量";
  if (props.production?.industry === "LIVESTOCK") return "出栏数量";
  return "收获数量";
});
const quantityUnit = computed<QuantityUnit | null>(() => {
  if (props.initialHarvest) return props.initialHarvest.unit;
  if (!props.production) return null;
  if (["AGRICULTURE", "FISHERY"].includes(props.production.industry)) return "KG";
  return props.production.individualUnit;
});
const selectedUnitLabel = computed(() => quantityUnit.value ? unitLabels[quantityUnit.value] : "待确定");
const quantityPlaceholder = computed(() => quantityUnit.value === "KG" ? "填写重量" : "填写数量");
const productionName = computed(() => {
  if (!props.production) return "请选择具体种养";
  return `${props.production.speciesName}${props.production.variety ? ` · ${props.production.variety}` : ""}`;
});
const workMethodIndex = computed(() => Math.max(0, workMethodValues.indexOf(form.workMethod)));
const operatorLabels = computed(() => props.members.map(displayMemberName));
const operatorIndex = computed(() => {
  const index = props.members.findIndex((member) => member.userId === form.operatorId);
  return index >= 0 ? index : 0;
});

watch(
  () => [props.initialHarvest, props.members, props.currentUserId] as const,
  ([harvest, members, currentUserId]) => {
    if (harvest) {
      const harvestedAt = new Date(harvest.harvestedAt);
      form.quantity = formatNumber(harvest.quantity);
      form.workMethod = harvest.workMethod;
      form.harvestedDate = formatDate(harvestedAt);
      form.harvestedTime = formatTime(harvestedAt);
      form.operatorId = members.some((member) => member.userId === harvest.operatorId)
        ? harvest.operatorId
        : currentUserId;
      form.productName = harvest.productName || "";
      form.grade = harvest.grade || "";
      form.remark = harvest.remark || "";
      initialized.value = true;
      return;
    }
    if (initialized.value || !members.length) return;
    form.operatorId = members.some((member) => member.userId === currentUserId)
      ? currentUserId
      : members[0]?.userId || 0;
    form.productName = props.production?.speciesName || "";
    initialized.value = true;
  },
  { immediate: true },
);

watch(
  () => props.production,
  (production, previousProduction) => {
    if (!production) return;
    if (!form.productName.trim() || form.productName === previousProduction?.speciesName) {
      form.productName = production.speciesName;
    }
    if (form.harvestedDate < production.startedOn) form.harvestedDate = production.startedOn;
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

function handleProductionSelect(): void {
  if (props.productionSelectable) emit("select-production");
}

function toggleOptionalSection(): void {
  optionalExpanded.value = !optionalExpanded.value;
}

function handleDateChange(event: { detail: { value: string } }): void {
  form.harvestedDate = event.detail.value;
}

function handleTimeChange(event: { detail: { value: string } }): void {
  form.harvestedTime = event.detail.value;
}

function handleOperatorChange(event: { detail: { value: number | string } }): void {
  form.operatorId = props.members[Number(event.detail.value)]?.userId || 0;
}

function handleSubmit(): void {
  if (!props.production) {
    uni.showToast({ title: "请选择种养", icon: "none" });
    return;
  }
  const quantityText = form.quantity.trim();
  if (!quantityText || !/^\d+(?:\.\d{1,4})?$/.test(quantityText) || Number(quantityText) <= 0) {
    uni.showToast({ title: "请填写正确的数量，最多 4 位小数", icon: "none" });
    return;
  }
  if (!quantityUnit.value) {
    uni.showToast({ title: "请先选择种养", icon: "none" });
    return;
  }
  if (integerUnits.has(quantityUnit.value) && !/^\d+$/.test(quantityText)) {
    uni.showToast({ title: `${selectedUnitLabel.value}数量必须为整数`, icon: "none" });
    return;
  }
  if (!form.operatorId) {
    uni.showToast({ title: "请选择操作人", icon: "none" });
    return;
  }
  if (form.harvestedDate < props.production.startedOn) {
    uni.showToast({ title: `${actionLabel.value}日期不能早于开始日期`, icon: "none" });
    return;
  }
  const harvestedAt = new Date(`${form.harvestedDate}T${form.harvestedTime}:00`);
  if (Number.isNaN(harvestedAt.getTime()) || harvestedAt.getTime() > Date.now()) {
    uni.showToast({ title: `${actionLabel.value}时间不能晚于当前时间`, icon: "none" });
    return;
  }
  emit("submit", {
    quantity: Number(quantityText),
    workMethod: form.workMethod,
    harvestedAt: harvestedAt.toISOString(),
    operatorId: form.operatorId,
    productName: form.productName.trim() || null,
    grade: form.grade.trim() || null,
    remark: form.remark.trim() || null,
  });
}
</script>

<style lang="scss" scoped>
@import "../styles/design-tokens.scss";

.harvest-form { padding-top: 28rpx; padding-bottom: $pf-space-page-bottom; }
.form-item + .form-item { margin-top: $pf-space-5; }
.field-label { display: block; margin-bottom: 14rpx; color: $pf-color-text; font-size: 27rpx; font-weight: 600; }
.field-required { margin-left: 6rpx; color: $pf-color-danger; }
.quantity-shell, .input-shell, .select-shell, .textarea-shell { display: flex; box-sizing: border-box; border: 1rpx solid $pf-color-border; border-radius: $pf-radius-control; background: $pf-color-surface; }
.quantity-shell, .input-shell, .select-shell { min-height: 88rpx; align-items: center; }
.quantity-shell, .input-shell { padding: 0 20rpx; }
.quantity-shell :deep(.uv-input), .input-shell :deep(.uv-input) { flex: 1; }
.unit-label { min-width: 92rpx; box-sizing: border-box; padding-left: 18rpx; border-left: 1rpx solid $pf-color-divider; color: $pf-color-text-secondary; font-size: 24rpx; text-align: right; }
.unit-label--empty { color: $pf-color-text-muted; }
.select-shell { justify-content: space-between; padding: 0 20rpx; color: $pf-color-text; font-size: 25rpx; }
.select-shell--disabled { background: $pf-color-surface-muted; color: $pf-color-text-secondary; }
.select-placeholder, .textarea-placeholder { color: $pf-color-text-muted; }
.textarea-shell { min-height: 160rpx; align-items: flex-start; padding: 18rpx 20rpx; }
.textarea-shell textarea { width: 100%; min-height: 110rpx; color: $pf-color-text; font-size: 25rpx; line-height: 1.5; }
.optional-section { margin-top: $pf-space-6; }
.optional-section__trigger { display: flex; min-height: 56rpx; align-items: center; justify-content: space-between; }
.optional-section__title { color: $pf-color-text-secondary; font-size: 26rpx; font-weight: 600; }
.optional-fields { margin-top: $pf-space-4; }
</style>
