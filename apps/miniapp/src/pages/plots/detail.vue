<template>
  <view class="pf-page plot-detail-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#286B46" />
      <text>正在加载地块</text>
    </view>

    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadPlot"
      >重试</uv-button>
    </view>

    <view v-else-if="plot" class="pf-page-content">
      <view class="plot-overview">
        <view class="plot-overview__top">
          <view class="plot-overview__icon">
            <uv-icon :name="plotIcon(plot.type)" size="25" color="#286B46" />
          </view>
          <view class="plot-overview__copy">
            <text class="plot-overview__eyebrow">{{ plotTypeLabel(plot.type) }}</text>
            <text class="plot-overview__name">{{ plot.name }}</text>
          </view>
          <view v-if="canEdit" class="plot-overview__edit pf-tappable" @tap="openEdit">
            <uv-icon name="edit-pen" size="15" color="#286B46" />
            <text>编辑</text>
          </view>
        </view>

        <view class="plot-overview__metrics">
          <view class="overview-metric">
            <text class="overview-metric__value">{{ areaLabel(plot) }}</text>
            <text class="overview-metric__label">地块面积</text>
          </view>
          <view class="overview-metric">
            <text class="overview-metric__value">{{ activeProductions.length }}</text>
            <text class="overview-metric__label">当前种养</text>
          </view>
          <view class="overview-metric">
            <text class="overview-metric__value overview-metric__value--date">{{ formatDate(plot.createdAt) }}</text>
            <text class="overview-metric__label">创建日期</text>
          </view>
        </view>
      </view>

      <view class="quick-actions">
        <view v-if="canManageProductions" class="quick-action pf-tappable" @tap="openCreateProduction">
          <view class="quick-action__icon"><uv-icon name="plus" size="21" color="#286B46" /></view>
          <text class="quick-action__title">开始种养</text>
        </view>
        <view v-if="canManageOperations" class="quick-action pf-tappable" @tap="openCreateOperation">
          <view class="quick-action__icon"><uv-icon name="edit-pen" size="20" color="#286B46" /></view>
          <text class="quick-action__title">记农事</text>
        </view>
        <view
          v-if="canManageHarvests"
          class="quick-action pf-tappable"
          :class="{ 'quick-action--disabled': !activeProductions.length }"
          @tap="openCreateHarvest"
        >
          <view class="quick-action__icon"><uv-icon name="order" size="20" color="#286B46" /></view>
          <text class="quick-action__title">记收获</text>
        </view>
      </view>

      <view class="pf-section-heading">
        <text class="pf-section-title">当前种养</text>
        <text class="pf-section-note">{{ activeProductions.length ? `进行中 ${activeProductions.length} 项` : "地块空闲" }}</text>
      </view>

      <view v-if="activeProductions.length" class="production-list pf-list-card">
        <view
          v-for="item in activeProductions"
          :key="item.id"
          class="production-row pf-tappable"
          @tap="openProduction(item.id)"
        >
          <view class="production-row__icon">
            <uv-icon :name="industryIcon(item.industry)" size="20" color="#286B46" />
          </view>
          <view class="production-row__copy">
            <view class="production-row__heading">
              <text class="production-row__name">{{ item.speciesName }}</text>
              <text v-if="item.variety" class="production-row__variety">{{ item.variety }}</text>
            </view>
            <text class="production-row__meta">{{ productionMeta(item) }}</text>
          </view>
          <view class="production-row__tail">
            <text class="status-chip">进行中</text>
            <uv-icon name="arrow-right" size="16" color="#7F8B82" />
          </view>
        </view>
      </view>
      <view v-else class="production-empty pf-card pf-tappable" @tap="openCreateProduction">
        <view class="production-empty__icon"><uv-icon name="plus" size="20" color="#286B46" /></view>
        <view class="production-empty__copy">
          <text class="production-empty__title">这个地块目前空闲</text>
          <text class="production-empty__meta">开始种养后，会在这里展示当前批次。</text>
        </view>
        <uv-icon name="arrow-right" size="16" color="#7F8B82" />
      </view>

      <template v-if="endedProductions.length">
        <view class="pf-section-heading history-heading">
          <text class="pf-section-title">历史种养</text>
          <text class="pf-section-note">共 {{ endedProductions.length }} 项</text>
        </view>
        <view class="production-list pf-list-card">
          <view
            v-for="item in endedProductions"
            :key="item.id"
            class="production-row pf-tappable"
            @tap="openProduction(item.id)"
          >
            <view class="production-row__icon production-row__icon--muted">
              <uv-icon :name="industryIcon(item.industry)" size="20" color="#536158" />
            </view>
            <view class="production-row__copy">
              <view class="production-row__heading">
                <text class="production-row__name">{{ item.speciesName }}</text>
                <text v-if="item.variety" class="production-row__variety production-row__variety--muted">{{ item.variety }}</text>
              </view>
              <text class="production-row__meta">{{ productionMeta(item) }}</text>
            </view>
            <view class="production-row__tail">
              <text class="status-chip status-chip--ended">已结束</text>
              <uv-icon name="arrow-right" size="16" color="#7F8B82" />
            </view>
          </view>
        </view>
      </template>

      <view class="pf-section-heading">
        <text class="pf-section-title">生产记录</text>
        <text class="pf-section-note">按记录类型查看</text>
      </view>
      <view class="record-list pf-list-card">
        <view class="record-row pf-tappable" @tap="openOperations">
          <view class="record-row__icon"><uv-icon name="calendar" size="20" color="#286B46" /></view>
          <view class="record-row__copy">
            <text class="record-row__title">农事记录</text>
            <text class="record-row__meta">翻耕、施肥、灌溉等现场作业</text>
          </view>
          <uv-icon name="arrow-right" size="16" color="#7F8B82" />
        </view>
        <view class="record-row pf-tappable" @tap="openHarvests">
          <view class="record-row__icon"><uv-icon name="order" size="20" color="#286B46" /></view>
          <view class="record-row__copy">
            <text class="record-row__title">收获记录</text>
            <text class="record-row__meta">查看采收、捕捞和出栏记录</text>
          </view>
          <uv-icon name="arrow-right" size="16" color="#7F8B82" />
        </view>
      </view>
    </view>
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
import type { IndividualUnit, Industry } from "../../services/species";
import { formatNumber } from "../../utils/number";

