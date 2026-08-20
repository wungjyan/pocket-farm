<template>
  <view class="pf-page operations-page">
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
      <view class="page-intro">
        <view>
          <text class="page-title">农事记录</text>
          <text class="page-description">{{ plot.name }} · 共 {{ operations.length }} 条</text>
        </view>
        <text class="page-action" @click="openCreate">记农事</text>
      </view>

      <view v-if="operations.length" class="operation-list">
        <view
          v-for="operation in operations"
          :key="operation.id"
          class="operation-card pf-card"
          :class="{ 'operation-card--locked': isLocked(operation) }"
          @click="openEdit(operation)"
        >
          <view class="operation-icon"><uv-icon :name="operationIcon(operation.operationType.code)" size="21" color="#2F7D4A" /></view>
          <view class="operation-copy">
            <view class="operation-title-line">
              <text class="operation-name">{{ operation.operationType.name }}</text>
              <text v-if="isLocked(operation)" class="operation-lock">已锁定</text>
            </view>
            <text class="operation-meta">{{ operationDateLabel(operation.operatedAt) }} · {{ productionLabel(operation) }}</text>
            <text class="operation-meta">操作人：{{ memberName(operation.operatorId) }}{{ creatorLabel(operation) }}</text>
          </view>
          <view v-if="!isLocked(operation)" class="operation-delete" @click.stop="confirmDelete(operation)">
            <uv-icon name="trash" size="18" color="#C96A45" />
          </view>
          <uv-icon v-else name="lock" size="17" color="#929A93" />
        </view>
      </view>
      <view v-else class="empty-card pf-card">
        <uv-icon name="calendar" size="30" color="#929A93" />
        <text class="empty-card__title">还没有农事记录</text>
        <text class="empty-card__description">从一次翻耕、施肥或灌溉开始记录生产现场。</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 24rpx; border-radius: 12rpx;"
          @click="openCreate"
        >
          记农事
        </uv-button>
      </view>
    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { getFarmMembers, type FarmMember } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import {
  deleteOperation,
  getPlotOperations,
  type FarmOperation,
} from "../../services/operation";
import { getPlot, type Plot } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";

const operationIcons: Record<string, string> = {
  FERTILIZE: "bag",
  IRRIGATE: "clock",
  PESTICIDE: "warning",
  DISINFECT: "shield",
  CHANGE_WATER: "reload",
};

const plotId = ref(0);
const plot = ref<Plot | null>(null);
const operations = ref<FarmOperation[]>([]);
const activeProductions = ref<Production[]>([]);
const members = ref<FarmMember[]>([]);
const loading = ref(true);
const loadError = ref("");
const deletingId = ref(0);
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const activeProductionIds = computed(() => new Set(activeProductions.value.map((item) => item.id)));

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function operationIcon(value: string): string {
  return operationIcons[value] || "calendar";
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
    const [operationPage, productionPage, memberPage] = await Promise.all([
      getPlotOperations(plotResult.id),
      getPlotProductions(plotResult.id, "ACTIVE"),
      getFarmMembers(plotResult.farmId),
    ]);
    plot.value = plotResult;
    operations.value = operationPage.items;
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

function openCreate(): void {
  if (plot.value) uni.navigateTo({ url: `/pages/operations/form?plotId=${plot.value.id}&plotLocked=1` });
}

function openEdit(operation: FarmOperation): void {
  if (isLocked(operation) || !plot.value) return;
  uni.navigateTo({ url: `/pages/operations/form?plotId=${plot.value.id}&operationId=${operation.id}&plotLocked=1` });
}

function confirmDelete(operation: FarmOperation): void {
  if (deletingId.value || isLocked(operation)) return;
  uni.showModal({
    title: "删除农事记录？",
    content: "删除后无法恢复，确定要继续吗？",
    confirmColor: "#C96A45",
    success: async (result) => {
      if (!result.confirm) return;
      deletingId.value = operation.id;
      try {
        await deleteOperation(operation.id);
        operations.value = operations.value.filter((item) => item.id !== operation.id);
        uni.showToast({ title: "已删除", icon: "none" });
      } catch (error) {
        if (error instanceof ApiRequestError && error.statusCode === 401) {
          handleUnauthorized();
        } else {
          toastRef.value?.error(error instanceof ApiRequestError ? error.message : "删除失败，请稍后再试");
        }
      } finally {
        deletingId.value = 0;
      }
    },
  });
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
});

onShow(() => {
  if (plotId.value && !deletingId.value) loadOperations();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.operations-page {
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.page-intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 4rpx 28rpx;
}

.page-title,
.page-description {
  display: block;
}

.page-title {
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
}

.page-description {
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.page-action {
  color: $pf-color-primary;
  font-size: 26rpx;
}

.operation-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.operation-card {
  display: flex;
  min-height: 126rpx;
  align-items: center;
  padding: 16rpx 20rpx;
}

.operation-card--locked {
  background: $pf-color-surface-muted;
}

.operation-icon {
  display: flex;
  width: 60rpx;
  height: 60rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  background: $pf-color-primary-soft;
}

.operation-copy {
  min-width: 0;
  flex: 1;
  margin: 0 16rpx;
}

.operation-title-line {
  display: flex;
  align-items: center;
}

.operation-name {
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 600;
}

.operation-lock {
  margin-left: 10rpx;
  padding: 3rpx 8rpx;
  border-radius: 8rpx;
  background: #e2e6e0;
  color: $pf-color-text-muted;
  font-size: 19rpx;
}

.operation-meta {
  display: block;
  margin-top: 5rpx;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-delete {
  display: flex;
  width: 48rpx;
  height: 48rpx;
  align-items: center;
  justify-content: center;
}

.empty-card,
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

.empty-card__title,
.empty-card__description {
  display: block;
}

.empty-card__title {
  margin-top: 14rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.empty-card__description {
  margin-top: 10rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  line-height: 1.5;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
