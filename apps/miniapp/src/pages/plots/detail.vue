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
        <text v-if="canEdit" class="plot-heading__action" @tap="openEdit">编辑</text>
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
import { formatNumber } from "../../utils/number";

const plotId = ref(0);
const plot = ref<Plot | null>(null);
const farm = ref<Farm | null>(null);
const loading = ref(true);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const canEdit = computed(() => farm.value?.myRole === "OWNER" || farm.value?.myRole === "ADMIN");

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
    farm.value = await getFarm(result.farmId);
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
