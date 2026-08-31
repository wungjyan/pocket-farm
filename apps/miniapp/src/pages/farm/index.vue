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
          <view class="pf-section-heading overview-heading">
            <text class="pf-section-title">农场概览</text>
          </view>
          <view class="overview-grid">
            <view class="overview-card pf-tappable" @tap="openPlotList('ALL')">
              <view class="overview-card__heading">
                <text class="overview-card__title">全部地块</text>
                <PfRowChevron />
              </view>
              <view class="overview-card__value"><text>{{ plots.length }}</text><text>块</text></view>
              <text class="overview-card__area">总面积 {{ totalAreaLabel }} 亩</text>
            </view>
            <view class="overview-card pf-tappable" @tap="openPlotList('IDLE')">
              <view class="overview-card__heading">
                <text class="overview-card__title">闲置地块</text>
                <PfRowChevron />
              </view>
              <view class="overview-card__value"><text>{{ idlePlots.length }}</text><text>块</text></view>
              <text class="overview-card__area">闲置总面积 {{ idleAreaLabel }} 亩</text>
            </view>
          </view>

          <view class="pf-section-heading">
            <text class="pf-section-title">当前种养</text>
            <text class="pf-section-note">{{ activeProductions.length ? `共 ${activeSpeciesCount} 种` : "暂无种养" }}</text>
          </view>
          <view v-if="activeProductions.length" class="production-list pf-list-card">
            <view
              v-for="item in displayProductions"
              :key="item.id"
              class="production-row pf-tappable"
              @tap="openProduction(item.id)"
            >
              <view class="production-copy">
                <text class="production-name">{{ productionName(item) }}</text>
                <text class="production-meta">{{ item.plotName }} · {{ productionTime(item.startedOn) }}</text>
              </view>
              <PfRowChevron />
            </view>
            <view v-if="hasMoreProductions" class="view-more-row pf-tappable" @tap="openAllProductions">
              <text class="view-more-text">查看更多</text>
              <PfRowChevron />
            </view>
          </view>
          <view v-else class="empty-production pf-card">
            <PfBusinessIcon name="list" />
            <view class="empty-production__copy">
              <text class="empty-production__title">没有进行中的种养</text>
            </view>
            <text class="empty-production__action" @tap="openStartProduction">去开始</text>
          </view>

          <view class="records-entry pf-tappable" @tap="openRecords">
            <PfBusinessIcon name="clock-3" />
            <view class="records-entry__copy">
              <text class="records-entry__title">生产记录</text>
              <text class="records-entry__description">查看种养/农事/收获</text>
            </view>
            <PfRowChevron />
          </view>
        </template>
      </template>

      <view v-else class="empty-state pf-card">
        <PfBusinessIcon name="map" size="empty" />
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
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfPageHeader from "../../components/PfPageHeader.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { useFarmContext } from "../../services/farm-context";
import { getFarmPlots, type Plot } from "../../services/plot";
import { getFarmProductions, type FarmProduction } from "../../services/production";
import { formatNumber } from "../../utils/number";

const { currentFarm, currentFarmName, hasCurrentFarm } = useFarmContext();
const hasFarm = hasCurrentFarm;
const plots = ref<Plot[]>([]);
const activeProductions = ref<FarmProduction[]>([]);
const loading = ref(false);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);

const FARM_OVERVIEW_LIMIT = 5;
const displayProductions = computed(() => activeProductions.value.slice(0, FARM_OVERVIEW_LIMIT));
const hasMoreProductions = computed(() => activeProductions.value.length > FARM_OVERVIEW_LIMIT);

const idlePlots = computed(() => {
  const activePlotIds = new Set(activeProductions.value.map((item) => item.plotId));
  return plots.value.filter((plot) => !activePlotIds.has(plot.id));
});
const activeSpeciesCount = computed(() => new Set(activeProductions.value.map((item) => item.speciesId)).size);
const totalAreaLabel = computed(() => areaInMu(plots.value));
const idleAreaLabel = computed(() => areaInMu(idlePlots.value));

function areaInMu(items: Plot[]): string {
  const totalM2 = items.reduce((total, plot) => {
    const area = Number(plot.areaM2 ?? 0);
    return total + (Number.isFinite(area) && area >= 0 ? area : 0);
  }, 0);
  const totalMu = totalM2 / 666.6666667;
  return formatNumber(Math.round(totalMu * 100) / 100);
}

function productionName(production: FarmProduction): string {
  return `${production.speciesName}${production.variety ? ` · ${production.variety}` : ""}`;
}

