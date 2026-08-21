<template>
  <view class="pf-page production-detail-page">
    <view v-if="loading" class="state-card">
      <uv-loading-icon mode="circle" color="#286B46" />
      <text>正在加载种养信息</text>
    </view>

    <view v-else-if="loadError" class="state-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadProduction"
        >重试</uv-button
      >
    </view>

    <view v-else-if="production" class="pf-page-content">
      <view class="production-header">
        <view class="production-header__top">
          <view class="production-header__copy">
            <view class="production-header__heading">
              <text class="production-header__name">{{
                production.speciesName
              }}</text>
              <text
                v-if="production.variety"
                class="production-header__variety"
                >{{ production.variety }}</text
              >
            </view>
            <text class="production-header__meta">{{ headerMeta }}</text>
          </view>
          <view
            v-if="production.status === 'ACTIVE'"
            class="production-header__edit pf-tappable"
            @tap="openEdit"
          >
            <uv-icon name="edit-pen" size="13" color="#286B46" />
            <text>编辑</text>
          </view>
        </view>

        <view class="production-header__divider" />

        <view class="production-header__metrics">
          <view class="production-header__metric">
            <text class="production-header__metric-label">{{
              initialQuantityLabel
            }}</text>
            <view
              v-if="production.initialQuantity !== null"
              class="production-header__metric-value"
            >
              <text>{{ formatNumber(production.initialQuantity) }}</text>
              <text class="production-header__metric-unit">{{
                individualUnitLabel(production.individualUnit)
              }}</text>
            </view>
            <text v-else class="production-header__metric-missing">未填写</text>
          </view>
          <text
            v-if="production.status === 'ACTIVE'"
            class="status-chip status-chip--active"
            >进行中</text
          >
          <text v-else class="status-chip">已结束</text>
        </view>
      </view>

      <template v-if="hasInfoRows">
        <view class="pf-section-heading">
          <text class="pf-section-title">种养信息</text>
        </view>
        <view class="info-card">
          <view v-if="production.plantingStandard" class="info-row">
            <text class="info-label">种植标准</text>
            <text class="info-value">{{
              plantingStandardLabel(production.plantingStandard)
            }}</text>
          </view>
          <view v-if="production.plantingMethod" class="info-row">
            <text class="info-label">种植方式</text>
            <text class="info-value">{{
              plantingMethodLabel(production.plantingMethod)
            }}</text>
          </view>
          <view v-if="production.workMethod" class="info-row">
            <text class="info-label">作业方式</text>
            <text class="info-value">{{
              workMethodLabel(production.workMethod)
            }}</text>
          </view>
          <view v-if="production.expectedHarvestOn" class="info-row">
            <text class="info-label">预计采收时间</text>
            <text class="info-value">{{ production.expectedHarvestOn }}</text>
          </view>
          <view v-if="production.expectedYieldPerMu !== null" class="info-row">
            <text class="info-label">预计亩产</text>
            <text class="info-value"
              >{{ formatNumber(production.expectedYieldPerMu) }} 公斤/亩</text
            >
          </view>
          <view v-if="production.plantSpacingCm !== null" class="info-row">
            <text class="info-label">株间距</text>
            <text class="info-value"
              >{{ formatNumber(production.plantSpacingCm) }} 厘米</text
            >
          </view>
          <view v-if="production.entryAgeDays !== null" class="info-row">
            <text class="info-label">入栏日龄</text>
            <text class="info-value">{{ production.entryAgeDays }} 日</text>
          </view>
          <view v-if="production.remark" class="info-row info-row--stack">
            <text class="info-label">备注</text>
            <text class="info-value">{{ production.remark }}</text>
          </view>
        </view>
      </template>

      <view class="pf-section-heading">
        <text class="pf-section-title">{{ harvestActionLabel }}记录</text>
        <text
          v-if="production.status === 'ACTIVE'"
          class="pf-section-action"
          @tap="openCreateHarvest"
          >记录{{ harvestActionLabel }}</text
        >
      </view>
      <view class="record-list">
        <view class="record-row pf-tappable" @tap="openHarvests">
          <view class="record-row__icon">
            <image
              class="record-row__image"
              src="/static/icons/home/harvest.png"
              mode="aspectFit"
            />
          </view>
          <text class="record-row__title"
            >查看{{ harvestActionLabel }}记录</text
          >
          <PfRowChevron />
        </view>
      </view>

      <view
        v-if="production.status === 'ACTIVE'"
        class="end-card pf-tappable"
        @tap="openEndProduction"
      >
        <view class="end-card__icon">
          <uv-icon name="checkmark-circle" size="18" color="#286B46" />
        </view>
        <text class="end-card__title">{{ endActionLabel }}</text>
        <PfRowChevron />
      </view>

      <template v-if="production.status === 'ACTIVE'">
        <view class="pf-section-heading">
          <text class="pf-section-title">危险操作</text>
        </view>
        <view class="danger-card pf-tappable" @tap="confirmDelete">
          <view class="danger-card__icon">
            <uv-icon name="close-circle" size="18" color="#A9433B" />
          </view>
          <text class="danger-card__title">删除种养记录</text>
          <PfRowChevron />
        </view>
      </template>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import {
  deleteProduction,
  getProduction,
  type PlantingMethod,
  type PlantingStandard,
  type Production,
  type WorkMethod,
} from "../../services/production";
import type { IndividualUnit, Industry } from "../../services/species";
import { formatNumber } from "../../utils/number";

