<template>
  <view class="pf-page operation-detail-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#286B46" />
      <text>正在加载农事记录</text>
    </view>

    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadDetail"
      >
        重试
      </uv-button>
    </view>

    <view v-else-if="operation && plot" class="pf-page-content">
      <view class="detail-card pf-card">
        <view class="detail-heading">
          <text class="detail-title">{{ operation.operationType.name }}</text>
        </view>

        <view class="detail-list">
          <view class="detail-row">
            <text class="detail-label">操作时间</text>
            <text class="detail-value">{{ operationDateLabel(operation.operatedAt) }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">地块</text>
            <text class="detail-value">{{ plot.name }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">关联种养</text>
            <text class="detail-value">{{ productionLabel }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">作业方式</text>
            <text class="detail-value">{{ workMethodLabel(operation.workMethod) }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">操作人</text>
            <text class="detail-value">{{ memberName(operation.operatorId) }}</text>
          </view>
          <view v-if="operation.createdBy !== operation.operatorId" class="detail-row">
            <text class="detail-label">记录人</text>
            <text class="detail-value">{{ memberName(operation.createdBy) }}</text>
          </view>
          <view v-if="operation.remark" class="detail-row detail-row--stack">
            <text class="detail-label">备注</text>
            <text class="detail-value">{{ operation.remark }}</text>
          </view>
        </view>
      </view>

      <view v-if="!readOnly" class="action-grid">
        <button
          class="action-button action-button--primary"
          hover-class="action-button--primary-pressed"
          @tap="openEdit"
        >
          编辑农事记录
        </button>
        <button
          class="action-button action-button--danger"
          hover-class="action-button--danger-pressed"
          @tap="confirmDelete"
        >
          删除农事记录
        </button>
      </view>
    </view>

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
  getOperation,
  type FarmOperation,
} from "../../services/operation";
import { getPlot, type Plot } from "../../services/plot";
import {
  getProduction,
  type Production,
  type WorkMethod,
} from "../../services/production";

const workMethodLabels: Record<WorkMethod, string> = {
  MANUAL: "人工",
  MECHANICAL: "机械",
};

const operationId = ref(0);
const operation = ref<FarmOperation | null>(null);
const plot = ref<Plot | null>(null);
const production = ref<Production | null>(null);
const members = ref<FarmMember[]>([]);
const loading = ref(true);
const deleting = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);

const readOnly = computed(() => {
  const value = operation.value;
  if (!value || value.productionId === null) return false;
  return production.value?.status !== "ACTIVE";
});

const productionLabel = computed(() => {
  if (operation.value?.productionId === null) return "整个地块";
  const value = production.value;
  if (!value) return "关联种养";
  return `${value.speciesName}${value.variety ? ` · ${value.variety}` : ""}`;
});

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function operationDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function workMethodLabel(value: WorkMethod): string {
  return workMethodLabels[value];
}

function memberName(userId: number): string {
  return members.value.find((member) => member.userId === userId)?.nickname?.trim() || "未设置昵称";
}

async function loadDetail(): Promise<void> {
  if (!operationId.value) {
    loadError.value = "农事记录信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const operationResult = await getOperation(operationId.value);
    const plotResult = await getPlot(operationResult.plotId);
    const [memberPage, productionResult] = await Promise.all([
      getFarmMembers(plotResult.farmId),
      operationResult.productionId
        ? getProduction(operationResult.productionId)
        : Promise.resolve(null),
    ]);
    operation.value = operationResult;
    plot.value = plotResult;
    production.value = productionResult;
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

function openEdit(): void {
  if (!operation.value || !plot.value || readOnly.value) return;
  uni.navigateTo({
    url: `/pages/operations/form?plotId=${plot.value.id}&operationId=${operation.value.id}&plotLocked=1`,
  });
}

function confirmDelete(): void {
  if (!operation.value || readOnly.value || deleting.value) return;
  uni.showModal({
    title: "删除农事记录？",
    content: "删除后无法恢复，确定要继续吗？",
    confirmColor: "#C96A45",
    success: async (result) => {
      if (!result.confirm || !operation.value) return;
      deleting.value = true;
      try {
        await deleteOperation(operation.value.id);
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
  operationId.value = Number(options?.operationId || 0);
});

onShow(() => {
  if (operationId.value && !deleting.value) loadDetail();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.operation-detail-page {
  padding-bottom: $pf-space-page-bottom;
}

.operation-detail-page .pf-page-content {
  padding-top: $pf-space-3;
}

.detail-card {
  padding: 28rpx;
}

.detail-heading {
  display: flex;
  align-items: center;
  padding-bottom: $pf-space-3;
  border-bottom: 1rpx solid $pf-color-divider;
}

.detail-title {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 34rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: $pf-space-4;
  padding: $pf-space-3 0;
  border-bottom: 1rpx solid $pf-color-divider;
}

.detail-row:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.detail-row--stack {
  flex-direction: column;
  gap: $pf-space-2;
}

.detail-label {
  flex-shrink: 0;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  line-height: 1.45;
}

.detail-value {
  min-width: 0;
  color: $pf-color-text;
  font-size: 24rpx;
  line-height: 1.45;
  text-align: right;
  word-break: break-all;
}

.detail-row--stack .detail-value {
  text-align: left;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: $pf-space-2;
  margin-top: $pf-space-4;
}

.action-button {
  display: flex;
  width: 100%;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  padding: 0 12rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  color: $pf-color-text;
  font-size: 25rpx;
  font-weight: 600;
  line-height: 1.25;
}

.action-button::after {
  border: 0;
}

.action-button--primary {
  border-color: $pf-color-primary-soft;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
}

.action-button--primary-pressed,
.action-button--danger-pressed {
  opacity: 0.72;
}

.action-button--danger {
  border-color: transparent;
  background: $pf-color-danger-soft;
  color: $pf-color-danger;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: $pf-space-3 $pf-space-page-x 0;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  text-align: center;
}

.state-card text {
  margin-top: $pf-space-2;
}
</style>
