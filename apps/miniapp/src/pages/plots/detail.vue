<template>
  <view class="pf-page plot-detail-page">
    <view v-if="loading" class="state-card">
      <uv-loading-icon mode="circle" color="#286B46" />
      <text>正在加载地块</text>
    </view>

    <view v-else-if="loadError" class="state-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadPlot"
        >重试</uv-button
      >
    </view>

    <view v-else-if="plot" class="pf-page-content">
      <view class="plot-header">
        <view class="plot-header__top">
          <view class="plot-header__copy">
            <text class="plot-header__name">{{ plot.name }}</text>
            <text class="plot-header__meta"
              >{{ plotTypeLabel(plot.type) }} · 创建于
              {{ formatDate(plot.createdAt) }}</text
            >
          </view>
          <view
            v-if="canEdit"
            class="plot-header__edit pf-tappable"
            @tap="openEdit"
          >
            <uv-icon name="edit-pen" size="13" color="#286B46" />
            <text>编辑</text>
          </view>
        </view>

        <view class="plot-header__divider" />

        <view class="plot-header__metrics">
          <view class="plot-header__metric">
            <text class="plot-header__metric-label">地块面积</text>
            <view v-if="areaDisplay" class="plot-header__metric-value">
              <text>{{ areaDisplay.value }}</text>
              <text v-if="areaDisplay.unit" class="plot-header__metric-unit">{{
                areaDisplay.unit
              }}</text>
            </view>
            <text v-else class="plot-header__metric-missing">未填写</text>
          </view>
          <text
            v-if="activeProductions.length"
            class="status-chip status-chip--active"
            >{{ activeProductions.length }} 批进行中</text
          >
          <text v-else class="status-chip">空闲</text>
        </view>
      </view>

      <view class="quick-actions">
        <view
          v-if="canManageProductions"
          class="quick-action pf-tappable"
          @tap="openCreateProduction"
        >
          <PfBusinessIcon name="sprout" size="compact" variant="plain" />
          <text class="quick-action__title">开始种养</text>
        </view>
        <view
          v-if="canManageOperations"
          class="quick-action pf-tappable"
          @tap="openCreateOperation"
        >
          <PfBusinessIcon name="shovel" size="compact" variant="plain" />
          <text class="quick-action__title">记农事</text>
        </view>
        <view
          v-if="canManageHarvests"
          class="quick-action pf-tappable"
          :class="{ 'quick-action--disabled': !activeProductions.length }"
          @tap="openCreateHarvest"
        >
          <PfBusinessIcon
            name="shopping-basket"
            size="compact"
            variant="plain"
            :muted="!activeProductions.length"
          />
          <text class="quick-action__title">记收获</text>
        </view>
      </view>

      <view class="pf-section-heading">
        <text class="pf-section-title">当前种养</text>
        <text class="pf-section-note">{{
          activeProductions.length
            ? `进行中 ${activeProductions.length} 批`
            : "地块空闲"
        }}</text>
      </view>

      <view v-if="activeProductions.length" class="production-list">
        <view
          v-for="item in activeProductions"
          :key="item.id"
          class="production-row pf-tappable"
          @tap="openProduction(item.id)"
        >
          <view class="production-row__copy">
            <view class="production-row__heading">
              <text class="production-row__name">{{ item.speciesName }}</text>
              <text v-if="item.variety" class="production-row__variety">{{
                item.variety
              }}</text>
            </view>
            <text class="production-row__meta">{{ activeMeta(item) }}</text>
          </view>
          <PfRowChevron />
        </view>
      </view>
      <PfEmptyState
        v-else
        variant="inline"
        icon="sprout"
        title="这个地块目前空闲"
        :action-text="canManageProductions ? '去开始' : ''"
        action-type="text"
        @action="openCreateProduction"
      />

      <template v-if="endedProductions.length">
        <view class="pf-section-heading">
          <text class="pf-section-title">历史种养</text>
          <text class="pf-section-note"
            >共 {{ endedProductions.length }} 批</text
          >
        </view>
        <view class="production-list">
          <view
            v-for="item in endedProductions"
            :key="item.id"
            class="production-row pf-tappable"
            @tap="openProduction(item.id)"
          >
            <view class="production-row__copy">
              <text class="production-row__name production-row__name--muted">{{
                item.speciesName
              }}</text>
              <text class="production-row__meta">{{ endedMeta(item) }}</text>
            </view>
            <text class="status-chip status-chip--ended">已结束</text>
            <PfRowChevron />
          </view>
        </view>
      </template>

      <view class="pf-section-heading">
        <text class="pf-section-title">生产记录</text>
        <text class="pf-section-note">按记录类型查看</text>
      </view>
      <view class="record-list">
        <view class="record-row pf-tappable" @tap="openOperations">
          <PfBusinessIcon name="shovel" />
          <text class="record-row__title">农事记录</text>
          <text class="record-row__count">共 {{ operationTotal }} 条</text>
          <PfRowChevron />
        </view>
        <view class="record-row pf-tappable" @tap="openHarvests">
          <PfBusinessIcon name="shopping-basket" />
          <text class="record-row__title">收获记录</text>
          <text class="record-row__count">共 {{ harvestTotal }} 条</text>
          <PfRowChevron />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfEmptyState from "../../components/PfEmptyState.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { getFarm, type Farm } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import { getPlotDetail, type Plot, type PlotType } from "../../services/plot";