const plotId = ref(0);
const plot = ref<Plot | null>(null);
const farm = ref<Farm | null>(null);
const loading = ref(true);
const loadError = ref("");
const activeProductions = ref<Production[]>([]);
const endedProductions = ref<Production[]>([]);
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
const individualUnitLabels: Record<IndividualUnit, string> = {
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "个",
  PLANT: "株",
  TAIL: "尾",
};

function plotTypeLabel(type: PlotType | null): string {
  return type ? plotTypeLabels[type] : "未分类";
}

function plotIcon(type: PlotType | null): string {
  if (type === "POND") return "order";
  if (type === "BARN") return "home";
  if (type === "ORCHARD" || type === "FOREST") return "map";
  return "grid";
}

function industryIcon(industry: Industry): string {
  if (industry === "FISHERY") return "order";
  if (industry === "LIVESTOCK") return "home";
  if (industry === "FORESTRY") return "map";
  return "grid";
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
  const details = [industryLabels[value.industry], `${value.startedOn}开始`];
  if (value.initialQuantity !== null && value.initialQuantity !== undefined) {
    details.push(`初始 ${formatNumber(value.initialQuantity)}${individualUnitLabels[value.individualUnit]}`);
  }
  return details.join(" · ");
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
  if (plot.value) {
    uni.navigateTo({
      url: `/pages/species/index?purpose=production&farmId=${plot.value.farmId}&plotId=${plot.value.id}`,
    });
  }
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
  if (!plot.value) return;
  if (!activeProductions.value.length) {
    uni.showToast({ title: "暂无进行中的种养", icon: "none" });
    return;
  }
  uni.navigateTo({ url: `/pages/harvests/form?farmId=${plot.value.farmId}&plotId=${plot.value.id}` });
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
  padding-bottom: $pf-space-page-bottom;
}

.plot-detail-page .pf-page-content {
  padding-top: $pf-space-3;
}

.plot-overview {
  overflow: hidden;
  border-radius: $pf-radius-card-lg;
  background: $pf-color-primary-soft;
}

.plot-overview__top {
  display: flex;
  align-items: center;
  padding: 30rpx 28rpx 26rpx;
}

.plot-overview__icon {
  display: flex;
  width: 72rpx;
  height: 72rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.72);
}

