<template>
  <view class="pf-page records-page">
    <view class="pf-page-content">
      <view class="records-tabs">
        <view
          v-for="tab in tabs"
          :key="tab.value"
          class="records-tab pf-tappable"
          :class="{ 'records-tab--active': activeTab === tab.value }"
          @tap="switchTab(tab.value)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>

      <template v-if="activeTab === 'PRODUCTION'">
        <view class="filter-toolbar">
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="industryOptions.map((item) => item.label)"
            :value="industryIndex"
            @change="handleIndustryChange"
          >
            <view class="filter-picker pf-tappable" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedIndustryLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#7F8B82" />
            </view>
          </picker>
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="varietyPickerOptions"
            :value="varietyIndex"
            @change="handleVarietyChange"
          >
            <view class="filter-picker pf-tappable" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedVarietyLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#7F8B82" />
            </view>
          </picker>
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="statusOptions.map((item) => item.label)"
            :value="statusIndex"
            @change="handleStatusChange"
          >
            <view class="filter-picker pf-tappable" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedStatusLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#7F8B82" />
            </view>
          </picker>
        </view>

        <view v-if="loading" class="state-card pf-card">
          <uv-loading-icon mode="circle" color="#286B46" />
          <text>正在加载种养记录</text>
        </view>
        <view v-else-if="productions.length" class="production-list">
          <view
            v-for="item in productions"
            :key="item.id"
            class="production-row pf-card pf-tappable"
            :class="{ 'production-row--ended': item.status === 'ENDED' }"
            @tap="openProduction(item.id)"
          >
            <view class="production-copy">
              <view class="production-title">
                <text class="production-name">{{ item.speciesName }}</text>
                <text v-if="item.variety" class="variety-tag">{{ item.variety }}</text>
                <text v-if="item.status === 'ENDED'" class="ended-tag">已结束</text>
              </view>
              <text class="production-field">地块：{{ item.plotName }}</text>
              <text class="production-field">开始日期：{{ operationDateLabel(item.startedOn) }}</text>
              <text
                v-if="item.status === 'ACTIVE' && item.initialQuantity !== null && item.initialQuantity !== undefined"
                class="production-field"
              >
                初始数量：{{ formatNumber(item.initialQuantity) }}{{ individualUnitLabels[item.individualUnit] }}
              </text>
              <text v-else-if="item.endedOn" class="production-field">
                结束日期：{{ operationDateLabel(item.endedOn) }}
              </text>
            </view>
            <PfRowChevron />
          </view>
        </view>
        <PfEmptyState v-else />
      </template>

      <template v-else-if="activeTab === 'OPERATION'">
        <view class="filter-toolbar">
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="operationTypePickerOptions"
            :value="operationTypeIndex"
            @change="handleOperationTypeChange"
          >
            <view class="filter-picker pf-tappable" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedOperationTypeLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#7F8B82" />
            </view>
          </picker>
        </view>

        <view v-if="operationsLoading" class="state-card pf-card">
          <uv-loading-icon mode="circle" color="#286B46" />
          <text>正在加载农事记录</text>
        </view>
        <view v-else-if="operations.length" class="operation-list">
          <view v-for="item in operations" :key="item.id" class="operation-row pf-card">
            <view class="operation-copy">
              <text class="operation-name">{{ item.operationTypeName }}</text>
              <text class="operation-field">地块：{{ operationPlotLabel(item) }}</text>
              <text class="operation-field">操作日期：{{ operationDateLabel(item.operatedAt) }}</text>
              <text v-if="item.speciesName" class="operation-field">品种：{{ item.speciesName }}</text>
            </view>
          </view>
        </view>
        <PfEmptyState v-else />
      </template>

      <view v-else class="placeholder-state pf-card">
        <PfBusinessIcon name="clock-3" size="empty" />
        <text class="placeholder-state__title">收获记录待上线</text>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfEmptyState from "../../components/PfEmptyState.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import {
  getFarmOperations,
  getOperationFilterOptions,
  type FarmOperationSummary,
  type OperationTypeOption,
} from "../../services/operation";
import {
  getFarmProductions,
  getProductionFilterOptions,
  type FarmProduction,
  type ProductionSpeciesOption,
} from "../../services/production";
import type { IndividualUnit, Industry } from "../../services/species";
import type { ProductionStatus } from "../../services/production";
import { formatNumber } from "../../utils/number";

type RecordsTab = "PRODUCTION" | "OPERATION" | "HARVEST";

const tabs: { value: RecordsTab; label: string }[] = [
  { value: "PRODUCTION", label: "种养" },
  { value: "OPERATION", label: "农事" },
  { value: "HARVEST", label: "收获" },
];

const industryOptions: { value: Industry; label: string }[] = [
  { value: "AGRICULTURE", label: "农业" },
  { value: "FORESTRY", label: "林业" },
  { value: "LIVESTOCK", label: "牧业" },
  { value: "FISHERY", label: "渔业" },
];

