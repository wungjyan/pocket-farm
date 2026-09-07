<template>
  <view class="pf-page records-page">
    <view class="pf-page-content">
      <view class="records-sticky-header">
        <view class="records-tabs">
          <view
            v-for="tab in tabs"
            :key="tab.value"
            class="records-tab"
            :class="{ 'records-tab--active': activeTab === tab.value }"
            hover-class="records-tab--pressed"
            @tap="switchTab(tab.value)"
          >
            <text>{{ tab.label }}</text>
          </view>
        </view>
        <view v-if="activeTab === 'PRODUCTION'" class="filter-toolbar">
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="industryOptions.map((item) => item.label)"
            :value="industryIndex"
            @change="handleIndustryChange"
          >
            <view class="filter-picker" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedIndustryLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#748178" />
            </view>
          </picker>
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="varietyPickerOptions"
            :value="varietyIndex"
            @change="handleVarietyChange"
          >
            <view class="filter-picker" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedVarietyLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#748178" />
            </view>
          </picker>
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="statusOptions.map((item) => item.label)"
            :value="statusIndex"
            @change="handleStatusChange"
          >
            <view class="filter-picker" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedStatusLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#748178" />
            </view>
          </picker>
        </view>
        <view v-else-if="activeTab === 'OPERATION'" class="filter-toolbar filter-toolbar--single">
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="operationTypePickerOptions"
            :value="operationTypeIndex"
            @change="handleOperationTypeChange"
          >
            <view class="filter-picker" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedOperationTypeLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#748178" />
            </view>
          </picker>
        </view>
        <view v-else class="filter-toolbar">
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="industryOptions.map((item) => item.label)"
            :value="harvestIndustryIndex"
            @change="handleHarvestIndustryChange"
          >
            <view class="filter-picker" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedHarvestIndustryLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#748178" />
            </view>
          </picker>
          <picker
            class="filter-picker-wrap"
            mode="selector"
            :range="harvestSpeciesPickerOptions"
            :value="harvestSpeciesIndex"
            @change="handleHarvestSpeciesChange"
          >
            <view class="filter-picker" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedHarvestSpeciesLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#748178" />
            </view>
          </picker>
        </view>
      </view>

      <template v-if="activeTab === 'PRODUCTION'">
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
              <text class="production-field">地块：{{ plotLabel(item) }}</text>
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
          <uv-load-more v-if="productions.length && (productionHasMore || productionLoadingMore)" :status="productionLoadingMore ? 'loading' : 'nomore'" icon-color="#286B46" color="#7F8B82" />
        </view>
        <PfEmptyState v-else />
      </template>

      <template v-else-if="activeTab === 'OPERATION'">
        <view v-if="operationsLoading" class="state-card pf-card">
          <uv-loading-icon mode="circle" color="#286B46" />
          <text>正在加载农事记录</text>
        </view>
        <view v-else-if="operations.length" class="operation-list">
          <view
            v-for="item in operations"
            :key="item.id"
            class="operation-row pf-card pf-tappable"
            @tap="openOperation(item.id)"
          >
            <view class="operation-copy">
              <view class="operation-title-line">
                <text class="operation-name">{{ item.operationTypeName }}</text>
                <text v-if="item.productionStatus === 'ENDED'" class="operation-status">种养已结束</text>
              </view>
              <text class="operation-field">地块：{{ plotLabel(item) }}</text>
              <text class="operation-field">操作时间：{{ operationTimeLabel(item.operatedAt) }}</text>
              <text v-if="item.speciesName" class="operation-field">品种：{{ item.speciesName }}</text>
            </view>
            <PfRowChevron />
          </view>
          <uv-load-more v-if="operations.length && (operationHasMore || operationLoadingMore)" :status="operationLoadingMore ? 'loading' : 'nomore'" icon-color="#286B46" color="#7F8B82" />
        </view>
        <PfEmptyState v-else />
      </template>

      <template v-else>
        <view v-if="harvestsLoading" class="state-card pf-card">
          <uv-loading-icon mode="circle" color="#286B46" />
          <text>正在加载收获记录</text>
        </view>
        <view v-else-if="harvests.length" class="harvest-list">
          <view
            v-for="item in harvests"
            :key="item.id"
            class="harvest-row pf-card pf-tappable"
            @tap="openHarvest(item.id)"
          >
            <view class="harvest-copy">
              <view class="harvest-title-line">
                <text class="harvest-name">{{ item.productName || item.speciesName }}</text>
                <text v-if="item.productionStatus === 'ENDED'" class="harvest-status">种养已结束</text>
              </view>
              <text class="harvest-field">
                {{ harvestActionLabel(item.industry) }}：<text class="harvest-quantity">{{ formatNumber(item.quantity) }} {{ quantityUnitLabels[item.unit] }}</text>
              </text>
              <text class="harvest-field">地块：{{ plotLabel(item) }}</text>
              <text class="harvest-field">操作时间：{{ operationTimeLabel(item.harvestedAt) }}</text>
              <text class="harvest-field">操作人：{{ harvestOperatorLabel(item) }}</text>
            </view>
            <PfRowChevron />
          </view>
          <uv-load-more v-if="harvests.length && (harvestHasMore || harvestLoadingMore)" :status="harvestLoadingMore ? 'loading' : 'nomore'" icon-color="#286B46" color="#7F8B82" />
        </view>
        <PfEmptyState v-else />
      </template>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onReachBottom, onShow } from "@dcloudio/uni-app";
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
  getFarmHarvests,
  getHarvestFilterOptions,
  type FarmHarvestSummary,
  type HarvestSpeciesOption,
  type QuantityUnit,
} from "../../services/harvest";
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