.plot-overview__copy {
  min-width: 0;
  flex: 1;
  margin-left: 20rpx;
}

.plot-overview__eyebrow,
.plot-overview__name,
.overview-metric__value,
.overview-metric__label,
.production-row__meta,
.production-empty__title,
.production-empty__meta,
.record-row__title,
.record-row__meta {
  display: block;
}

.plot-overview__eyebrow {
  color: $pf-color-primary;
  font-size: 22rpx;
  font-weight: 600;
}

.plot-overview__name {
  overflow: hidden;
  margin-top: 5rpx;
  color: $pf-color-text;
  font-size: 36rpx;
  font-weight: 700;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-overview__edit {
  display: flex;
  min-height: 64rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  margin-left: 18rpx;
  padding: 0 18rpx;
  border: 1rpx solid rgba(40, 107, 70, 0.18);
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.66);
  color: $pf-color-primary;
  font-size: 22rpx;
  font-weight: 600;
}

.plot-overview__edit text {
  margin-left: 7rpx;
}

.plot-overview__metrics {
  display: flex;
  padding: 24rpx 12rpx 26rpx;
  border-top: 1rpx solid rgba(40, 107, 70, 0.1);
  background: rgba(255, 255, 255, 0.28);
}

.overview-metric {
  position: relative;
  min-width: 0;
  flex: 1;
  padding: 0 12rpx;
  text-align: center;
}

.overview-metric + .overview-metric::before {
  position: absolute;
  top: 5rpx;
  bottom: 5rpx;
  left: 0;
  width: 1rpx;
  background: rgba(40, 107, 70, 0.12);
  content: "";
}

.overview-metric__value {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 680;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-metric__value--date {
  font-size: 24rpx;
}

.overview-metric__label {
  margin-top: 7rpx;
  color: $pf-color-text-secondary;
  font-size: 20rpx;
}

.quick-actions {
  display: flex;
  gap: 14rpx;
  margin-top: $pf-space-3;
}

.quick-action {
  display: flex;
  min-width: 0;
  min-height: 118rpx;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.quick-action--disabled {
  opacity: 0.48;
}

.quick-action__icon {
  display: flex;
  width: 50rpx;
  height: 50rpx;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: $pf-color-primary-soft;
}

.quick-action__title {
  margin-top: 10rpx;
  color: $pf-color-text;
  font-size: 23rpx;
  font-weight: 600;
}

.production-list {
  padding: 4rpx 0;
}

.production-row {
  display: flex;
  min-height: 120rpx;
  align-items: center;
  padding: 0 22rpx;
}

.production-row + .production-row,
.record-row + .record-row {
  border-top: 1rpx solid $pf-color-divider;
}

.production-row__icon,
.record-row__icon,
.production-empty__icon {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  background: $pf-color-primary-soft;
}

.production-row__icon--muted {
  background: $pf-color-surface-muted;
}

.production-row__copy {
  min-width: 0;
  flex: 1;
  margin: 0 16rpx;
}

.production-row__heading {
  display: flex;
  min-width: 0;
  align-items: center;
}

.production-row__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-row__variety {
  overflow: hidden;
  max-width: 180rpx;
  flex-shrink: 1;
  margin-left: 12rpx;
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 19rpx;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-row__variety--muted {
  background: $pf-color-surface-muted;
  color: $pf-color-text-secondary;
}

.production-row__meta {
  overflow: hidden;
  margin-top: 7rpx;
  color: $pf-color-text-muted;
  font-size: 20rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-row__tail {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 12rpx;
}

.status-chip {
  padding: 5rpx 10rpx;
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 19rpx;
  line-height: 1.3;
}

.status-chip--ended {
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
}

.production-empty {
  display: flex;
  min-height: 116rpx;
  align-items: center;
  padding: 0 22rpx;
}

.production-empty__copy {
  min-width: 0;
  flex: 1;
  margin: 0 16rpx;
}

.production-empty__title,
.record-row__title {
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 620;
}

.production-empty__meta,
.record-row__meta {
  overflow: hidden;
  margin-top: 7rpx;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-heading {
  margin-top: $pf-space-5;
}

.record-list {
  padding: 4rpx 0;
}

.record-row {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 22rpx;
}

.record-row__copy {
  min-width: 0;
  flex: 1;
  margin: 0 16rpx;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: $pf-space-3 $pf-space-page-x 0;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
