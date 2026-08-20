<template>
  <view class="pf-page farm-page">
    <PfPageHeader :title="hasFarm ? currentFarmName : '未选择农场'" variant="tab" />

    <view class="pf-page-content">
      <template v-if="hasFarm">
        <view v-if="loading" class="overview-loading pf-card">
          <uv-loading-icon mode="circle" color="#286B46" />
          <text>正在汇总农场数据</text>
        </view>
        <template v-else>
          <view class="overview-card pf-card--emphasis">
            <view class="overview-area">
              <text class="overview-eyebrow">农场总面积</text>
              <view class="overview-area__value">
                <text>{{ totalAreaLabel }}</text>
                <text v-if="totalAreaLabel !== '–'" class="overview-area__unit">亩</text>
              </view>
            </view>
            <view class="overview-metrics">
              <view class="overview-metric">
                <text class="overview-metric__value">{{ plots.length }}</text>
                <text class="overview-metric__label">全部地块</text>
              </view>
              <view class="overview-metric">
                <text class="overview-metric__value">{{ activeProductions.length }}</text>
                <text class="overview-metric__label">进行中种养</text>
              </view>
              <view class="overview-metric">
                <text class="overview-metric__value">{{ idlePlotCount }}</text>
                <text class="overview-metric__label">闲置地块</text>
              </view>
            </view>
          </view>

          <view class="pf-section-heading">
            <text class="pf-section-title">当前种养</text>
            <text class="pf-section-note">{{ activeProductions.length ? `共 ${activeProductions.length} 批` : "暂无种养" }}</text>
          </view>
          <view v-if="activeProductions.length" class="production-list pf-list-card">
            <view
              v-for="item in activeProductions"
              :key="item.id"
              class="production-row pf-tappable"
              @tap="openProduction(item.id)"
            >
              <view class="production-icon"><uv-icon :name="industryIcon(item.industry)" size="19" color="#286B46" /></view>
              <view class="production-copy">
                <view class="production-heading">
                  <text class="production-name">{{ productionName(item) }}</text>
                  <text class="production-status">进行中</text>
                </view>
                <text class="production-meta">{{ item.plotName }} · {{ productionTime(item.startedOn) }}</text>
              </view>
              <uv-icon name="arrow-right" size="16" color="#7F8B82" />
            </view>
          </view>
          <view v-else class="empty-production pf-card">
            <view class="empty-production__icon"><uv-icon name="list" size="23" color="#286B46" /></view>
            <view class="empty-production__copy">
              <text class="empty-production__title">没有进行中的种养</text>
              <text class="empty-production__description">从工作台开始一批新的种养。</text>
            </view>
            <text class="empty-production__action" @tap="openHome">去开始</text>
          </view>

          <view class="pf-section-heading">
            <text class="pf-section-title">农场管理</text>
            <text class="pf-section-note">资料与生产现场</text>
          </view>
          <view class="manage-list pf-list-card">
            <view class="manage-row pf-tappable" @tap="openPlotList">
              <view class="manage-icon"><uv-icon name="grid" size="20" color="#286B46" /></view>
              <view class="manage-copy">
                <text class="manage-title">地块列表</text>
                <text class="manage-description">查看、创建和维护全部地块</text>
              </view>
              <uv-icon name="arrow-right" size="17" color="#7F8B82" />
            </view>
            <view class="manage-divider" />
            <view class="manage-row pf-tappable" @tap="openFarmSettings">
              <view class="manage-icon manage-icon--neutral"><uv-icon name="setting" size="20" color="#536158" /></view>
              <view class="manage-copy">
                <text class="manage-title">农场设置</text>
                <text class="manage-description">农场资料、成员与权限</text>
              </view>
              <uv-icon name="arrow-right" size="17" color="#7F8B82" />
            </view>
          </view>
        </template>
      </template>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon"><uv-icon name="map" size="27" color="#286B46" /></view>
        <text class="empty-state__title">先创建一个农场</text>
        <text class="empty-state__description">农场建立后，这里会汇总面积、地块和当前种养。</text>
        <uv-button type="primary" shape="square" custom-style="width: 100%; height: 88rpx; margin-top: 32rpx; border-radius: 16rpx;" @click="openCreateFarm">创建农场</uv-button>
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
import { getFarmPlots, type Plot } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import type { Industry } from "../../services/species";
import { formatNumber } from "../../utils/number";

