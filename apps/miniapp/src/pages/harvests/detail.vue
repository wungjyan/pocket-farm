<template>
  <view class="pf-page harvest-detail-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#286B46" />
      <text>正在加载收获记录</text>
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

    <view v-else-if="harvest && production && plot" class="pf-page-content">
      <view class="detail-card pf-card">
        <view class="detail-heading">
          <text class="detail-title">{{ harvest.productName || production.speciesName }}</text>
        </view>

        <view class="detail-list">
          <view class="detail-row">
            <text class="detail-label">收获时间</text>
            <text class="detail-value">{{ harvestDateLabel(harvest.harvestedAt) }}</text>
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
            <text class="detail-label">数量</text>
            <text class="detail-value detail-value--quantity">{{ quantityLabel }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">作业方式</text>
            <text class="detail-value">{{ workMethodLabel(harvest.workMethod) }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">操作人</text>
            <text class="detail-value">{{ memberName(harvest.operatorId) }}</text>
          </view>
          <view v-if="harvest.createdBy !== harvest.operatorId" class="detail-row">
            <text class="detail-label">记录人</text>
            <text class="detail-value">{{ memberName(harvest.createdBy) }}</text>
          </view>
          <view v-if="harvest.grade" class="detail-row">
            <text class="detail-label">等级</text>
            <text class="detail-value">{{ harvest.grade }}</text>
          </view>
          <view v-if="harvest.remark" class="detail-row detail-row--stack">
            <text class="detail-label">备注</text>
            <text class="detail-value">{{ harvest.remark }}</text>
          </view>
        </view>
      </view>

      <view v-if="!readOnly" class="action-grid">
        <button
          class="action-button action-button--primary"
          hover-class="action-button--primary-pressed"
          @tap="openEdit"
        >
          编辑收获记录
        </button>
        <button
          class="action-button action-button--danger"
          hover-class="action-button--danger-pressed"
          @tap="confirmDelete"
        >
          删除收获记录
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
import {
  deleteHarvest,
  getHarvest,
  type HarvestRecord,
  type QuantityUnit,
} from "../../services/harvest";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot } from "../../services/plot";
import {
  getProduction,
  type Production,
  type WorkMethod,
} from "../../services/production";
import { formatNumber } from "../../utils/number";

const unitLabels: Record<QuantityUnit, string> = {
  KG: "公斤",
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只/个",
  PLANT: "株",
  TAIL: "尾",
};

const workMethodLabels: Record<WorkMethod, string> = {
  MANUAL: "人工",
  MECHANICAL: "机械",
};

const harvestId = ref(0);
const harvest = ref<HarvestRecord | null>(null);
const production = ref<Production | null>(null);
const plot = ref<Plot | null>(null);
const members = ref<FarmMember[]>([]);
const loading = ref(true);
const deleting = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);

const readOnly = computed(() => production.value?.status !== "ACTIVE");
const productionLabel = computed(() => {
  const value = production.value;
  if (!value) return "关联种养";
  return `${value.speciesName}${value.variety ? ` · ${value.variety}` : ""}`;
});
const quantityLabel = computed(() => {
  const value = harvest.value;
  return value ? `${formatNumber(value.quantity)} ${unitLabels[value.unit]}` : "";
});

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function harvestDateLabel(value: string): string {
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
  if (!harvestId.value) {
    loadError.value = "收获记录信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const harvestResult = await getHarvest(harvestId.value);
    const productionResult = await getProduction(harvestResult.productionId);
    const plotResult = await getPlot(productionResult.plotId);
    const memberPage = await getFarmMembers(plotResult.farmId);
    harvest.value = harvestResult;
    production.value = productionResult;
    plot.value = plotResult;
    members.value = memberPage.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "收获记录加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openEdit(): void {
  if (!harvest.value || readOnly.value) return;
  uni.navigateTo({
    url: `/pages/harvests/form?productionId=${harvest.value.productionId}&harvestId=${harvest.value.id}`,
  });
}

function confirmDelete(): void {
  if (!harvest.value || readOnly.value || deleting.value) return;
  uni.showModal({
    title: "删除收获记录？",
    content: "删除后无法恢复，确定要继续吗？",
    confirmColor: "#C96A45",
    success: async (result) => {
      if (!result.confirm || !harvest.value) return;
      deleting.value = true;
      try {
        await deleteHarvest(harvest.value.id);
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
  harvestId.value = Number(options?.harvestId || 0);
});

onShow(() => {
  if (harvestId.value && !deleting.value) loadDetail();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.harvest-detail-page {
  padding-bottom: $pf-space-page-bottom;
}

.harvest-detail-page .pf-page-content {
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

.detail-value--quantity {
  color: $pf-color-harvest;
  font-weight: 650;
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
  border-color: $pf-color-harvest-soft;
  background: $pf-color-harvest-soft;
  color: $pf-color-harvest;
}

.action-button--danger {
  border-color: transparent;
  background: $pf-color-danger-soft;
  color: $pf-color-danger;
}

.action-button--primary-pressed,
.action-button--danger-pressed {
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
  color: $pf-color-text-secondary;
  font-size: 24rpx;
  text-align: center;
}

.state-card text {
  margin-top: $pf-space-2;
}
</style>