function productionTime(startedOn: string): string {
  const started = new Date(`${startedOn}T00:00:00`);
  if (Number.isNaN(started.getTime())) return startedOn;
  const days = Math.max(0, Math.floor((Date.now() - started.getTime()) / 86_400_000));
  return `${started.getMonth() + 1}月${started.getDate()}日开始 · ${days}天`;
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
    const productionPage = await getFarmProductions(farm.id, { status: "ACTIVE", pageSize: 100 });
    if (currentFarm.value?.id !== farm.id) return;
    plots.value = plotPage.items;
    activeProductions.value = productionPage.items;
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

function openPlotList(filter: "ALL" | "IDLE"): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/farm-plots/index?farmId=${currentFarm.value.id}&filter=${filter}` });
}

function openProduction(productionId: number): void {
  uni.navigateTo({ url: `/pages/productions/detail?productionId=${productionId}` });
}

function openRecords(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/records/index?farmId=${currentFarm.value.id}` });
}

function openAllProductions(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/records/index?farmId=${currentFarm.value.id}` });
}

function openStartProduction(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/productions/start?farmId=${currentFarm.value.id}` });
}

// 农场上下文由共享上下文维护（创建/编辑/退出/切换时本地更新），
// 展示时只需刷新真正会变化的概览数据。
onShow(() => {
  loadOverview();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.overview-loading { display: flex; min-height: 220rpx; flex-direction: column; align-items: center; justify-content: center; margin-top: 24rpx; color: $pf-color-text-secondary; font-size: 23rpx; }
.overview-loading text { margin-top: 14rpx; }
.overview-heading { margin-top: 8rpx; }
.overview-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16rpx; }
.overview-card { min-width: 0; padding: 22rpx; border-radius: 20rpx; background: $pf-color-surface; box-shadow: $pf-shadow-card; }
.overview-card__heading { display: flex; align-items: center; justify-content: space-between; }
.overview-card__title, .overview-card__area, .production-name, .production-meta, .empty-production__title, .empty-state__title, .empty-state__description, .records-entry__title, .records-entry__description { display: block; }
.overview-card__title { color: $pf-color-text-secondary; font-size: 22rpx; font-weight: 600; }
.overview-card__value { display: flex; align-items: baseline; margin-top: 14rpx; color: $pf-color-text; }
.overview-card__value > text:first-child { font-size: 46rpx; font-weight: 750; letter-spacing: -1rpx; }
.overview-card__value > text:last-child { margin-left: 6rpx; font-size: 22rpx; font-weight: 550; }
.overview-card__area { margin-top: 7rpx; color: $pf-color-text-muted; font-size: 20rpx; }
.production-list { padding: 0; border: none; border-radius: 20rpx; box-shadow: $pf-shadow-card; }
.production-row { display: flex; min-height: 112rpx; align-items: center; padding: 0 22rpx; }
.production-row + .production-row { border-top: 1rpx solid $pf-color-divider; }
.view-more-row { display: flex; min-height: 96rpx; align-items: center; justify-content: center; border-top: 1rpx solid $pf-color-divider; }
.view-more-text { color: $pf-color-primary; font-size: 24rpx; font-weight: 600; }
.production-copy { min-width: 0; flex: 1; margin-right: 16rpx; }
.production-name { min-width: 0; overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.production-meta { margin-top: 7rpx; overflow: hidden; color: $pf-color-text-muted; font-size: 21rpx; text-overflow: ellipsis; white-space: nowrap; }
.empty-production { display: flex; min-height: 112rpx; align-items: center; padding: 0 24rpx; border: none; }
.empty-production__copy { min-width: 0; flex: 1; margin-left: 16rpx; }
.empty-production__title { color: $pf-color-text; font-size: 25rpx; font-weight: 600; }
.empty-production__action { color: $pf-color-primary; font-size: 23rpx; font-weight: 600; }
.records-entry { display: flex; min-height: 104rpx; align-items: center; margin-top: 32rpx; padding: 0 22rpx; border-radius: 20rpx; background: $pf-color-surface; box-shadow: $pf-shadow-card; }
.records-entry__copy { min-width: 0; flex: 1; margin: 0 16rpx; }
.records-entry__title { color: $pf-color-text; font-size: 27rpx; font-weight: 600; }
.records-entry__description { margin-top: 6rpx; color: $pf-color-text-muted; font-size: 21rpx; }
.empty-state { display: flex; flex-direction: column; align-items: center; margin-top: 32rpx; padding: 40rpx 28rpx 30rpx; text-align: center; }
.empty-state__title { margin-top: 24rpx; color: $pf-color-text; font-size: 31rpx; font-weight: 650; }
.empty-state__description { margin-top: 10rpx; color: $pf-color-text-secondary; font-size: 24rpx; line-height: 1.55; }
</style>