import type { Production } from "../../services/production";
import type { IndividualUnit } from "../../services/species";
import { formatNumber } from "../../utils/number";

const plotId = ref(0);
const plot = ref<Plot | null>(null);
const farm = ref<Farm | null>(null);
const loading = ref(true);
const loadError = ref("");
const activeProductions = ref<Production[]>([]);
const endedProductions = ref<Production[]>([]);
const operationTotal = ref(0);
const harvestTotal = ref(0);
const canEdit = computed(
  () => farm.value?.myRole === "OWNER" || farm.value?.myRole === "ADMIN",
);
const canManageProductions = computed(() => Boolean(farm.value?.myRole));
const canManageOperations = computed(() => Boolean(farm.value?.myRole));
const canManageHarvests = computed(() => Boolean(farm.value?.myRole));
const areaDisplay = computed(() => {
  const current = plot.value;
  if (
    !current ||
    current.areaValue === null ||
    current.areaValue === undefined ||
    !current.areaUnit
  )
    return null;
  const units: Record<string, string> = {
    MU: "亩",
    SQUARE_METER: "平方米",
    HECTARE: "公顷",
  };
  return {
    value: formatNumber(current.areaValue),
    unit: units[current.areaUnit] || "",
  };
});

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

function formatDate(value: string): string {
  const date = new Date(
    value.replace(" ", "T") + (value.includes("Z") ? "" : "Z"),
  );
  if (Number.isNaN(date.getTime())) return "未知";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function formatShortDate(value: string | null): string {
  if (!value) return "未知";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function activeMeta(value: Production): string {
  const details = [`${formatShortDate(value.startedOn)}开始`];
  if (value.initialQuantity !== null && value.initialQuantity !== undefined) {
    details.push(
      `初始 ${formatNumber(value.initialQuantity)}${individualUnitLabels[value.individualUnit]}`,
    );
  }
  return details.join(" · ");
}

function endedMeta(value: Production): string {
  const details = [`${formatShortDate(value.startedOn)}开始`];
  if (value.endedOn) details.push(`${formatShortDate(value.endedOn)}结束`);
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
    const detail = await getPlotDetail(plotId.value);
    const farmResult = await getFarm(detail.plot.farmId);
    plot.value = detail.plot;
    farm.value = farmResult;
    activeProductions.value = detail.activeProductions;
    endedProductions.value = detail.endedProductions;
    operationTotal.value = detail.operationTotal;
    harvestTotal.value = detail.harvestTotal;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value =
      error instanceof ApiRequestError
        ? error.message
        : "地块加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openEdit(): void {
  if (plot.value)
    uni.navigateTo({ url: `/pages/plots/edit?plotId=${plot.value.id}` });
}

function openCreateProduction(): void {
  if (plot.value) {
    uni.navigateTo({
      url: `/pages/productions/start?farmId=${plot.value.farmId}&plotId=${plot.value.id}`,
    });
  }
}

function openProduction(productionId: number): void {
  uni.navigateTo({
    url: `/pages/productions/detail?productionId=${productionId}`,
  });
}

function openOperations(): void {
  if (plot.value)
    uni.navigateTo({ url: `/pages/operations/index?plotId=${plot.value.id}` });
}

function openCreateOperation(): void {
  if (plot.value)
    uni.navigateTo({
      url: `/pages/operations/form?plotId=${plot.value.id}&plotLocked=1`,
    });
}

function openHarvests(): void {
  if (plot.value)
    uni.navigateTo({ url: `/pages/harvests/index?plotId=${plot.value.id}` });
}

function openCreateHarvest(): void {
  if (!plot.value) return;
  if (!activeProductions.value.length) {
    uni.showToast({ title: "暂无进行中的种养", icon: "none" });
    return;
  }
  uni.navigateTo({
    url: `/pages/harvests/form?farmId=${plot.value.farmId}&plotId=${plot.value.id}`,
  });
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

/* 地块信息卡 */
.plot-header {
  padding: 28rpx;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.plot-header__top {
  display: flex;
  align-items: center;
}

.plot-header__copy {
  min-width: 0;
  flex: 1;
}

.plot-header__name,
.plot-header__meta,
.plot-header__metric-label,
.plot-header__metric-missing,
.production-row__meta,
.record-row__title,
.record-row__count,
.quick-action__title {
  display: block;
}

.plot-header__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-header__meta {
  overflow: hidden;
  margin-top: 4rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-header__edit {
  display: flex;
  min-height: 60rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  margin-left: 18rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 24rpx;
  font-weight: 600;
}

.plot-header__edit text {
  margin-left: 8rpx;
}

.plot-header__divider {
  height: 1rpx;
  margin: 24rpx 0 22rpx;
  background: $pf-color-divider;
}

.plot-header__metrics {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.plot-header__metric-label {
  color: $pf-color-text-muted;
  font-size: 21rpx;
}

.plot-header__metric-value {
  display: flex;
  align-items: baseline;
  margin-top: 6rpx;
  color: $pf-color-text;
}

.plot-header__metric-value > text:first-child {
  font-size: 46rpx;
  font-weight: 750;
  letter-spacing: -1rpx;
}

.plot-header__metric-unit {
  margin-left: 6rpx;
  font-size: 22rpx;
  font-weight: 550;
}

.plot-header__metric-missing {
  margin-top: 6rpx;
  color: $pf-color-text-secondary;
  font-size: 30rpx;
  font-weight: 600;
}

.status-chip {
  flex-shrink: 0;
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  font-weight: 550;
  line-height: 1.4;
}

.status-chip--active {
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
}

.status-chip--ended {
  margin-right: 12rpx;
}

/* 快捷操作 */
.quick-actions {
  display: flex;
  margin-top: $pf-space-3;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.quick-action {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 26rpx 0 24rpx;
}

.quick-action + .quick-action {
  border-left: 1rpx solid $pf-color-divider;
}

.quick-action__title {
  color: $pf-color-text;
  font-size: 24rpx;
  font-weight: 600;
}

.quick-action--disabled .quick-action__title {
  color: $pf-color-text-muted;
  opacity: 0.75;
}

/* 当前种养 / 历史种养 */
.production-list {
  overflow: hidden;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.production-row {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 22rpx;
}

.production-row + .production-row {
  border-top: 1rpx solid $pf-color-divider;
}

.production-row__copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}

.production-row__heading {
  display: flex;
  min-width: 0;
  align-items: center;
}

.production-row__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-row__name--muted {
  color: $pf-color-text-secondary;
}

.production-row__variety {
  overflow: hidden;
  max-width: 180rpx;
  flex-shrink: 1;
  margin-left: 12rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 19rpx;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-row__meta {
  overflow: hidden;
  margin-top: 7rpx;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 生产记录 */
.record-list {
  overflow: hidden;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.record-row {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 22rpx;
}

.record-row + .record-row {
  border-top: 1rpx solid $pf-color-divider;
}

.record-row__title {
  min-width: 0;
  flex: 1;
  margin-left: 16rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.record-row__count {
  flex-shrink: 0;
  margin-right: 12rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

/* 加载 / 失败态 */
.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: $pf-space-3 $pf-space-page-x 0;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
