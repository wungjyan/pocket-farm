<template>
  <view class="pf-page production-detail-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#2F7D4A" />
      <text>正在加载种养信息</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadProduction"
      >
        重试
      </uv-button>
    </view>
    <template v-else-if="production">
      <view class="production-heading">
        <view>
          <text class="production-heading__name">{{ production.speciesName }}</text>
          <text class="production-heading__meta">{{ industryLabel(production.industry) }} · {{ statusLabel(production.status) }}</text>
        </view>
        <text v-if="production.status === 'ACTIVE'" class="production-heading__action" @click="openEdit">编辑</text>
      </view>

      <view class="info-card pf-card">
        <view class="info-row">
          <text class="info-label">{{ startedOnLabel }}</text>
          <text class="info-value">{{ production.startedOn }}</text>
        </view>
        <view v-if="production.variety" class="info-row">
          <text class="info-label">品种</text>
          <text class="info-value">{{ production.variety }}</text>
        </view>
        <view v-if="production.plantingStandard" class="info-row">
          <text class="info-label">种植标准</text>
          <text class="info-value">{{ plantingStandardLabel(production.plantingStandard) }}</text>
        </view>
        <view v-if="production.plantingMethod" class="info-row">
          <text class="info-label">种植方式</text>
          <text class="info-value">{{ plantingMethodLabel(production.plantingMethod) }}</text>
        </view>
        <view v-if="production.workMethod" class="info-row">
          <text class="info-label">作业方式</text>
          <text class="info-value">{{ workMethodLabel(production.workMethod) }}</text>
        </view>
      </view>

      <view v-if="hasAdditionalInfo" class="section-label">更多信息</view>
      <view v-if="hasAdditionalInfo" class="info-card pf-card">
        <view v-if="production.expectedHarvestOn" class="info-row">
          <text class="info-label">预计采收时间</text>
          <text class="info-value">{{ production.expectedHarvestOn }}</text>
        </view>
        <view v-if="production.expectedYieldPerMu !== null" class="info-row">
          <text class="info-label">预计亩产</text>
          <text class="info-value">{{ formatNumber(production.expectedYieldPerMu) }} 公斤/亩</text>
        </view>
        <view v-if="production.initialQuantity !== null" class="info-row">
          <text class="info-label">{{ initialQuantityLabel }}</text>
          <text class="info-value">{{ formatNumber(production.initialQuantity) }} {{ individualUnitLabel(production.individualUnit) }}</text>
        </view>
        <view v-if="production.plantSpacingCm !== null" class="info-row">
          <text class="info-label">株间距</text>
          <text class="info-value">{{ formatNumber(production.plantSpacingCm) }} 厘米</text>
        </view>
        <view v-if="production.entryAgeDays !== null" class="info-row">
          <text class="info-label">入栏日龄</text>
          <text class="info-value">{{ production.entryAgeDays }} 日</text>
        </view>
        <view v-if="production.remark" class="info-row info-row--remark">
          <text class="info-label">备注</text>
          <text class="info-value">{{ production.remark }}</text>
        </view>
      </view>

      <view v-if="production.status === 'ACTIVE'" class="danger-section">
        <view class="section-label">危险操作</view>
        <view class="danger-card pf-card" @click="confirmDelete">
          <view class="danger-icon"><uv-icon name="close-circle" size="20" color="#C96A45" /></view>
          <text class="danger-title">删除种养记录</text>
          <uv-icon name="arrow-right" size="17" color="#C96A45" />
        </view>
      </view>
    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import {
  deleteProduction,
  getProduction,
  type PlantingMethod,
  type PlantingStandard,
  type Production,
  type ProductionStatus,
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
const workMethodLabels: Record<WorkMethod, string> = { MANUAL: "人工", MECHANICAL: "机械" };

const productionId = ref(0);
const production = ref<Production | null>(null);
const loading = ref(true);
const deleting = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const hasAdditionalInfo = computed(() => {
  const value = production.value;
  return Boolean(
    value &&
      (value.expectedHarvestOn ||
        value.expectedYieldPerMu !== null ||
        value.initialQuantity !== null ||
        value.plantSpacingCm !== null ||
        value.entryAgeDays !== null ||
        value.remark),
  );
});
const startedOnLabel = computed(() => {
  const value = production.value;
  if (value?.industry === "AGRICULTURE" || value?.industry === "FORESTRY") {
    return value.plantingMethod === "DIRECT_SEEDING" ? "播种时间" : "移栽时间";
  }
  return value?.industry === "LIVESTOCK" ? "入栏时间" : "养殖时间";
});
const initialQuantityLabel = computed(() => {
  const value = production.value;
  if (value?.industry === "AGRICULTURE" || value?.industry === "FORESTRY") {
    return value.plantingMethod === "DIRECT_SEEDING" ? "播种数量" : "移栽数量";
  }
  return value?.industry === "LIVESTOCK" ? "入栏数量" : "养殖数量";
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

function statusLabel(value: ProductionStatus): string {
  return value === "ACTIVE" ? "进行中" : "已结束";
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
    loadError.value = error instanceof ApiRequestError ? error.message : "种养信息加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openEdit(): void {
  if (production.value) uni.navigateTo({ url: `/pages/productions/edit?productionId=${production.value.id}` });
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
          toastRef.value?.error(error instanceof ApiRequestError ? error.message : "删除失败，请稍后再试");
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
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.production-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 4rpx 28rpx;
}

.production-heading__name,
.production-heading__meta {
  display: block;
}

.production-heading__name {
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
}

.production-heading__meta {
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.production-heading__action {
  flex-shrink: 0;
  margin-left: 24rpx;
  color: $pf-color-primary;
  font-size: 25rpx;
}

.section-label {
  margin: 38rpx 8rpx 14rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 600;
}

.info-card {
  padding: 8rpx 24rpx;
}

.info-row {
  display: flex;
  min-height: 92rpx;
  align-items: center;
  justify-content: space-between;
}

.info-row + .info-row {
  border-top: 1rpx solid $pf-color-divider;
}

.info-row--remark {
  align-items: flex-start;
  padding: 24rpx 0;
}

.info-label {
  color: $pf-color-text-secondary;
  font-size: 25rpx;
}

.info-value {
  max-width: 65%;
  color: $pf-color-text;
  font-size: 25rpx;
  text-align: right;
}

.danger-section {
  margin-top: 6rpx;
}

.danger-card {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  padding: 0 22rpx;
  border-color: #f1d9d0;
}

.danger-icon {
  display: flex;
  width: 52rpx;
  height: 52rpx;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: #fff1ec;
}

.danger-title {
  flex: 1;
  margin: 0 18rpx;
  color: #c96a45;
  font-size: 27rpx;
  font-weight: 500;
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
