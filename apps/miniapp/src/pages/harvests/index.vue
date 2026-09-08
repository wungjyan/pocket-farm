<template>
  <view class="pf-page harvests-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#006C49" />
        <text>正在加载收获记录</text>
      </view>
      <view v-else-if="loadError" class="state-card pf-card">
        <uv-icon name="warning" size="28" color="#A9433B" />
        <text>{{ loadError }}</text>
        <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 24rpx; border-radius: 16rpx;" @click="loadHarvests">重试</uv-button>
      </view>
      <template v-else-if="plot">
        <view class="page-toolbar">
          <view class="page-context">
            <text class="page-context__name">{{ contextValue }}</text>
            <text class="page-context__meta">{{ contextMeta }}</text>
          </view>
          <view
            v-if="canCreate"
            class="page-action pf-tappable"
            hover-class="page-action--pressed"
            @tap="openCreate"
          >
            <uv-icon name="plus" size="14" color="#006C49" />
            <text>记录{{ production ? actionLabel : "收获" }}</text>
          </view>
        </view>

        <view v-if="harvests.length" class="harvest-list">
          <view
            v-for="harvest in harvests"
            :key="harvest.id"
            class="harvest-card pf-card pf-tappable"
            hover-class="harvest-card--pressed"
            @tap="openDetail(harvest)"
          >
            <view class="harvest-copy">
              <view class="harvest-title-line">
                <text class="harvest-name">{{ harvest.productName || productionFor(harvest)?.speciesName || "收获" }}</text>
                <text v-if="isLocked(harvest)" class="harvest-status">种养已结束</text>
              </view>
              <view class="harvest-summary">
                <text class="harvest-summary__label">{{ harvestActionLabel(harvest) }}</text>
                <text class="harvest-quantity">{{ formatNumber(harvest.quantity) }} {{ unitLabel(harvest.unit) }}</text>
              </view>
              <text class="harvest-meta">{{ harvestDateLabel(harvest.harvestedAt) }} · 操作人：{{ memberName(harvest.operatorId) }}{{ creatorLabel(harvest) }}</text>
            </view>
            <PfRowChevron />
          </view>
          <uv-load-more v-if="hasMore || loadingMore" :status="loadingMore ? 'loading' : 'nomore'" icon-color="#006C49" color="#748178" />
        </view>
        <PfEmptyState v-else icon="shopping-basket" title="还没有收获记录" />
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
import { getFarmMembers, type FarmMember } from "../../services/farm";
import {
  getPlotHarvests,
  getProductionHarvests,
  type HarvestRecord,
  type QuantityUnit,
} from "../../services/harvest";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot } from "../../services/plot";
import { getPlotProductions, getProduction, type Production } from "../../services/production";
import { formatNumber } from "../../utils/number";

const unitLabels: Record<QuantityUnit, string> = {
  KG: "公斤",
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只/个",
  PLANT: "株",
  TAIL: "尾",
};

const productionId = ref(0);
const plotId = ref(0);
const production = ref<Production | null>(null);
const plot = ref<Plot | null>(null);
const productions = ref<Production[]>([]);
const harvests = ref<HarvestRecord[]>([]);
const members = ref<FarmMember[]>([]);
const loading = ref(true);
const loadError = ref("");
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const PAGE_SIZE = 20;
const totalCount = ref(0);
const currentPage = ref(1);
const hasMore = ref(false);
const loadingMore = ref(false);
const actionLabel = computed(() => {
  if (production.value?.industry === "LIVESTOCK") return "出栏";
  if (production.value?.industry === "FISHERY") return "捕捞";
  return "采收";
});
const contextValue = computed(() => production.value
  ? `${production.value.speciesName}${production.value.variety ? ` · ${production.value.variety}` : ""}`
  : plot.value?.name || "地块");
const contextMeta = computed(() => {
  const count = `共 ${formatNumber(totalCount.value)} 条收获记录`;
  return production.value && plot.value ? `${plot.value.name} · ${count}` : count;
});
const canCreate = computed(() => production.value
  ? production.value.status === "ACTIVE"
  : productions.value.some((item) => item.status === "ACTIVE"));

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function productionFor(harvest: HarvestRecord): Production | null {
  if (production.value?.id === harvest.productionId) return production.value;
  return productions.value.find((item) => item.id === harvest.productionId) || null;
}

function isLocked(harvest: HarvestRecord): boolean {
  return productionFor(harvest)?.status !== "ACTIVE";
}

function harvestActionLabel(harvest: HarvestRecord): string {
  const industry = productionFor(harvest)?.industry;
  if (industry === "LIVESTOCK") return "出栏";
  if (industry === "FISHERY") return "捕捞";
  return industry ? "采收" : "收获";
}

