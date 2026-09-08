<template>
  <view class="pf-page operations-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#2F7D4A" />
        <text>正在加载农事记录</text>
      </view>

      <view v-else-if="loadError" class="state-card pf-card">
        <uv-icon name="warning" size="28" color="#C96A45" />
        <text>{{ loadError }}</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 22rpx; border-radius: 12rpx;"
          @click="loadOperations"
        >
          重试
        </uv-button>
      </view>

      <template v-else-if="plot">
        <view class="page-toolbar">
          <view class="page-context">
            <view class="page-context__plot">
              <text class="page-context__label">地块</text>
              <text class="page-context__value">{{ plot.name }}</text>
            </view>
            <text class="page-context__separator">·</text>
            <view class="page-context__count">
              <text class="page-context__label">农事记录共</text>
              <text class="page-context__value">{{ formatNumber(totalCount) }}</text>
              <text class="page-context__label">条</text>
            </view>
          </view>
          <view class="page-action pf-tappable" @tap="openCreate">
            <text>记农事</text>
          </view>
        </view>

        <view v-if="operations.length" class="operation-list">
          <view
            v-for="operation in operations"
            :key="operation.id"
            class="operation-card pf-card pf-tappable"
            @tap="openDetail(operation)"
          >
            <view class="operation-copy">
              <view class="operation-title-line">
                <text class="operation-name">{{ operation.operationType.name }}</text>
                <text v-if="isLocked(operation)" class="operation-status">种养已结束</text>
              </view>
              <text class="operation-meta">{{ operationDateLabel(operation.operatedAt) }} · {{ productionLabel(operation) }}</text>
              <text class="operation-meta">操作人：{{ memberName(operation.operatorId) }}{{ creatorLabel(operation) }}</text>
            </view>
            <PfRowChevron />
          </view>
          <uv-load-more v-if="hasMore || loadingMore" :status="loadingMore ? 'loading' : 'nomore'" icon-color="#2F7D4A" color="#7F8B82" />
        </view>
        <PfEmptyState v-else icon="shovel" title="还没有农事记录" />
      </template>
    </view>
    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onReachBottom, onShow } from "@dcloudio/uni-app";
import PfEmptyState from "../../components/PfEmptyState.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { getFarmMembers, type FarmMember } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import {
  getPlotOperations,
  type FarmOperation,
} from "../../services/operation";
import { getPlot, type Plot } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import { formatNumber } from "../../utils/number";

const PAGE_SIZE = 20;
const plotId = ref(0);
const plot = ref<Plot | null>(null);
const operations = ref<FarmOperation[]>([]);
const activeProductions = ref<Production[]>([]);
const members = ref<FarmMember[]>([]);
const loading = ref(true);
const loadError = ref("");
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const totalCount = ref(0);
const currentPage = ref(1);
const hasMore = ref(false);
const loadingMore = ref(false);
const activeProductionIds = computed(() => new Set(activeProductions.value.map((item) => item.id)));

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function operationDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function memberName(userId: number): string {
  return members.value.find((member) => member.userId === userId)?.nickname?.trim() || "未设置昵称";
}

function productionLabel(operation: FarmOperation): string {
  if (operation.productionId === null) return "整个地块";
  const production = activeProductions.value.find((item) => item.id === operation.productionId);
  return production ? production.speciesName : "关联种养";
}

function creatorLabel(operation: FarmOperation): string {
  return operation.createdBy === operation.operatorId ? "" : ` · 记录人：${memberName(operation.createdBy)}`;
}

function isLocked(operation: FarmOperation): boolean {
  return operation.productionId !== null && !activeProductionIds.value.has(operation.productionId);
}

async function fetchOperationPage(page: number): Promise<void> {
  const operationPage = await getPlotOperations(plotId.value, page, PAGE_SIZE);
  totalCount.value = operationPage.total;
  operations.value = page === 1 ? operationPage.items : [...operations.value, ...operationPage.items];
  currentPage.value = page;
  hasMore.value = operations.value.length < operationPage.total;
}

async function loadOperations(): Promise<void> {
  if (!plotId.value) {
    loadError.value = "地块信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const plotResult = await getPlot(plotId.value);
    plot.value = plotResult;
    const [, productionPage, memberPage] = await Promise.all([
      fetchOperationPage(1),
      getPlotProductions(plotResult.id, "ACTIVE"),
      getFarmMembers(plotResult.farmId),
    ]);
    activeProductions.value = productionPage.items;
    members.value = memberPage.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "农事记录加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

async function loadMoreOperations(): Promise<void> {
  if (loading.value || loadingMore.value || !hasMore.value || loadError.value) return;
  loadingMore.value = true;
  try {
    await fetchOperationPage(currentPage.value + 1);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({
      type: "default",
      message: error instanceof ApiRequestError ? error.message : "更多记录加载失败",
    });
  } finally {
    loadingMore.value = false;
  }
}

function openCreate(): void {
  if (plot.value) uni.navigateTo({ url: `/pages/operations/form?plotId=${plot.value.id}&plotLocked=1` });
}

function openDetail(operation: FarmOperation): void {
  uni.navigateTo({ url: `/pages/operations/detail?operationId=${operation.id}` });
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
});

onShow(() => {
  if (plotId.value) loadOperations();
});

onReachBottom(() => {
  void loadMoreOperations();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.page-toolbar {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 4rpx 10rpx;
}

.page-context {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  overflow: hidden;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  white-space: nowrap;
}

.page-context__plot {
  display: flex;
  min-width: 0;
  flex: 0 1 auto;
  align-items: center;
  overflow: hidden;
}

.page-context__value {
  overflow: hidden;
  margin: 0 $pf-space-1;
  color: $pf-color-primary;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-context__plot .page-context__value {
  min-width: 0;
  flex: 1;
}

.page-context__separator {
  flex-shrink: 0;
  margin-right: $pf-space-1;
  color: $pf-color-text-muted;
}

.page-context__count {
  display: flex;
  align-items: center;
}

.page-context__count,
.page-context__label {
  flex-shrink: 0;
}

.page-action {
  display: flex;
  min-height: 88rpx;
  flex-shrink: 0;
  align-items: center;
  margin-left: $pf-space-3;
  padding: 0 $pf-space-1;
  color: $pf-color-primary;
  font-size: 25rpx;
  font-weight: 600;
}

.operation-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.operation-card {
  display: flex;
  align-items: center;
  padding: $pf-space-3;
}

.operation-copy {
  min-width: 0;
  flex: 1;
  margin-right: $pf-space-2;
}

.operation-title-line {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.operation-name {
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
}

.operation-status {
  padding: 3rpx 8rpx;
  border-radius: 8rpx;
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
  font-size: 19rpx;
}

.operation-meta {
  display: block;
  margin-top: $pf-space-1;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-title-line + .operation-meta {
  margin-top: $pf-space-2;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  text-align: center;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
