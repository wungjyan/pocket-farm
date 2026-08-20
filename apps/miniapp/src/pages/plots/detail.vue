<template>
  <view class="pf-page plot-detail-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#2F7D4A" />
      <text>正在加载地块</text>
    </view>

    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadPlot">
        重试
      </uv-button>
    </view>

    <template v-else-if="plot">
      <view class="plot-heading">
        <view class="plot-heading__main">
          <text class="plot-heading__name">{{ plot.name }}</text>
          <text class="plot-heading__meta">{{ plotTypeLabel(plot.type) }} · {{ areaLabel(plot) }}</text>
        </view>
        <text v-if="canEdit" class="plot-heading__action" @click="openEdit">编辑</text>
      </view>

      <view class="info-card pf-card">
        <view class="info-row">
          <text class="info-label">地块类型</text>
          <text class="info-value">{{ plotTypeLabel(plot.type) }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">面积</text>
          <text class="info-value">{{ areaLabel(plot) }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">创建时间</text>
          <text class="info-value">{{ formatDate(plot.createdAt) }}</text>
        </view>
      </view>

      <view class="section-heading">
        <text class="section-heading__title">种养</text>
        <text v-if="canManageProductions" class="section-heading__action" @click="openCreateProduction">开始种养</text>
      </view>

      <view v-if="activeProductions.length" class="production-list">
        <view
          v-for="item in activeProductions"
          :key="item.id"
          class="production-card pf-card"
          @click="openProduction(item.id)"
        >
          <view class="production-card__main">
            <text class="production-card__name">{{ item.speciesName }}</text>
            <text class="production-card__meta">{{ productionMeta(item) }}</text>
          </view>
          <text class="production-card__harvest" @click.stop="openCreateHarvestFor(item.id)">{{ harvestActionLabel(item.industry) }}</text>
          <view class="production-card__status">进行中</view>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
      </view>
      <view v-else class="production-empty pf-card">
        <text>当前空闲</text>
        <text v-if="canManageProductions" class="production-empty__action" @click="openCreateProduction">开始种养</text>
      </view>

      <template v-if="endedProductions.length">
        <view class="section-heading section-heading--history">
          <text class="section-heading__title">历史种养</text>
        </view>
        <view class="production-list">
          <view
            v-for="item in endedProductions"
            :key="item.id"
            class="production-card pf-card"
            @click="openProduction(item.id)"
          >
            <view class="production-card__main">
              <text class="production-card__name">{{ item.speciesName }}</text>
              <text class="production-card__meta">{{ productionMeta(item) }}</text>
            </view>
            <view class="production-card__status production-card__status--ended">已结束</view>
            <uv-icon name="arrow-right" size="17" color="#929A93" />
          </view>
        </view>
      </template>

      <view class="section-heading">
        <text class="section-heading__title">农事</text>
        <view class="section-heading__actions">
          <text class="section-heading__action section-heading__action--secondary" @click="openOperations">查看记录</text>
          <text v-if="canManageOperations" class="section-heading__action" @click="openCreateOperation">记农事</text>
        </view>
      </view>
      <view class="operation-entry pf-card" @click="openOperations">
        <view>
          <text class="operation-entry__title">查看地块农事</text>
          <text class="operation-entry__meta">翻耕、施肥、灌溉等现场记录</text>
        </view>
        <uv-icon name="arrow-right" size="17" color="#929A93" />
      </view>

      <view class="section-heading">
        <text class="section-heading__title">收获</text>
        <view class="section-heading__actions">
          <text class="section-heading__action section-heading__action--secondary" @click="openHarvests">查看记录</text>
          <text v-if="canManageHarvests && activeProductions.length" class="section-heading__action section-heading__action--harvest" @click="openCreateHarvest">记录收获</text>
        </view>
      </view>
      <view class="harvest-entry pf-card" @click="openHarvests">
        <view class="harvest-entry__icon"><uv-icon name="order" size="20" color="#D79532" /></view>
        <view class="harvest-entry__copy">
          <text class="harvest-entry__title">查看地块收获</text>
          <text class="harvest-entry__meta">汇总该地块下的采收、捕捞和出栏记录</text>
        </view>
        <uv-icon name="arrow-right" size="17" color="#929A93" />
      </view>
    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { getFarm, type Farm } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot, type PlotType } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import type { Industry } from "../../services/species";
import { formatNumber } from "../../utils/number";

const plotId = ref(0);
const plot = ref<Plot | null>(null);
const farm = ref<Farm | null>(null);
const loading = ref(true);
const loadError = ref("");
const activeProductions = ref<Production[]>([]);
const endedProductions = ref<Production[]>([]);
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const canEdit = computed(() => farm.value?.myRole === "OWNER" || farm.value?.myRole === "ADMIN");
const canManageProductions = computed(() => Boolean(farm.value?.myRole));
const canManageOperations = computed(() => Boolean(farm.value?.myRole));
const canManageHarvests = computed(() => Boolean(farm.value?.myRole));

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
const industryLabels: Record<Industry, string> = {
  AGRICULTURE: "农业",
  FORESTRY: "林业",
  LIVESTOCK: "牧业",
  FISHERY: "渔业",
};

function plotTypeLabel(type: PlotType | null): string {
  return type ? plotTypeLabels[type] : "未分类";
}

function areaLabel(value: Plot): string {
  if (value.areaValue === null || value.areaValue === undefined || !value.areaUnit) return "未填写";
  const units: Record<string, string> = { MU: "亩", SQUARE_METER: "平方米", HECTARE: "公顷" };
  return `${formatNumber(value.areaValue)}${units[value.areaUnit] || ""}`;
}

function formatDate(value: string): string {
  const date = new Date(value.replace(" ", "T") + (value.includes("Z") ? "" : "Z"));
  if (Number.isNaN(date.getTime())) return "未知";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function productionMeta(value: Production): string {
  return `${industryLabels[value.industry]} · ${value.startedOn}开始`;
}

function harvestActionLabel(industry: Industry): string {
  if (industry === "LIVESTOCK") return "出栏";
  if (industry === "FISHERY") return "捕捞";
  return "采收";
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadPlot(): Promise<void> {
  if (!plotId.value) {
    loadError.value = "地块信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const result = await getPlot(plotId.value);
    plot.value = result;
    const [farmResult, activeResult, endedResult] = await Promise.all([
      getFarm(result.farmId),
      getPlotProductions(result.id, "ACTIVE"),
      getPlotProductions(result.id, "ENDED"),
    ]);
    farm.value = farmResult;
    activeProductions.value = activeResult.items;
    endedProductions.value = endedResult.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "地块加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openEdit(): void {
  if (plot.value) uni.navigateTo({ url: `/pages/plots/edit?plotId=${plot.value.id}` });
}

function openCreateProduction(): void {
  if (plot.value) uni.navigateTo({ url: `/pages/productions/create?plotId=${plot.value.id}` });
}

function openProduction(productionId: number): void {
  uni.navigateTo({ url: `/pages/productions/detail?productionId=${productionId}` });
}

function openOperations(): void {
  if (plot.value) uni.navigateTo({ url: `/pages/operations/index?plotId=${plot.value.id}` });
}

function openCreateOperation(): void {
  if (plot.value) uni.navigateTo({ url: `/pages/operations/form?plotId=${plot.value.id}&plotLocked=1` });
}

function openHarvests(): void {
  if (plot.value) uni.navigateTo({ url: `/pages/harvests/index?plotId=${plot.value.id}` });
}

function openCreateHarvest(): void {
  if (plot.value && activeProductions.value.length) {
    uni.navigateTo({ url: `/pages/harvests/form?farmId=${plot.value.farmId}&plotId=${plot.value.id}` });
  }
}

function openCreateHarvestFor(productionId: number): void {
  uni.navigateTo({ url: `/pages/harvests/form?productionId=${productionId}` });
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
});

onShow(() => {
  if (plotId.value) loadPlot();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.plot-detail-page {
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.plot-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 4rpx 28rpx;
}

.plot-heading__main,
.plot-heading__name,
.plot-heading__meta {
  display: block;
}

.plot-heading__main {
  min-width: 0;
}

.plot-heading__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-heading__meta {
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.plot-heading__action {
  flex-shrink: 0;
  margin-left: 24rpx;
  color: $pf-color-primary;
  font-size: 25rpx;
}

.info-card {
  padding: 8rpx 24rpx;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 92rpx;
}

.info-row + .info-row {
  border-top: 1rpx solid $pf-color-divider;
}

.info-label {
  color: $pf-color-text-secondary;
  font-size: 25rpx;
}

.info-value {
  color: $pf-color-text;
  font-size: 25rpx;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 38rpx 8rpx 14rpx;
}

.section-heading--history {
  margin-top: 34rpx;
}

.section-heading__title {
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 600;
}

.section-heading__action,
.production-empty__action {
  color: $pf-color-primary;
  font-size: 24rpx;
}

.section-heading__actions {
  display: flex;
  align-items: center;
}

.section-heading__action--secondary {
  margin-right: 22rpx;
  color: $pf-color-text-secondary;
}

.production-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.production-card {
  display: flex;
  min-height: 104rpx;
  align-items: center;
  padding: 0 22rpx;
}

.production-card__main {
  min-width: 0;
  flex: 1;
}

.production-card__name,
.production-card__meta {
  display: block;
}

.production-card__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-card__meta {
  margin-top: 6rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.production-card__status {
  margin: 0 18rpx;
  padding: 5rpx 12rpx;
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 21rpx;
}

.production-card__harvest {
  flex-shrink: 0;
  margin-left: 12rpx;
  color: $pf-color-harvest;
  font-size: 22rpx;
}

.production-card__status--ended {
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
}

.production-empty {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 24rpx;
  color: $pf-color-text-secondary;
  font-size: 25rpx;
}

.operation-entry {
  display: flex;
  min-height: 100rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 22rpx;
}

.operation-entry__title,
.operation-entry__meta {
  display: block;
}

.section-heading__action--harvest {
  color: $pf-color-harvest;
}

.harvest-entry {
  display: flex;
  min-height: 100rpx;
  align-items: center;
  padding: 0 22rpx;
  border-left: 5rpx solid $pf-color-harvest;
}

.harvest-entry__icon {
  display: flex;
  width: 52rpx;
  height: 52rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: $pf-color-harvest-soft;
}

.harvest-entry__copy {
  min-width: 0;
  flex: 1;
  margin: 0 16rpx;
}

.harvest-entry__title,
.harvest-entry__meta {
  display: block;
}

.harvest-entry__title {
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 600;
}

.harvest-entry__meta {
  margin-top: 6rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.operation-entry__title {
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 600;
}

.operation-entry__meta {
  margin-top: 6rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