interface FarmProduction extends Production {
  plotName: string;
}

const { currentFarm, currentFarmName, hasCurrentFarm, refreshFromApi } = useFarmContext();
const hasFarm = hasCurrentFarm;
const plots = ref<Plot[]>([]);
const activeProductions = ref<FarmProduction[]>([]);
const loading = ref(false);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);

const idlePlotCount = computed(() => {
  const activePlotIds = new Set(activeProductions.value.map((item) => item.plotId));
  return plots.value.filter((plot) => !activePlotIds.has(plot.id)).length;
});
const totalAreaLabel = computed(() => {
  const areaValues = plots.value
    .filter((plot) => plot.areaM2 !== null && plot.areaM2 !== undefined && plot.areaM2 !== "")
    .map((plot) => Number(plot.areaM2))
    .filter((area) => Number.isFinite(area) && area >= 0);
  if (!areaValues.length) return "–";
  const totalMu = areaValues.reduce((total, area) => total + area, 0) / 666.6666667;
  return formatNumber(Math.round(totalMu * 100) / 100);
});

function productionName(production: FarmProduction): string {
  return `${production.speciesName}${production.variety ? ` · ${production.variety}` : ""}`;
}

function productionTime(startedOn: string): string {
  const started = new Date(`${startedOn}T00:00:00`);
  if (Number.isNaN(started.getTime())) return startedOn;
  const days = Math.max(0, Math.floor((Date.now() - started.getTime()) / 86_400_000));
  return `${started.getMonth() + 1}月${started.getDate()}日开始 · ${days}天`;
}

function industryIcon(industry: Industry): string {
  if (industry === "FISHERY") return "order";
  if (industry === "LIVESTOCK") return "home";
  if (industry === "FORESTRY") return "map";
  return "grid";
}

async function loadOverview(): Promise<void> {
  const farm = currentFarm.value;
  if (!farm) {
    plots.value = [];
    activeProductions.value = [];
    return;
  }
  loading.value = true;
  try {
    const plotPage = await getFarmPlots(farm.id);
    const productionGroups = await Promise.all(
      plotPage.items.map(async (plot) => {
        const page = await getPlotProductions(plot.id, "ACTIVE", 1, 100);
        return page.items.map((item) => ({ ...item, plotName: plot.name }));
      }),
    );
    if (currentFarm.value?.id !== farm.id) return;
    plots.value = plotPage.items;
    activeProductions.value = productionGroups
      .flat()
      .sort((left, right) => right.startedOn.localeCompare(left.startedOn));
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
      return;
    }
    toastRef.value?.show({ type: "default", message: error instanceof ApiRequestError ? error.message : "农场数据加载失败" });
  } finally {
    loading.value = false;
  }
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

function openPlotList(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/plots/index?farmId=${currentFarm.value.id}` });
}

function openFarmSettings(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/farms/detail?farmId=${currentFarm.value.id}` });
}

function openProduction(productionId: number): void {
  uni.navigateTo({ url: `/pages/productions/detail?productionId=${productionId}` });
}

function openHome(): void {
  uni.switchTab({ url: "/pages/home/index" });
}

