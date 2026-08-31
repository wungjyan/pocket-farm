<template>
  <view class="pf-page harvests-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#286B46" />
        <text>正在加载收获记录</text>
      </view>
      <view v-else-if="loadError" class="state-card pf-card">
        <uv-icon name="warning" size="28" color="#C96A45" />
        <text>{{ loadError }}</text>
        <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadHarvests">重试</uv-button>
      </view>
      <template v-else-if="plot">
        <view class="page-toolbar">
          <view class="page-context">
            <view class="page-context__scope">
              <text class="page-context__label">{{ contextLabel }}</text>
              <text class="page-context__value">{{ contextValue }}</text>
            </view>
            <text class="page-context__separator">·</text>
            <view class="page-context__count">
              <text class="page-context__label">收获记录共</text>
              <text class="page-context__value">{{ harvests.length }}</text>
              <text class="page-context__label">条</text>
            </view>
          </view>
          <view v-if="canCreate" class="page-action pf-tappable" @tap="openCreate">
            <text>记录{{ production ? actionLabel : "收获" }}</text>
          </view>
        </view>

        <view v-if="harvests.length" class="harvest-list">
          <view
            v-for="harvest in harvests"
            :key="harvest.id"
            class="harvest-card pf-card pf-tappable"
            @tap="openDetail(harvest)"
          >
            <view class="harvest-copy">
              <view class="harvest-title-line">
                <text class="harvest-name">{{ harvest.productName || productionFor(harvest)?.speciesName || "收获" }}</text>
                <text v-if="isLocked(harvest)" class="harvest-status">种养已结束</text>
              </view>
              <text class="harvest-summary">
                {{ harvestActionLabel(harvest) }}：<text class="harvest-quantity">{{ formatNumber(harvest.quantity) }} {{ unitLabel(harvest.unit) }}</text>
              </text>
              <text class="harvest-meta">操作时间：{{ harvestDateLabel(harvest.harvestedAt) }}</text>
              <text class="harvest-meta">操作人：{{ memberName(harvest.operatorId) }}{{ creatorLabel(harvest) }}</text>
            </view>
            <PfRowChevron />
          </view>
        </view>
        <view v-else class="empty-card pf-card">
          <uv-icon name="order" size="30" color="#286B46" />
          <text class="empty-card__title">还没有收获记录</text>
          <uv-button v-if="canCreate" type="primary" size="small" shape="square" custom-style="margin-top: 24rpx; border-radius: 12rpx;" @click="openCreate">记录收获</uv-button>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
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
const actionLabel = computed(() => {
  if (production.value?.industry === "LIVESTOCK") return "出栏";
  if (production.value?.industry === "FISHERY") return "捕捞";
  return "采收";
});
const contextLabel = computed(() => production.value ? "种养" : "地块");
const contextValue = computed(() => production.value
  ? `${production.value.speciesName}${production.value.variety ? ` · ${production.value.variety}` : ""}`
  : plot.value?.name || "地块");
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
      const [harvestPage, memberPage] = await Promise.all([
        getProductionHarvests(productionResult.id),
        getFarmMembers(plotResult.farmId),
      ]);
      production.value = productionResult;
      productions.value = [productionResult];
      plot.value = plotResult;
      plotId.value = plotResult.id;
      harvests.value = harvestPage.items;
      members.value = memberPage.items;
      return;
    }
    const plotResult = await getPlot(plotId.value);
    const [harvestPage, productionPage, memberPage] = await Promise.all([
      getPlotHarvests(plotResult.id),
      getPlotProductions(plotResult.id),
      getFarmMembers(plotResult.farmId),
    ]);
    plot.value = plotResult;
    harvests.value = harvestPage.items;
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
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.page-toolbar { display: flex; min-height: 96rpx; align-items: center; justify-content: space-between; padding: 0 4rpx 10rpx; }
.page-context { min-width: 0; flex: 1; display: flex; align-items: center; overflow: hidden; color: $pf-color-text-secondary; font-size: 24rpx; white-space: nowrap; }
.page-context__scope { display: flex; min-width: 0; flex: 0 1 auto; align-items: center; overflow: hidden; }
.page-context__value { overflow: hidden; margin: 0 $pf-space-1; color: $pf-color-harvest; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.page-context__scope .page-context__value { min-width: 0; flex: 1; }
.page-context__separator { flex-shrink: 0; margin-right: $pf-space-1; color: $pf-color-text-muted; }
.page-context__count { display: flex; align-items: center; }
.page-context__count, .page-context__label { flex-shrink: 0; }
.page-action { display: flex; min-height: 88rpx; flex-shrink: 0; align-items: center; margin-left: $pf-space-3; padding: 0 $pf-space-1; color: $pf-color-harvest; font-size: 25rpx; font-weight: 600; }
.harvest-list { display: flex; flex-direction: column; gap: $pf-space-2; }
.harvest-card { display: flex; align-items: center; padding: $pf-space-3; }
.harvest-copy { min-width: 0; flex: 1; margin-right: $pf-space-2; }
.harvest-title-line { display: flex; min-width: 0; align-items: center; gap: 10rpx; }
.harvest-name { overflow: hidden; color: $pf-color-text; font-size: 28rpx; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.harvest-status { flex-shrink: 0; padding: 3rpx 8rpx; border-radius: 8rpx; background: $pf-color-surface-muted; color: $pf-color-text-muted; font-size: 19rpx; }
.harvest-summary { display: block; margin-top: $pf-space-2; color: $pf-color-text-secondary; font-size: 22rpx; line-height: 1.35; }
.harvest-quantity { color: $pf-color-harvest; font-size: 24rpx; font-weight: 650; }
.harvest-meta { display: block; margin-top: $pf-space-1; overflow: hidden; color: $pf-color-text-muted; font-size: 22rpx; line-height: 1.35; text-overflow: ellipsis; white-space: nowrap; }
.empty-card, .state-card { display: flex; min-height: 220rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 28rpx; color: $pf-color-text-secondary; font-size: 24rpx; text-align: center; }
.empty-card__title { display: block; margin-top: 14rpx; color: $pf-color-text; font-size: 27rpx; font-weight: 600; }
.state-card text { margin-top: 16rpx; }
</style>
