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
          <view class="pf-section-heading overview-section-heading">
            <text class="pf-section-title">农场概览</text>
          </view>
          <view
            class="overview-panel pf-tappable"
            @tap="openPlotList('ALL')"
          >
            <view class="overview-art" aria-hidden="true">
              <image class="overview-art__image" src="/static/farm-card-bg.png" mode="widthFix" />
            </view>
            <view class="overview-body">
              <view class="overview-heading">
                <view class="overview-heading__icon">
                  <image class="overview-heading__icon-image" src="/static/icons/lucide/grid-2x2.svg" mode="aspectFit" />
                </view>
                <text class="overview-heading__title">全部地块</text>
                <PfRowChevron />
              </view>
              <view class="overview-value">
                <text class="overview-value__number">{{ formatNumber(plots.length) }}</text>
                <text class="overview-value__unit">块</text>
                <view class="overview-value__area">
                  <text class="overview-value__area-label">总面积</text>
                  <text class="overview-value__area-number">{{ totalAreaLabel }}</text>
                  <text class="overview-value__area-unit">亩</text>
                </view>
              </view>
              <view class="overview-breakdown">
                <view class="breakdown-item">
                  <text class="breakdown-item__label">在种</text>
                  <view class="breakdown-item__data">
                    <text class="breakdown-item__number">{{ formatNumber(activePlotCount) }}</text>
                    <text class="breakdown-item__unit">块</text>
                  </view>
                </view>
                <view class="breakdown-item breakdown-item--idle pf-tappable" hover-class="breakdown-item--idle--pressed" @tap.stop="openPlotList('IDLE')">
                  <text class="breakdown-item__label">闲置</text>
                  <view class="breakdown-item__data">
                    <text class="breakdown-item__number">{{ formatNumber(idlePlots.length) }}</text>
                    <text class="breakdown-item__unit">块</text>
                    <text class="breakdown-item__area">· {{ idleAreaLabel }} 亩</text>
                  </view>
                  <PfRowChevron />
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
const activePlotCount = computed(() => plots.value.length - idlePlots.value.length);
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
.overview-section-heading {
  margin-top: 8rpx;
}
.overview-panel {
  position: relative;
  overflow: hidden;
  padding: 28rpx 28rpx 0;
  border: 1rpx solid $pf-color-divider;
  border-radius: $pf-radius-card-lg;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}
.overview-art {
  // 插画独立限制在上半区，避免卡片高度或统计内容改变时景物压住数值。
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 176rpx;
  overflow: hidden;
  pointer-events: none;
}
.overview-art__image {
  position: absolute;
  top: -64rpx;
  right: 0;
  width: 100%;
  opacity: 0.85;
}
.overview-art::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba($pf-color-surface, 0) 52%, $pf-color-surface 100%);
}
.overview-body {
  position: relative;
  z-index: 1;
}
.overview-heading {
  display: flex;
  align-items: center;
}
.overview-heading .pf-row-chevron {
  width: 24rpx;
  height: 24rpx;
  margin-left: 6rpx;
  opacity: 0.42;
}
.overview-heading__icon {
  display: flex;
  width: 44rpx;
  height: 44rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  border-radius: 10rpx;
  background: $pf-color-primary-soft;
}
.overview-heading__icon-image {
  display: block;
  width: 28rpx;
  height: 28rpx;
}
.overview-heading__title {
  min-width: 0;
  overflow: hidden;
  margin-left: 12rpx;
  color: $pf-color-text;
  font-size: $pf-font-size-body;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.overview-value {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  column-gap: 6rpx;
  row-gap: 12rpx;
  margin-top: 24rpx;
}
.overview-value__number {
  color: $pf-color-primary;
  font-size: 76rpx;
  font-weight: 750;
  letter-spacing: -1rpx;
  line-height: 1.05;
}
.overview-value__unit {
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-label;
  font-weight: 550;
}
.overview-value__area {
  display: flex;
  align-items: baseline;
  margin-left: auto;
  padding-left: 16rpx;
  white-space: nowrap;
}
.overview-value__area-label {
  margin-right: 8rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}
.overview-value__area-number {
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: 650;
}
.overview-value__area-unit {
  margin-left: 4rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-caption;
}
.overview-breakdown {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  column-gap: 16rpx;
  min-height: 96rpx;
  margin-top: 24rpx;
  border-top: 1rpx solid $pf-color-divider;
}
.breakdown-item {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
}
.breakdown-item__label {
  margin-right: 14rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}
.breakdown-item__data {
  display: flex;
  align-items: baseline;
}
.breakdown-item__number {
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: 650;
}
.breakdown-item__unit {
  margin-left: 4rpx;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-label;
}
.breakdown-item__area {
  margin-left: 10rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}
.breakdown-item--idle {
  margin-right: -12rpx;
  padding: 0 12rpx;
  border-radius: 12rpx;
}
.breakdown-item--idle--pressed {
  background: $pf-color-surface-muted;
}
.breakdown-item--idle .pf-row-chevron {
  width: 24rpx;
  height: 24rpx;
  margin-left: 10rpx;
  opacity: 0.42;
}
.production-name,
.production-meta,
.empty-production__title,
.empty-state__title,
.empty-state__description,
.records-entry__title,
.records-entry__description {
  display: block;
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
