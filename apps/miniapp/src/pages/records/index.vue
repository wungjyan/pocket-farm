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
            :range="statusOptions.map((item) => item.label)"
            :value="statusIndex"
            @change="handleStatusChange"
          >
            <view class="filter-picker pf-tappable" hover-class="filter-picker--pressed">
              <text class="filter-picker__label">{{ selectedStatusLabel }}</text>
              <uv-icon name="arrow-down" size="15" color="#7F8B82" />
            </view>
          </picker>
          <text class="filter-count">{{ loading ? "–" : `${productionTotal} 条` }}</text>
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
              <text class="production-meta">{{ productionMeta(item) }}</text>
            </view>
            <PfRowChevron />
          </view>
        </view>
        <view v-else class="empty-state pf-card">
          <PfBusinessIcon name="clock-3" size="empty" />
          <text class="empty-state__title">没有符合条件的种养</text>
          <text v-if="hasFilters" class="empty-state__action pf-tappable" @tap="clearFilters">查看全部种养</text>
        </view>
      </template>

      <view v-else class="placeholder-state pf-card">
        <PfBusinessIcon name="clock-3" size="empty" />
        <text class="placeholder-state__title">{{ activeTab === "OPERATION" ? "农事记录待上线" : "收获记录待上线" }}</text>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import {
  getFarmProductions,
  type FarmProduction,
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

const industryOptions: { value: Industry | ""; label: string }[] = [
  { value: "", label: "全部行业" },
  { value: "AGRICULTURE", label: "农业" },
  { value: "FORESTRY", label: "林业" },
  { value: "LIVESTOCK", label: "牧业" },
  { value: "FISHERY", label: "渔业" },
];

const statusOptions: { value: ProductionStatus | ""; label: string }[] = [
  { value: "ACTIVE", label: "进行中" },
  { value: "ENDED", label: "已结束" },
  { value: "", label: "全部状态" },
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
const industryValue = ref<Industry | "">("");
const statusValue = ref<ProductionStatus | "">("ACTIVE");
const productions = ref<FarmProduction[]>([]);
const productionTotal = ref(0);
const loading = ref(false);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm } = useFarmContext();

const industryIndex = computed(() =>
  Math.max(0, industryOptions.findIndex((item) => item.value === industryValue.value)),
);
const statusIndex = computed(() =>
  Math.max(0, statusOptions.findIndex((item) => item.value === statusValue.value)),
);
const selectedIndustryLabel = computed(() => industryOptions[industryIndex.value].label);
const selectedStatusLabel = computed(() => statusOptions[statusIndex.value].label);
const hasFilters = computed(() => Boolean(industryValue.value || statusValue.value !== "ACTIVE"));

function productionMeta(item: FarmProduction): string {
  const parts = [item.plotName, `${formatMonthDay(item.startedOn)}开始`];
  if (item.status === "ENDED") {
    if (item.endedOn) parts.push(`${formatMonthDay(item.endedOn)}结束`);
  } else if (item.initialQuantity !== null && item.initialQuantity !== undefined) {
    parts.push(`初始 ${formatNumber(item.initialQuantity)}${individualUnitLabels[item.individualUnit]}`);
  }
  return parts.join(" · ");
}

function formatMonthDay(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function switchTab(tab: RecordsTab): void {
  if (activeTab.value === tab) return;
  activeTab.value = tab;
}

function handleIndustryChange(event: { detail: { value: number | string } }): void {
  const selected = industryOptions[Number(event.detail.value)];
  if (!selected || selected.value === industryValue.value) return;
  industryValue.value = selected.value;
  loadProductions();
}

function handleStatusChange(event: { detail: { value: number | string } }): void {
  const selected = statusOptions[Number(event.detail.value)];
  if (!selected || selected.value === statusValue.value) return;
  statusValue.value = selected.value;
  loadProductions();
}

function clearFilters(): void {
  industryValue.value = "";
  statusValue.value = "ACTIVE";
  loadProductions();
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
    productionTotal.value = 0;
    return;
  }
  loading.value = true;
  try {
    const page = await getFarmProductions(targetFarmId, {
      industry: industryValue.value || undefined,
      status: statusValue.value || undefined,
      page: 1,
      pageSize: 100,
    });
    if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
    productions.value = page.items;
    productionTotal.value = page.total;
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

async function loadPageData(): Promise<void> {
  const currentFarmId = currentFarm.value?.id || 0;
  if (!currentFarmId) {
    farmId.value = 0;
    productions.value = [];
    productionTotal.value = 0;
    return;
  }
  if (currentFarmId !== farmId.value) {
    farmId.value = currentFarmId;
  }
  await loadProductions();
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
}

.filter-picker-wrap + .filter-picker-wrap {
  margin-left: 16rpx;
}

.filter-picker {
  display: flex;
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
  color: $pf-color-text-secondary;
  font-size: 25rpx;
  font-weight: 550;
}

.filter-picker .uv-icon {
  margin-left: 8rpx;
}

.filter-count {
  margin-left: auto;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.production-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.production-row {
  display: flex;
  min-height: 132rpx;
  align-items: center;
  padding: 0 22rpx;
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

.production-meta {
  display: block;
  margin-top: 7rpx;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-row--ended .production-name {
  color: $pf-color-text-secondary;
  font-weight: 600;
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

.empty-state,
.placeholder-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 42rpx 28rpx 36rpx;
  text-align: center;
}

.empty-state__title,
.placeholder-state__title {
  display: block;
  margin-top: 24rpx;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
}

.empty-state__action {
  display: block;
  margin-top: 16rpx;
  color: $pf-color-primary;
  font-size: 23rpx;
  font-weight: 600;
}
</style>