onShow(async () => {
  try {
    await refreshFromApi();
    await loadOverview();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
    }
  }
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.overview-loading { display: flex; min-height: 220rpx; flex-direction: column; align-items: center; justify-content: center; margin-top: 24rpx; color: $pf-color-text-secondary; font-size: 23rpx; }
.overview-loading text { margin-top: 14rpx; }
.overview-card { margin-top: 24rpx; padding: 30rpx 28rpx 26rpx; }
.overview-eyebrow, .overview-metric__value, .overview-metric__label, .production-name, .production-meta, .empty-production__title, .empty-production__description, .manage-title, .manage-description, .empty-state__title, .empty-state__description { display: block; }
.overview-eyebrow { color: $pf-color-primary; font-size: 22rpx; font-weight: 600; }
.overview-area__value { display: flex; align-items: baseline; margin-top: 6rpx; color: $pf-color-text; }
.overview-area__value > text:first-child { font-size: 58rpx; font-weight: 750; letter-spacing: -2rpx; }
.overview-area__unit { margin-left: 9rpx; font-size: 24rpx; font-weight: 550; }
.overview-metrics { display: flex; margin-top: 28rpx; padding-top: 24rpx; border-top: 1rpx solid rgba(40, 107, 70, 0.12); }
.overview-metric { flex: 1; }
.overview-metric + .overview-metric { padding-left: 22rpx; border-left: 1rpx solid rgba(40, 107, 70, 0.12); }
.overview-metric__value { color: $pf-color-text; font-size: 32rpx; font-weight: 700; }
.overview-metric__label { margin-top: 5rpx; color: $pf-color-text-secondary; font-size: 20rpx; }
.production-list { padding: 6rpx 0; }
.production-row { display: flex; min-height: 112rpx; align-items: center; padding: 0 22rpx; }
.production-row + .production-row { border-top: 1rpx solid $pf-color-divider; }
.production-icon { display: flex; width: 54rpx; height: 54rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 17rpx; background: $pf-color-primary-soft; }
.production-copy { min-width: 0; flex: 1; margin: 0 16rpx; }
.production-heading { display: flex; align-items: center; }
.production-name { min-width: 0; overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.production-status { flex-shrink: 0; margin-left: 10rpx; padding: 4rpx 10rpx; border-radius: 999rpx; background: $pf-color-primary-soft; color: $pf-color-primary; font-size: 18rpx; }
.production-meta { margin-top: 7rpx; overflow: hidden; color: $pf-color-text-muted; font-size: 21rpx; text-overflow: ellipsis; white-space: nowrap; }
.empty-production { display: flex; min-height: 126rpx; align-items: center; padding: 24rpx; }
.empty-production__icon { display: flex; width: 54rpx; height: 54rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 17rpx; background: $pf-color-primary-soft; }
.empty-production__copy { min-width: 0; flex: 1; margin-left: 16rpx; }
.empty-production__title { color: $pf-color-text; font-size: 25rpx; font-weight: 600; }
.empty-production__description { margin-top: 6rpx; color: $pf-color-text-muted; font-size: 21rpx; }
.empty-production__action { color: $pf-color-primary; font-size: 23rpx; font-weight: 600; }
.manage-list { overflow: hidden; }
.manage-row { display: flex; min-height: 112rpx; align-items: center; padding: 0 22rpx; }
.manage-divider { height: 1rpx; margin-left: 92rpx; background: $pf-color-divider; }
.manage-icon { display: flex; width: 54rpx; height: 54rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 17rpx; background: $pf-color-primary-soft; }
.manage-icon--neutral { background: $pf-color-surface-muted; }
.manage-copy { min-width: 0; flex: 1; margin: 0 16rpx; }
.manage-title { color: $pf-color-text; font-size: 27rpx; font-weight: 600; }
.manage-description { margin-top: 6rpx; color: $pf-color-text-muted; font-size: 21rpx; }
.empty-state { margin-top: 32rpx; padding: 40rpx 28rpx 30rpx; text-align: center; }
.empty-state__icon { display: flex; width: 72rpx; height: 72rpx; align-items: center; justify-content: center; margin: 0 auto; border-radius: 22rpx; background: $pf-color-primary-soft; }
.empty-state__title { margin-top: 24rpx; color: $pf-color-text; font-size: 31rpx; font-weight: 650; }
.empty-state__description { margin-top: 10rpx; color: $pf-color-text-secondary; font-size: 24rpx; line-height: 1.55; }
</style>