const statusOptions: { value: ProductionStatus | ""; label: string }[] = [
  { value: "", label: "全部状态" },
  { value: "ACTIVE", label: "进行中" },
  { value: "ENDED", label: "已结束" },
];

const individualUnitLabels: Record<IndividualUnit, string> = {
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只",
  PLANT: "株",
  TAIL: "尾",
};

const farmId = ref(0);
const activeTab = ref<RecordsTab>("PRODUCTION");
const industryValue = ref<Industry>("AGRICULTURE");
const statusValue = ref<ProductionStatus | "">("ACTIVE");
const varietyOptions = ref<ProductionSpeciesOption[]>([]);
const varietyValue = ref(0);
const operations = ref<FarmOperationSummary[]>([]);
const operationTypeOptions = ref<OperationTypeOption[]>([]);
const operationTypeValue = ref(0);
const operationsLoading = ref(false);
const productions = ref<FarmProduction[]>([]);
const loading = ref(false);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm } = useFarmContext();

const ALL_VARIETY_LABEL = "全部品种";

const industryIndex = computed(() =>
  Math.max(0, industryOptions.findIndex((item) => item.value === industryValue.value)),
);
const statusIndex = computed(() =>
  Math.max(0, statusOptions.findIndex((item) => item.value === statusValue.value)),
);
const selectedIndustryLabel = computed(() => industryOptions[industryIndex.value].label);
const selectedStatusLabel = computed(() => statusOptions[statusIndex.value].label);
const varietyPickerOptions = computed(() => [
  ALL_VARIETY_LABEL,
  ...varietyOptions.value.map((item) => item.name),
]);
const varietyIndex = computed(() => {
  if (!varietyValue.value) return 0;
  const index = varietyOptions.value.findIndex((item) => item.id === varietyValue.value);
  return index >= 0 ? index + 1 : 0;
});
const selectedVarietyLabel = computed(
  () => varietyOptions.value.find((item) => item.id === varietyValue.value)?.name || ALL_VARIETY_LABEL,
);

const ALL_TYPE_LABEL = "全部类型";

const operationTypePickerOptions = computed(() => [
  ALL_TYPE_LABEL,
  ...operationTypeOptions.value.map((item) => item.name),
]);
const operationTypeIndex = computed(() => {
  if (!operationTypeValue.value) return 0;
  const index = operationTypeOptions.value.findIndex((item) => item.id === operationTypeValue.value);
  return index >= 0 ? index + 1 : 0;
});
const selectedOperationTypeLabel = computed(
  () =>
    operationTypeOptions.value.find((item) => item.id === operationTypeValue.value)?.name ||
    ALL_TYPE_LABEL,
);

function operationDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}.${month}.${day}`;
}

function operationPlotLabel(item: FarmOperationSummary): string {
  if (
    item.plotAreaValue === null ||
    item.plotAreaValue === undefined ||
    !item.plotAreaUnit
  ) {
    return item.plotName;
  }
  const units: Record<string, string> = { MU: "亩", SQUARE_METER: "平方米", HECTARE: "公顷" };
  return `${item.plotName}（${formatNumber(item.plotAreaValue)}${units[item.plotAreaUnit] || ""}）`;
}

function switchTab(tab: RecordsTab): void {
  if (activeTab.value === tab) return;
  activeTab.value = tab;
  if (tab === "OPERATION") {
    loadOperationTypeOptions();
    loadOperations();
  }
}

function handleIndustryChange(event: { detail: { value: number | string } }): void {
  const selected = industryOptions[Number(event.detail.value)];
  if (!selected || selected.value === industryValue.value) return;
  industryValue.value = selected.value;
  varietyValue.value = 0;
  loadVarietyOptions();
  loadProductions();
}

function handleStatusChange(event: { detail: { value: number | string } }): void {
  const selected = statusOptions[Number(event.detail.value)];
  if (!selected || selected.value === statusValue.value) return;
  statusValue.value = selected.value;
  loadProductions();
}

function handleVarietyChange(event: { detail: { value: number | string } }): void {
  const index = Number(event.detail.value);
  const selected = varietyOptions.value[index - 1];
  const targetId = index > 0 && selected ? selected.id : 0;
  if (targetId === varietyValue.value) return;
  varietyValue.value = targetId;
  loadProductions();
}

function handleOperationTypeChange(event: { detail: { value: number | string } }): void {
  const index = Number(event.detail.value);
  const selected = operationTypeOptions.value[index - 1];
  const targetId = index > 0 && selected ? selected.id : 0;
  if (targetId === operationTypeValue.value) return;
  operationTypeValue.value = targetId;
  loadOperations();
}


function openProduction(productionId: number): void {
  uni.navigateTo({ url: `/pages/productions/detail?productionId=${productionId}` });
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadProductions(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    productions.value = [];
    return;
  }
  loading.value = true;
  try {
    const page = await getFarmProductions(targetFarmId, {
      industry: industryValue.value || undefined,
      status: statusValue.value || undefined,
      speciesId: varietyValue.value || undefined,
      page: 1,
      pageSize: 100,
    });
    if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
    productions.value = page.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "种养记录加载失败",
    });
  } finally {
    loading.value = false;
  }
}

async function loadVarietyOptions(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    varietyOptions.value = [];
    return;
  }
  try {
    const options = await getProductionFilterOptions(targetFarmId, industryValue.value || undefined);
    if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
    varietyOptions.value = options.species;
    if (varietyValue.value && !options.species.some((item) => item.id === varietyValue.value)) {
      varietyValue.value = 0;
      await loadProductions();
    }
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "筛选选项加载失败",
    });
  }
}

async function loadOperations(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    operations.value = [];
    return;
  }
  operationsLoading.value = true;
  try {
    const page = await getFarmOperations(targetFarmId, {
      operationTypeId: operationTypeValue.value || undefined,
      page: 1,
      pageSize: 100,
    });
    if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
    operations.value = page.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "农事记录加载失败",
    });
  } finally {
    operationsLoading.value = false;
  }
}

async function loadOperationTypeOptions(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    operationTypeOptions.value = [];
    return;
  }
  try {
    const options = await getOperationFilterOptions(targetFarmId);
    if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
    operationTypeOptions.value = options.types;
    if (
      operationTypeValue.value &&
      !options.types.some((item) => item.id === operationTypeValue.value)
    ) {
      operationTypeValue.value = 0;
      await loadOperations();
    }
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "筛选选项加载失败",
    });
  }
}

async function loadPageData(): Promise<void> {
  const currentFarmId = currentFarm.value?.id || 0;
  if (!currentFarmId) {
    farmId.value = 0;
    varietyValue.value = 0;
    varietyOptions.value = [];
    operationTypeValue.value = 0;
    operationTypeOptions.value = [];
    productions.value = [];
    operations.value = [];
    return;
  }
  if (currentFarmId !== farmId.value) {
    farmId.value = currentFarmId;
    varietyValue.value = 0;
    operationTypeValue.value = 0;
  }
  await Promise.all([
    loadVarietyOptions(),
    loadProductions(),
    loadOperationTypeOptions(),
    loadOperations(),
  ]);
}

onLoad((query) => {
  const parsedFarmId = Number(query?.farmId || 0);
  farmId.value = Number.isInteger(parsedFarmId) && parsedFarmId > 0 ? parsedFarmId : currentFarm.value?.id || 0;
});

onShow(() => loadPageData());
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.records-tabs {
  display: flex;
  padding: 4rpx 4rpx 20rpx;
}

.records-tab {
  position: relative;
  flex: 1;
  padding: 12rpx 4rpx;
  text-align: center;
  color: $pf-color-text-secondary;
  font-size: 30rpx;
  font-weight: 550;
}

.records-tab--active {
  color: $pf-color-primary;
  font-weight: 650;
}

.records-tab--active::after {
  content: "";
  position: absolute;
  right: 50%;
  bottom: 0;
  width: 40rpx;
  height: 6rpx;
  border-radius: 999rpx;
  background: $pf-color-primary;
  transform: translateX(50%);
}

.filter-toolbar {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  padding: 0 4rpx 10rpx;
}

.filter-picker-wrap {
  display: block;
  flex: 1;
  min-width: 0;
}

.filter-picker-wrap + .filter-picker-wrap {
  margin-left: 16rpx;
}

.filter-picker {
  display: inline-flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 16rpx;
  border-radius: $pf-radius-control;
}

.filter-picker--pressed {
  background: $pf-color-surface-muted;
}

.filter-picker__label {
  overflow: hidden;
  color: $pf-color-text-secondary;
  font-size: 25rpx;
  font-weight: 550;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-picker .uv-icon {
  margin-left: 8rpx;
  flex-shrink: 0;
}

.production-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.production-row {
  display: flex;
  align-items: center;
  padding: $pf-space-3;
}

.production-copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}

.production-title {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.production-name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.variety-tag,
.ended-tag {
  display: block;
  flex-shrink: 0;
  padding: 5rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  line-height: 1.25;
}

.variety-tag {
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
}

.ended-tag {
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
}

.production-field {
  display: block;
  margin-top: $pf-space-1;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-title + .production-field {
  margin-top: $pf-space-2;
}

.production-row--ended .production-name {
  color: $pf-color-text-secondary;
  font-weight: 600;
}

.operation-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.operation-row {
  padding: $pf-space-3;
}

.operation-copy {
  min-width: 0;
  flex: 1;
}

.operation-name {
  display: block;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-field {
  display: block;
  margin-top: $pf-space-1;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-name + .operation-field {
  margin-top: $pf-space-2;
}

.state-card {
  display: flex;
  min-height: 180rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}

.state-card text {
  margin-top: 14rpx;
}


</style>
