<template>
  <view class="pf-page operation-detail-page">
    <view v-if="loading" class="state-card">
      <uv-loading-icon mode="circle" color="#006C49" />
      <text>正在加载农事记录</text>
    </view>

    <view v-else-if="loadError" class="state-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 16rpx;"
        @click="loadDetail"
      >
        重试
      </uv-button>
    </view>

    <view v-else-if="operation && plot" class="pf-page-content">
      <view class="detail-summary">
        <view class="detail-summary__top">
          <view class="detail-summary__copy">
            <text class="detail-summary__title">{{
              operation.operationType.name
            }}</text>
            <text class="detail-summary__meta">{{
              operationDateLabel(operation.operatedAt)
            }}</text>
          </view>
          <view
            v-if="!readOnly"
            class="detail-summary__edit pf-tappable"
            @tap="openEdit"
          >
            <uv-icon name="edit-pen" size="14" color="#006C49" />
            <text>编辑</text>
          </view>
        </view>
        <view class="detail-summary__divider" />
        <view class="detail-summary__context">
          <view class="detail-summary__field">
            <text class="detail-summary__label">地块</text>
            <text class="detail-summary__value">{{ plot.name }}</text>
          </view>
          <view class="detail-summary__field">
            <text class="detail-summary__label">关联种养</text>
            <text class="detail-summary__value">{{ productionLabel }}</text>
          </view>
        </view>
      </view>

      <view class="pf-section-heading">
        <text class="pf-section-title">农事信息</text>
      </view>
      <view class="detail-list">
        <view class="detail-row">
          <text class="detail-label">作业方式</text>
          <text class="detail-value">{{
            workMethodLabel(operation.workMethod)
          }}</text>
        </view>
        <view class="detail-row">
          <text class="detail-label">操作人</text>
          <text class="detail-value">{{
            memberName(operation.operatorId)
          }}</text>
        </view>
        <view
          v-if="operation.createdBy !== operation.operatorId"
          class="detail-row"
        >
          <text class="detail-label">记录人</text>
          <text class="detail-value">{{
            memberName(operation.createdBy)
          }}</text>
        </view>
        <view v-if="operation.remark" class="detail-row detail-row--stack">
          <text class="detail-label">备注</text>
          <text class="detail-value">{{ operation.remark }}</text>
        </view>
      </view>

      <button
        v-if="!readOnly"
        class="delete-button"
        hover-class="delete-button--pressed"
        @tap="confirmDelete"
      >
        删除农事记录
      </button>
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
    confirmColor: "#A9433B",
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
  padding-top: $pf-space-4;
}

.detail-summary {
  padding: $pf-space-4 28rpx 28rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.detail-summary__top {
  display: flex;
  align-items: flex-start;
}

.detail-summary__copy {
  min-width: 0;
  flex: 1;
}

.detail-summary__title,
.detail-summary__meta,
.detail-summary__label,
.detail-summary__value {
  display: block;
}

.detail-summary__title {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 40rpx;
  font-weight: $pf-font-weight-bold;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-summary__meta {
  margin-top: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  line-height: 1.45;
}

.detail-summary__edit {
  display: flex;
  min-width: 112rpx;
  min-height: 72rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-left: 18rpx;
  padding: 0 $pf-space-2;
  border-radius: $pf-radius-control;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
}

.detail-summary__edit text {
  margin-left: $pf-space-1;
}

.detail-summary__divider {
  height: 1rpx;
  margin: 28rpx 0 $pf-space-3;
  background: $pf-color-divider;
}

.detail-summary__context {
  display: flex;
  min-width: 0;
}

.detail-summary__field {
  min-width: 0;
  flex: 1;
}

.detail-summary__field + .detail-summary__field {
  margin-left: $pf-space-3;
  padding-left: $pf-space-3;
  border-left: 1rpx solid $pf-color-divider;
}

.detail-summary__label {
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.detail-summary__value {
  overflow: hidden;
  margin-top: $pf-space-1;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-detail-page .pf-section-heading {
  margin-top: $pf-space-5;
}

.detail-list {
  overflow: hidden;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.detail-row {
  display: flex;
  min-height: 104rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  gap: $pf-space-4;
  padding: 0 $pf-space-3;
}

.detail-row + .detail-row {
  border-top: 1rpx solid $pf-color-divider;
}

.detail-row--stack {
  flex-direction: column;
  align-items: flex-start;
  gap: $pf-space-1;
  padding-top: $pf-space-3;
  padding-bottom: $pf-space-3;
}

.detail-label {
  flex-shrink: 0;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  line-height: 1.45;
}

.detail-value {
  min-width: 0;
  max-width: 62%;
  color: $pf-color-text;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
  line-height: 1.45;
  text-align: right;
  word-break: break-all;
}

.detail-row--stack .detail-value {
  max-width: 100%;
  color: $pf-color-text-secondary;
  font-weight: $pf-font-weight-medium;
  text-align: left;
}

.delete-button {
  display: flex;
  width: 100%;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  margin: $pf-space-5 0 0;
  padding: 0 $pf-space-2;
  border: 1rpx solid $pf-color-danger-soft;
  border-radius: $pf-radius-control;
  background: $pf-color-danger-soft;
  color: $pf-color-danger;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  line-height: 1.25;
}

.delete-button::after {
  border: 0;
}

.delete-button--pressed {
  opacity: 0.72;
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
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  text-align: center;
}

.state-card text {
  margin-top: $pf-space-2;
}
</style>