const PAGE_SIZE = 20;

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

const quantityUnitLabels: Record<QuantityUnit, string> = {
  KG: "公斤",
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只/个",
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
const operationPage = ref(1);
const operationHasMore = ref(false);
const operationLoadingMore = ref(false);
const harvestIndustryValue = ref<Industry>("AGRICULTURE");
const harvestSpeciesOptions = ref<HarvestSpeciesOption[]>([]);
const harvestSpeciesValue = ref(0);
const harvests = ref<FarmHarvestSummary[]>([]);
const harvestsLoading = ref(false);
const harvestPage = ref(1);
const harvestHasMore = ref(false);
const harvestLoadingMore = ref(false);
const productions = ref<FarmProduction[]>([]);
const loading = ref(false);
const productionPage = ref(1);
const productionHasMore = ref(false);
const productionLoadingMore = ref(false);
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

const harvestIndustryIndex = computed(() =>
  Math.max(0, industryOptions.findIndex((item) => item.value === harvestIndustryValue.value)),
);
const selectedHarvestIndustryLabel = computed(
  () => industryOptions[harvestIndustryIndex.value].label,
);
const harvestSpeciesPickerOptions = computed(() => [
  ALL_VARIETY_LABEL,
  ...harvestSpeciesOptions.value.map((item) => item.name),
]);
const harvestSpeciesIndex = computed(() => {
  if (!harvestSpeciesValue.value) return 0;
  const index = harvestSpeciesOptions.value.findIndex((item) => item.id === harvestSpeciesValue.value);
  return index >= 0 ? index + 1 : 0;
});
const selectedHarvestSpeciesLabel = computed(
  () =>
    harvestSpeciesOptions.value.find((item) => item.id === harvestSpeciesValue.value)?.name ||
    ALL_VARIETY_LABEL,
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

function operationTimeLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${minute}`;
}

type PlotSummary = Pick<
  FarmOperationSummary,
  "plotName" | "plotAreaValue" | "plotAreaUnit"
>;

const plotAreaUnitLabels: Record<string, string> = {
  MU: "亩",
  SQUARE_METER: "平方米",
  HECTARE: "公顷",
};

function plotLabel(item: PlotSummary): string {
  if (
    item.plotAreaValue === null ||
    item.plotAreaValue === undefined ||
    !item.plotAreaUnit
  ) {
    return item.plotName;
  }
  return `${item.plotName}（${formatNumber(item.plotAreaValue)}${plotAreaUnitLabels[item.plotAreaUnit] || ""}）`;
}

function switchTab(tab: RecordsTab): void {
  if (activeTab.value === tab) return;
  activeTab.value = tab;
  if (tab === "OPERATION") {
    loadOperationTypeOptions();
    loadOperations();
  } else if (tab === "HARVEST") {
    loadHarvestSpeciesOptions();
    loadHarvests();
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

function handleHarvestIndustryChange(event: { detail: { value: number | string } }): void {
  const selected = industryOptions[Number(event.detail.value)];
  if (!selected || selected.value === harvestIndustryValue.value) return;
  harvestIndustryValue.value = selected.value;
  harvestSpeciesValue.value = 0;
  loadHarvestSpeciesOptions();
  loadHarvests();
}

function handleHarvestSpeciesChange(event: { detail: { value: number | string } }): void {
  const index = Number(event.detail.value);
  const selected = harvestSpeciesOptions.value[index - 1];
  const targetId = index > 0 && selected ? selected.id : 0;
  if (targetId === harvestSpeciesValue.value) return;
  harvestSpeciesValue.value = targetId;
  loadHarvests();
}


function openProduction(productionId: number): void {
  uni.navigateTo({ url: `/pages/productions/detail?productionId=${productionId}` });
}

function openOperation(operationId: number): void {
  uni.navigateTo({ url: `/pages/operations/detail?operationId=${operationId}` });
}

function openHarvest(harvestId: number): void {
  uni.navigateTo({ url: `/pages/harvests/detail?harvestId=${harvestId}` });
}

function harvestActionLabel(industry: Industry): string {
  if (industry === "LIVESTOCK") return "出栏";
  if (industry === "FISHERY") return "捕捞";
  return "采收";
}

function harvestOperatorLabel(item: FarmHarvestSummary): string {
  const operatorName = item.operatorName?.trim() || "未设置昵称";
  if (item.createdBy === item.operatorId) return operatorName;
  return `${operatorName} · 记录人：${item.creatorName?.trim() || "未设置昵称"}`;
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function fetchProductionPage(targetFarmId: number, page: number): Promise<void> {
  const result = await getFarmProductions(targetFarmId, {
    industry: industryValue.value || undefined,
    status: statusValue.value || undefined,
    speciesId: varietyValue.value || undefined,
    page,
    pageSize: PAGE_SIZE,
  });
  if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
  productions.value = page === 1 ? result.items : [...productions.value, ...result.items];
  productionPage.value = page;
  productionHasMore.value = productions.value.length < result.total;
}

async function loadProductions(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    productions.value = [];
    productionHasMore.value = false;
    return;
  }
  loading.value = true;
  try {
    await fetchProductionPage(targetFarmId, 1);
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

async function loadMoreProductions(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId || loading.value || productionLoadingMore.value || !productionHasMore.value) return;
  productionLoadingMore.value = true;
  try {
    await fetchProductionPage(targetFarmId, productionPage.value + 1);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "更多记录加载失败",
    });
  } finally {
    productionLoadingMore.value = false;
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

async function fetchOperationPage(targetFarmId: number, page: number): Promise<void> {
  const result = await getFarmOperations(targetFarmId, {
    operationTypeId: operationTypeValue.value || undefined,
    page,
    pageSize: PAGE_SIZE,
  });
  if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
  operations.value = page === 1 ? result.items : [...operations.value, ...result.items];
  operationPage.value = page;
  operationHasMore.value = operations.value.length < result.total;
}

async function loadOperations(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    operations.value = [];
    operationHasMore.value = false;
    return;
  }
  operationsLoading.value = true;
  try {
    await fetchOperationPage(targetFarmId, 1);
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

async function loadMoreOperations(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId || operationsLoading.value || operationLoadingMore.value || !operationHasMore.value) return;
  operationLoadingMore.value = true;
  try {
    await fetchOperationPage(targetFarmId, operationPage.value + 1);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "更多记录加载失败",
    });
  } finally {
    operationLoadingMore.value = false;
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

async function fetchHarvestPage(targetFarmId: number, page: number): Promise<void> {
  const result = await getFarmHarvests(targetFarmId, {
    industry: harvestIndustryValue.value,
    speciesId: harvestSpeciesValue.value || undefined,
    page,
    pageSize: PAGE_SIZE,
  });
  if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
  harvests.value = page === 1 ? result.items : [...harvests.value, ...result.items];
  harvestPage.value = page;
  harvestHasMore.value = harvests.value.length < result.total;
}

async function loadHarvests(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    harvests.value = [];
    harvestHasMore.value = false;
    return;
  }
  harvestsLoading.value = true;
  try {
    await fetchHarvestPage(targetFarmId, 1);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "收获记录加载失败",
    });
  } finally {
    harvestsLoading.value = false;
  }
}

async function loadMoreHarvests(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId || harvestsLoading.value || harvestLoadingMore.value || !harvestHasMore.value) return;
  harvestLoadingMore.value = true;
  try {
    await fetchHarvestPage(targetFarmId, harvestPage.value + 1);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "更多记录加载失败",
    });
  } finally {
    harvestLoadingMore.value = false;
  }
}

async function loadHarvestSpeciesOptions(): Promise<void> {
  const targetFarmId = farmId.value;
  if (!targetFarmId) {
    harvestSpeciesOptions.value = [];
    return;
  }
  try {
    const options = await getHarvestFilterOptions(targetFarmId, harvestIndustryValue.value);
    if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
    harvestSpeciesOptions.value = options.species;
    if (
      harvestSpeciesValue.value &&
      !options.species.some((item) => item.id === harvestSpeciesValue.value)
    ) {
      harvestSpeciesValue.value = 0;
      await loadHarvests();
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
    harvestSpeciesValue.value = 0;
    harvestSpeciesOptions.value = [];
    harvests.value = [];
    return;
  }
  if (currentFarmId !== farmId.value) {
    farmId.value = currentFarmId;
    varietyValue.value = 0;
    operationTypeValue.value = 0;
    harvestSpeciesValue.value = 0;
  }
  await Promise.all([
    loadVarietyOptions(),
    loadProductions(),
    loadOperationTypeOptions(),
    loadOperations(),
    loadHarvestSpeciesOptions(),
    loadHarvests(),
  ]);
}

onLoad((query) => {
  const parsedFarmId = Number(query?.farmId || 0);
  farmId.value = Number.isInteger(parsedFarmId) && parsedFarmId > 0 ? parsedFarmId : currentFarm.value?.id || 0;
});

onShow(() => loadPageData());

onReachBottom(() => {
  if (activeTab.value === "PRODUCTION") {
    void loadMoreProductions();
  } else if (activeTab.value === "OPERATION") {
    void loadMoreOperations();
  } else {
    void loadMoreHarvests();
  }
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.records-tabs {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: stretch;
  padding: 0 4rpx;
}

.records-tab {
  position: relative;
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-section;
  font-weight: $pf-font-weight-semibold;
  transition: color $pf-duration-fast ease, background $pf-duration-fast ease;
}

.records-tab--pressed {
  background: $pf-color-surface-muted;
}

.records-tab--active {
  color: $pf-color-primary;
  font-weight: $pf-font-weight-bold;
}

.records-tab--active::after {
  content: "";
  position: absolute;
  right: 50%;
  bottom: 8rpx;
  width: 42rpx;
  height: 5rpx;
  border-radius: $pf-radius-pill;
  background: $pf-color-primary;
  transform: translateX(50%);
}

.records-sticky-header {
  position: sticky;
  top: 0;
  z-index: 10;
  margin-left: -$pf-space-page-x;
  margin-right: -$pf-space-page-x;
  padding: $pf-space-1 $pf-space-page-x $pf-space-2;
  background: $pf-color-page;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: $pf-space-2;
  padding: $pf-space-1 0 0;
}

.filter-picker-wrap {
  display: block;
  flex: 1;
  min-width: 0;
}

.filter-toolbar--single .filter-picker-wrap {
  flex: 0 0 calc((100% - 32rpx) / 3);
}

.filter-picker {
  display: flex;
  width: 100%;
  min-height: 80rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  padding: 0 $pf-space-2;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  transition: background $pf-duration-fast ease, border-color $pf-duration-fast ease;
}

.filter-picker--pressed {
  border-color: $pf-color-outline;
  background: $pf-color-primary-soft;
}

.filter-picker__label {
  overflow: hidden;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-medium;
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
  display: flex;
  align-items: center;
  padding: $pf-space-3;
}

.operation-copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}

.operation-title-line {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.operation-name {
  min-width: 0;
  flex: 0 1 auto;
  display: block;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-status {
  flex-shrink: 0;
  padding: 3rpx 8rpx;
  border-radius: 8rpx;
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
  font-size: 19rpx;
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

.operation-title-line + .operation-field {
  margin-top: $pf-space-2;
}

.harvest-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.harvest-row {
  display: flex;
  align-items: center;
  padding: $pf-space-3;
}

.harvest-copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}

.harvest-title-line {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10rpx;
}

.harvest-name {
  min-width: 0;
  flex: 0 1 auto;
  display: block;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.harvest-status {
  flex-shrink: 0;
  padding: 3rpx 8rpx;
  border-radius: 8rpx;
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
  font-size: 19rpx;
}

.harvest-field {
  display: block;
  margin-top: $pf-space-1;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.harvest-title-line + .harvest-field {
  margin-top: $pf-space-2;
}

.harvest-quantity {
  color: $pf-color-harvest;
  font-weight: 650;
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