const industryLabels: Record<Industry, string> = {
  AGRICULTURE: "农业",
  FORESTRY: "林业",
  LIVESTOCK: "牧业",
  FISHERY: "渔业",
};
const individualUnitLabels: Record<IndividualUnit, string> = {
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只",
  PLANT: "株",
  TAIL: "尾",
};
const plantingStandardLabels: Record<PlantingStandard, string> = {
  NORMAL: "普通",
  GREEN: "绿色",
  ORGANIC: "有机",
};
const plantingMethodLabels: Record<PlantingMethod, string> = {
  TRANSPLANT: "移栽",
  DIRECT_SEEDING: "直播",
};
const workMethodLabels: Record<WorkMethod, string> = {
  MANUAL: "人工",
  MECHANICAL: "机械",
};

const productionId = ref(0);
const production = ref<Production | null>(null);
const loading = ref(true);
const deleting = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const headerMeta = computed(() => {
  const value = production.value;
  if (!value) return "";
  const details = [industryLabel(value.industry), `${value.startedOn} 开始`];
  if (value.endedOn) details.push(`${value.endedOn} 结束`);
  return details.join(" · ");
});
const hasInfoRows = computed(() => {
  const value = production.value;
  return Boolean(
    value &&
    (value.plantingStandard ||
      value.plantingMethod ||
      value.workMethod ||
      value.expectedHarvestOn ||
      value.expectedYieldPerMu !== null ||
      value.plantSpacingCm !== null ||
      value.entryAgeDays !== null ||
      value.remark),
  );
});
const initialQuantityLabel = computed(() => {
  const value = production.value;
  if (value?.industry === "AGRICULTURE" || value?.industry === "FORESTRY") {
    return value.plantingMethod === "DIRECT_SEEDING" ? "播种数量" : "移栽数量";
  }
  return value?.industry === "LIVESTOCK" ? "入栏数量" : "养殖数量";
});
const harvestActionLabel = computed(() => {
  if (production.value?.industry === "LIVESTOCK") return "出栏";
  if (production.value?.industry === "FISHERY") return "捕捞";
  return "采收";
});
const endActionLabel = computed(() => {
  if (
    production.value?.industry === "AGRICULTURE" ||
    production.value?.industry === "FORESTRY"
  ) {
    return "结束种植";
  }
  return "结束养殖";
});

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function industryLabel(value: Industry): string {
  return industryLabels[value];
}

function individualUnitLabel(value: IndividualUnit): string {
  return individualUnitLabels[value];
}

function plantingStandardLabel(value: PlantingStandard): string {
  return plantingStandardLabels[value];
}

function plantingMethodLabel(value: PlantingMethod): string {
  return plantingMethodLabels[value];
}

function workMethodLabel(value: WorkMethod): string {
  return workMethodLabels[value];
}

