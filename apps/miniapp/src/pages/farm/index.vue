<template>
  <view class="pf-page farm-page">
    <PfPageHeader :title="hasFarm ? currentFarmName : '未选择农场'" variant="tab" />

    <view class="pf-page-content">
      <template v-if="hasFarm">
        <view v-if="loading" class="overview-loading pf-card">
          <uv-loading-icon mode="circle" color="#006C49" />
          <text>正在汇总农场数据</text>
        </view>
        <template v-else>
          <view class="pf-section-heading overview-heading">
            <text class="pf-section-title">农场概览</text>
          </view>
          <view class="overview-panel">
            <view class="overview-grid">
              <view
                class="overview-card overview-card--primary pf-tappable"
                @tap="openPlotList('ALL')"
              >
                <view class="overview-card__heading">
                  <view class="overview-card__icon">
                    <image class="overview-card__icon-image" src="/static/icons/lucide/grid-2x2.svg" mode="aspectFit" />
                  </view>
                  <text class="overview-card__title">全部地块</text>
                  <PfRowChevron />
                </view>
                <view class="overview-card__value"><text>{{ plots.length }}</text><text>块</text></view>
                <view class="overview-card__footer">
                  <text class="overview-card__area-label">总面积</text>
                  <text class="overview-card__area-value">{{ totalAreaLabel }} 亩</text>
                </view>
              </view>
              <view class="overview-card overview-card--idle pf-tappable" @tap="openPlotList('IDLE')">
                <view class="overview-card__heading">
                  <view class="overview-card__icon">
                    <image class="overview-card__icon-image" src="/static/icons/lucide/land-plot.svg" mode="aspectFit" />
                  </view>
                  <text class="overview-card__title">闲置地块</text>
                  <PfRowChevron />
                </view>
                <view class="overview-card__value"><text>{{ idlePlots.length }}</text><text>块</text></view>
                <view class="overview-card__footer">
                  <text class="overview-card__area-label">闲置总面积</text>
                  <text class="overview-card__area-value">{{ idleAreaLabel }} 亩</text>
                </view>
              </view>
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

.farm-page {
  background: $pf-color-page;
}

.farm-page .pf-section-title {
  color: $pf-color-text;
  font-size: 32rpx;
  font-weight: 720;
}

.farm-page .pf-section-note {
  color: $pf-color-text-muted;
  font-size: 22rpx;
  font-weight: 500;
}

.overview-loading {
  display: flex;
  min-height: 220rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 24rpx;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}
