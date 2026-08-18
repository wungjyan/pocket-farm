<template>
  <view class="pf-page farm-page">
    <PfPageHeader :title="currentFarmName" />

    <view class="pf-page-content">
      <template v-if="hasFarm">
        <view class="farm-summary">
          <view class="farm-summary__item">
            <text class="farm-summary__value">{{ plotCount }}</text>
            <text class="farm-summary__label">个地块</text>
          </view>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">地块</text>
          <text v-if="canManagePlots" class="pf-section-action" @tap="openCreatePlot">创建地块</text>
        </view>
        <view v-if="loadingPlots" class="pf-card state-card">
          <uv-loading-icon mode="circle" color="#2F7D4A" />
          <text>正在加载地块</text>
        </view>
        <view v-else-if="plots.length" class="plot-list">
          <view v-for="plot in plots" :key="plot.id" class="plot-card pf-card" @tap="openPlot(plot.id)">
            <view class="plot-card__main">
              <text class="plot-card__name">{{ plot.name }}</text>
              <text class="plot-card__meta">{{ plotTypeLabel(plot.type) }} · {{ areaLabel(plot) }}</text>
            </view>
            <uv-icon name="arrow-right" size="17" color="#929A93" />
          </view>
        </view>
        <view v-else class="pf-card empty-plot">
          <uv-icon name="grid" size="24" color="#2F7D4A" />
          <text>还没有地块</text>
          <uv-button
            v-if="canManagePlots"
            type="primary"
            size="small"
            shape="square"
            custom-style="margin-top: 22rpx; border-radius: 12rpx;"
            @click="openCreatePlot"
          >
            创建地块
          </uv-button>
        </view>
      </template>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon">
          <uv-icon name="map" size="28" color="#2F7D4A" />
        </view>
        <text class="empty-state__title">先创建一个农场</text>
        <text class="empty-state__description">农场建立后，这里会成为你的生产现场。</text>
        <uv-button
          type="primary"
          shape="square"
          custom-style="width: 100%; height: 84rpx; margin-top: 28rpx; border-radius: 16rpx;"
          @click="openCreateFarm"
        >
          创建农场
        </uv-button>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { useFarmContext } from "../../services/farm-context";
import { getFarmPlots, type Plot, type PlotType } from "../../services/plot";
import { formatNumber } from "../../utils/number";

const { currentFarm, currentFarmName, hasCurrentFarm, refreshFromApi } = useFarmContext();
const hasFarm = hasCurrentFarm;
const plotCount = ref(0);
const plots = ref<Plot[]>([]);
const loadingPlots = ref(false);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);

const canManagePlots = computed(
  () => currentFarm.value?.role === "OWNER" || currentFarm.value?.role === "ADMIN",
);

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

function plotTypeLabel(type: PlotType | null): string {
  return type ? plotTypeLabels[type] : "未分类";
}

function areaLabel(plot: Plot): string {
  if (plot.areaValue === null || plot.areaValue === undefined || !plot.areaUnit) return "面积未填写";
  const units: Record<string, string> = { MU: "亩", SQUARE_METER: "平方米", HECTARE: "公顷" };
  return `${formatNumber(plot.areaValue)}${units[plot.areaUnit] || ""}`;
}

async function loadPlots(): Promise<void> {
  if (!currentFarm.value) {
    plots.value = [];
    plotCount.value = 0;
    return;
  }
  loadingPlots.value = true;
  try {
    const page = await getFarmPlots(currentFarm.value.id);
    plots.value = page.items;
    plotCount.value = page.total;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
      return;
    }
    toastRef.value?.show({ type: "default", message: error instanceof ApiRequestError ? error.message : "地块加载失败" });
  } finally {
    loadingPlots.value = false;
  }
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

function openCreatePlot(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/plots/create?farmId=${currentFarm.value.id}` });
}

function openPlot(plotId: number): void {
  uni.navigateTo({ url: `/pages/plots/detail?plotId=${plotId}` });
}

onShow(async () => {
  try {
    await refreshFromApi();
    await loadPlots();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
    }
    // The farm page keeps its local context while a transient refresh fails.
  }
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.farm-summary {
  display: flex;
  align-items: center;
  margin-top: 28rpx;
  padding: 20rpx 4rpx;
  border-bottom: 1rpx solid $pf-color-divider;
}

.farm-summary__item {
  display: flex;
  align-items: baseline;
  flex: 1;
}

.farm-summary__value {
  color: $pf-color-text;
  font-size: 34rpx;
  font-weight: 700;
}

.farm-summary__label {
  margin-left: 8rpx;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}

.empty-state {
  margin-top: 32rpx;
  padding: 32rpx 28rpx 28rpx;
  text-align: center;
}

.empty-state__icon {
  display: flex;
  width: 68rpx;
  height: 68rpx;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  border-radius: 18rpx;
  background: $pf-color-primary-soft;
}

.empty-state__title,
.empty-state__description {
  display: block;
}

.empty-state__title {
  margin-top: 22rpx;
  color: $pf-color-text;
  font-size: 30rpx;
  font-weight: 600;
}

.empty-state__description {
  margin-top: 8rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  line-height: 1.5;
}

.plot-list {
  display: flex;
  flex-direction: column;
}

.plot-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 104rpx;
  padding: 22rpx 24rpx;
}

.plot-card + .plot-card {
  margin-top: 16rpx;
}

.plot-card__main {
  min-width: 0;
}

.plot-card__name,
.plot-card__meta {
  display: block;
}

.plot-card__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 29rpx;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-card__meta {
  margin-top: 8rpx;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}

.state-card,
.empty-plot {
  display: flex;
  min-height: 140rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text,
.empty-plot text {
  margin-top: 14rpx;
}
</style>