async function loadProduction(): Promise<void> {
  if (!productionId.value) {
    loadError.value = "种养信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    production.value = await getProduction(productionId.value);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value =
      error instanceof ApiRequestError
        ? error.message
        : "种养信息加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openEdit(): void {
  if (production.value)
    uni.navigateTo({
      url: `/pages/productions/edit?productionId=${production.value.id}`,
    });
}

function openHarvests(): void {
  if (production.value) {
    uni.navigateTo({
      url: `/pages/harvests/index?productionId=${production.value.id}`,
    });
  }
}

function openCreateHarvest(): void {
  if (production.value?.status === "ACTIVE") {
    uni.navigateTo({
      url: `/pages/harvests/form?productionId=${production.value.id}`,
    });
  }
}

function openEndProduction(): void {
  if (production.value?.status === "ACTIVE") {
    uni.navigateTo({
      url: `/pages/productions/end?productionId=${production.value.id}`,
    });
  }
}

function confirmDelete(): void {
  if (!production.value || deleting.value) return;
  uni.showModal({
    title: "删除种养记录？",
    content: "删除后无法恢复，确定要继续吗？",
    confirmColor: "#C96A45",
    success: async (result) => {
      if (!result.confirm || !production.value) return;
      deleting.value = true;
      try {
        await deleteProduction(production.value.id);
        uni.showToast({ title: "已删除", icon: "none" });
        setTimeout(() => uni.navigateBack(), 400);
      } catch (error) {
        if (error instanceof ApiRequestError && error.statusCode === 401) {
          handleUnauthorized();
        } else {
          toastRef.value?.error(
            error instanceof ApiRequestError
              ? error.message
              : "删除失败，请稍后再试",
          );
        }
      } finally {
        deleting.value = false;
      }
    },
  });
}

onLoad((options) => {
  productionId.value = Number(options?.productionId || 0);
});

onShow(() => {
  if (productionId.value && !deleting.value) loadProduction();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.production-detail-page {
  padding-bottom: $pf-space-page-bottom;
}

.production-detail-page .pf-page-content {
  padding-top: $pf-space-3;
}

/* 种养信息卡 */
.production-header {
  padding: 28rpx;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.production-header__top {
  display: flex;
  align-items: center;
}

.production-header__copy {
  min-width: 0;
  flex: 1;
}

.production-header__heading {
  display: flex;
  min-width: 0;
  align-items: center;
}

.production-header__name,
.production-header__meta,
.production-header__metric-label,
.production-header__metric-missing,
.record-row__title,
.end-card__title,
.danger-card__title {
  display: block;
}

.production-header__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-header__variety {
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

.production-header__meta {
  overflow: hidden;
  margin-top: 4rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-header__edit {
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

.production-header__edit text {
  margin-left: 8rpx;
}

.production-header__divider {
  height: 1rpx;
  margin: 24rpx 0 22rpx;
  background: $pf-color-divider;
}

.production-header__metrics {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.production-header__metric-label {
  color: $pf-color-text-muted;
  font-size: 21rpx;
}

.production-header__metric-value {
  display: flex;
  align-items: baseline;
  margin-top: 6rpx;
  color: $pf-color-text;
}

.production-header__metric-value > text:first-child {
  font-size: 46rpx;
  font-weight: 750;
  letter-spacing: -1rpx;
}

.production-header__metric-unit {
  margin-left: 6rpx;
  font-size: 22rpx;
  font-weight: 550;
}

.production-header__metric-missing {
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

/* 种养信息 */
.info-card {
  overflow: hidden;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.info-row {
  display: flex;
  min-height: 92rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 28rpx;
}

.info-row + .info-row {
  border-top: 1rpx solid $pf-color-divider;
}

.info-label {
  color: $pf-color-text-secondary;
  font-size: 25rpx;
}

.info-value {
  max-width: 62%;
  color: $pf-color-text;
  font-size: 25rpx;
  font-weight: 550;
  text-align: right;
}

.info-row--stack {
  flex-direction: column;
  align-items: flex-start;
  gap: 8rpx;
  padding: 24rpx 28rpx;
}

.info-row--stack .info-value {
  max-width: 100%;
  color: $pf-color-text-secondary;
  font-weight: 400;
  line-height: 1.55;
  text-align: left;
}

/* 采收记录 */
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

.record-row__icon {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: $pf-color-primary-soft;
}

.record-row__image {
  width: 44rpx;
  height: 44rpx;
}

.record-row__title {
  min-width: 0;
  flex: 1;
  margin-left: 16rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

/* 结束种养 */
.end-card {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  margin-top: $pf-space-3;
  padding: 0 22rpx;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.end-card__icon {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: $pf-color-primary-soft;
}

.end-card__title {
  flex: 1;
  margin-left: 16rpx;
  color: $pf-color-primary;
  font-size: 27rpx;
  font-weight: 600;
}

/* 危险操作 */
.danger-card {
  display: flex;
  min-height: 112rpx;
  align-items: center;
  padding: 0 22rpx;
  border-radius: 20rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.danger-card__icon {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: $pf-color-danger-soft;
}

.danger-card__title {
  flex: 1;
  margin-left: 16rpx;
  color: $pf-color-danger;
  font-size: 27rpx;
  font-weight: 600;
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