function unitLabel(unit: QuantityUnit): string {
  return unitLabels[unit];
}

function harvestDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function memberName(userId: number): string {
  return members.value.find((member) => member.userId === userId)?.nickname?.trim() || "未设置昵称";
}

function creatorLabel(harvest: HarvestRecord): string {
  return harvest.createdBy === harvest.operatorId ? "" : ` · 记录人：${memberName(harvest.createdBy)}`;
}

async function fetchHarvestPage(page: number): Promise<void> {
  const harvestPage = productionId.value
    ? await getProductionHarvests(productionId.value, page, PAGE_SIZE)
    : await getPlotHarvests(plotId.value, page, PAGE_SIZE);
  totalCount.value = harvestPage.total;
  harvests.value = page === 1 ? harvestPage.items : [...harvests.value, ...harvestPage.items];
  currentPage.value = page;
  hasMore.value = harvests.value.length < harvestPage.total;
}

async function loadHarvests(): Promise<void> {
  if (!productionId.value && !plotId.value) {
    loadError.value = "收获记录信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    if (productionId.value) {
      const productionResult = await getProduction(productionId.value);
      const plotResult = await getPlot(productionResult.plotId);
      production.value = productionResult;
      productions.value = [productionResult];
      plot.value = plotResult;
      plotId.value = plotResult.id;
      const [, memberPage] = await Promise.all([
        fetchHarvestPage(1),
        getFarmMembers(plotResult.farmId),
      ]);
      members.value = memberPage.items;
      return;
    }
    const plotResult = await getPlot(plotId.value);
    plot.value = plotResult;
    const [, productionPage, memberPage] = await Promise.all([
      fetchHarvestPage(1),
      getPlotProductions(plotResult.id),
      getFarmMembers(plotResult.farmId),
    ]);
    productions.value = productionPage.items;
    members.value = memberPage.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "收获记录加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

async function loadMoreHarvests(): Promise<void> {
  if (loading.value || loadingMore.value || !hasMore.value || loadError.value) return;
  loadingMore.value = true;
  try {
    await fetchHarvestPage(currentPage.value + 1);
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
    loadingMore.value = false;
  }
}

function openCreate(): void {
  if (production.value) {
    uni.navigateTo({ url: `/pages/harvests/form?productionId=${production.value.id}` });
  } else if (plot.value) {
    uni.navigateTo({ url: `/pages/harvests/form?farmId=${plot.value.farmId}&plotId=${plot.value.id}` });
  }
}

function openDetail(harvest: HarvestRecord): void {
  uni.navigateTo({ url: `/pages/harvests/detail?harvestId=${harvest.id}` });
}

onLoad((options) => {
  productionId.value = Number(options?.productionId || 0);
  plotId.value = Number(options?.plotId || 0);
});

onShow(() => {
  if (productionId.value || plotId.value) loadHarvests();
});

onReachBottom(() => {
  void loadMoreHarvests();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.harvests-page .pf-page-content {
  padding-top: $pf-space-4;
}

.page-toolbar {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 4rpx $pf-space-3;
}

.page-context {
  min-width: 0;
  flex: 1;
  overflow: hidden;
}

.page-context__name,
.page-context__meta,
.harvest-name,
.harvest-meta {
  display: block;
}

.page-context__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: $pf-font-size-section;
  font-weight: $pf-font-weight-bold;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-context__meta {
  overflow: hidden;
  margin-top: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-action {
  display: flex;
  min-height: 72rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-left: $pf-space-3;
  padding: 0 $pf-space-2;
  border-radius: $pf-radius-control;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
}

.page-action text {
  margin-left: 6rpx;
}

.page-action--pressed {
  opacity: 0.68;
}

.harvest-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.harvest-card {
  display: flex;
  min-height: 176rpx;
  box-sizing: border-box;
  align-items: center;
  padding: $pf-space-3;
}

.harvest-card--pressed {
  background: $pf-color-surface-muted;
}

.harvest-copy {
  min-width: 0;
  flex: 1;
  margin-right: $pf-space-2;
}

.harvest-title-line {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10rpx;
}

.harvest-name {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.harvest-status {
  flex-shrink: 0;
  padding: 4rpx 10rpx;
  border-radius: $pf-radius-pill;
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-caption;
  line-height: 1.3;
}

.harvest-summary {
  display: flex;
  align-items: baseline;
  margin-top: $pf-space-2;
}

.harvest-summary__label {
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-label;
}

.harvest-quantity {
  margin-left: $pf-space-1;
  color: $pf-color-primary;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.harvest-meta {
  overflow: hidden;
  margin-top: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $pf-space-4;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  text-align: center;
}

.state-card text {
  margin-top: $pf-space-2;
}
</style>