.overview-loading text {
  margin-top: 14rpx;
}
.overview-heading {
  margin-top: 8rpx;
}
.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr);
  gap: 18rpx;
}
.overview-panel {
  padding: 20rpx;
  border: 1rpx solid rgba($pf-color-divider, 0.78);
  border-radius: 28rpx;
  background: $pf-color-surface;
}
.overview-card {
  display: flex;
  min-width: 0;
  min-height: 208rpx;
  box-sizing: border-box;
  flex-direction: column;
  padding: 22rpx 24rpx 20rpx;
  border-radius: 20rpx;
  background: $pf-color-page;
}
.overview-card--primary {
  background: $pf-gradient-data;
}
.overview-card--idle {
  border: 1rpx solid $pf-color-divider;
  background: $pf-color-surface-subtle;
}
.overview-card__heading {
  display: flex;
  align-items: center;
}
.overview-card__heading .pf-row-chevron {
  width: 28rpx;
  height: 28rpx;
  margin-left: auto;
  opacity: 0.42;
}
.overview-card__icon {
  width: 28rpx;
  height: 28rpx;
}
.overview-card__icon-image {
  display: block;
  width: 28rpx;
  height: 28rpx;
}
.overview-card__title,
.overview-card__area-label,
.overview-card__area-value,
.production-name,
.production-meta,
.empty-production__title,
.empty-state__title,
.empty-state__description,
.records-entry__title,
.records-entry__description {
  display: block;
}
.overview-card__title {
  min-width: 0;
  overflow: hidden;
  margin-left: 8rpx;
  color: $pf-color-text-secondary;
  font-size: 22rpx;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.overview-card__value {
  display: flex;
  align-items: baseline;
  margin-top: 18rpx;
  color: $pf-color-text;
}
.overview-card__value > text:first-child {
  font-size: 52rpx;
  font-weight: 750;
  letter-spacing: -1rpx;
}
.overview-card__value > text:last-child {
  margin-left: 4rpx;
  color: $pf-color-text-secondary;
  font-size: 22rpx;
  font-weight: 550;
}
.overview-card__footer {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 14rpx;
  border-top: 1rpx solid $pf-color-divider;
}
.overview-card__area-label {
  color: $pf-color-text-muted;
  font-size: 20rpx;
}
.overview-card__area-value {
  color: $pf-color-text;
  font-size: 24rpx;
  font-weight: 650;
}
.overview-card--primary .overview-card__title {
  color: rgba($pf-color-on-primary, 0.85);
}
.overview-card--primary .overview-card__value {
  color: $pf-color-surface;
}
.overview-card--primary .overview-card__value > text:last-child {
  color: rgba($pf-color-on-primary, 0.75);
}
.overview-card--primary .overview-card__area-label {
  color: rgba($pf-color-on-primary, 0.65);
}
.overview-card--primary .overview-card__area-value {
  color: $pf-color-surface;
}
.overview-card--primary .overview-card__footer {
  border-top-color: rgba($pf-color-on-primary, 0.2);
}
.overview-card--primary .overview-card__heading .pf-row-chevron {
  opacity: 0.8;
  filter: brightness(0) invert(1);
}
.overview-card--primary .overview-card__icon-image {
  filter: brightness(0) invert(1);
}
.overview-card--idle .overview-card__icon-image {
  opacity: 0.48;
}
.production-list {
  padding: 0;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}
.production-row {
  display: flex;
  min-height: 112rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 18rpx 22rpx;
}
.production-row + .production-row {
  border-top: 1rpx solid $pf-color-divider;
}
.production-row .pf-row-chevron {
  width: 28rpx;
  height: 28rpx;
  flex-shrink: 0;
  opacity: 0.42;
}
.view-more-row {
  display: flex;
  min-height: 88rpx;
  align-items: center;
  justify-content: center;
  border-top: 1rpx solid $pf-color-divider;
}
.view-more-text {
  color: $pf-color-primary;
  font-size: 24rpx;
  font-weight: 650;
}
.view-more-row .pf-row-chevron {
  width: 26rpx;
  height: 26rpx;
  margin-left: 4rpx;
  opacity: 0.7;
}
.production-copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}
.production-name {
  min-width: 0;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.production-meta {
  margin-top: 6rpx;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty-production {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 24rpx;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}
.empty-production :deep(.pf-business-icon) {
  background: $pf-color-primary-soft;
}
.empty-production__copy {
  min-width: 0;
  flex: 1;
  margin-left: 16rpx;
}
.empty-production__title {
  color: $pf-color-text;
  font-size: 25rpx;
  font-weight: 600;
}
.empty-production__action {
  color: $pf-color-primary;
  font-size: 23rpx;
  font-weight: 650;
}
.records-entry {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  margin-top: 32rpx;
  padding: 12rpx 22rpx;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}
.records-entry :deep(.pf-business-icon) {
  width: 56rpx;
  height: 56rpx;
  border-radius: 16rpx;
  background: $pf-color-primary-soft;
}
.records-entry :deep(.pf-business-icon__image) {
  width: 32rpx;
  height: 32rpx;
}
.records-entry .pf-row-chevron {
  width: 28rpx;
  height: 28rpx;
  opacity: 0.42;
}
.records-entry__copy {
  min-width: 0;
  flex: 1;
  margin: 0 16rpx;
}
.records-entry__title {
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 650;
}
.records-entry__description {
  margin-top: 3rpx;
  color: $pf-color-text-muted;
  font-size: 20rpx;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 32rpx;
  padding: 40rpx 28rpx 30rpx;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
  text-align: center;
}
.empty-state :deep(.pf-business-icon) {
  background: $pf-color-primary-soft;
}
.empty-state__title {
  margin-top: 24rpx;
  color: $pf-color-text;
  font-size: 31rpx;
  font-weight: 650;
}
.empty-state__description {
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  line-height: 1.55;
}
</style>
