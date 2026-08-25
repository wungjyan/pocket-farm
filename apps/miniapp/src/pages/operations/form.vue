<template>
  <view class="pf-page operation-form-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#2F7D4A" />
      <text>正在加载农事表单</text>
    </view>

    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadForm"
      >
        重试
      </uv-button>
    </view>

    <template v-else>
      <view class="page-intro">
        <text class="page-title">{{ operationId ? "编辑农事" : "记录农事" }}</text>
        <text class="page-description">填写本次农事，地块可随时选择</text>
      </view>
      <view
        class="plot-field pf-card"
        :class="{ 'plot-field--selectable': !operationId, 'plot-field--empty': !plot }"
        @click="openPlotSelector"
      >
        <view>
          <text class="plot-field__label">地块 <text v-if="!operationId" class="field-required">*</text></text>
          <text class="plot-field__name">{{ plot?.name || "请选择地块" }}</text>
        </view>
        <text v-if="operationId" class="plot-field__locked">编辑时不可变更</text>
        <uv-icon v-else name="arrow-right" size="17" color="#929A93" />
      </view>
      <OperationForm
        :productions="activeProductions"
        :members="members"
        :operation-types="operationTypes"
        :current-user-id="currentUserId"
        :has-plot="Boolean(plot)"
        :initial-operation="operation"
        :selected-operation-type-id="selectedOperationTypeId"
        :selected-production-id="selectedProductionId"
        :submitting="submitting"
        :submit-label="operationId ? '保存修改' : '保存农事'"
        :loading-text="operationId ? '保存中' : '记录中'"
        @submit="handleSubmit"
        @select-operation-type="openOperationTypeSelector"
        @select-production="openProductionSelector"
      />
    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import OperationForm from "../../components/OperationForm.vue";
import { clearAuthToken } from "../../services/auth";
import { getFarmMembers, type FarmMember } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import {
  createOperation,
  getOperationTypes,
  getPlotOperations,
  updateOperation,
  type FarmOperation,
  type OperationInput,
  type OperationType,
} from "../../services/operation";
import { getPlot, type Plot } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import { getCurrentUser } from "../../services/user";

const plotId = ref(0);
const operationId = ref(0);
const farmId = ref(0);
const plot = ref<Plot | null>(null);
const operation = ref<FarmOperation | null>(null);
const activeProductions = ref<Production[]>([]);
const operationTypes = ref<OperationType[]>([]);
const selectedOperationTypeId = ref(0);
const selectedProductionId = ref<number | null>(null);
const members = ref<FarmMember[]>([]);
const currentUserId = ref(0);
const loading = ref(true);
const submitting = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadForm(): Promise<void> {
  if (!plotId.value) {
    if (!farmId.value) {
      loadError.value = "农场信息无效";
      loading.value = false;
      return;
    }
    loading.value = true;
    loadError.value = "";
    try {
      const [memberPage, user, operationTypePage] = await Promise.all([
        getFarmMembers(farmId.value),
        getCurrentUser(),
        getOperationTypes(),
      ]);
      members.value = memberPage.items;
      currentUserId.value = user.id;
      operationTypes.value = operationTypePage.items;
    } catch (error) {
      if (error instanceof ApiRequestError && error.statusCode === 401) {
        handleUnauthorized();
        return;
      }
      loadError.value = error instanceof ApiRequestError ? error.message : "农事表单加载失败，请稍后再试";
    } finally {
      loading.value = false;
    }
    return;
  }
  const showFullPageLoading = !members.value.length || !operationTypes.value.length;
  if (showFullPageLoading) loading.value = true;
  loadError.value = "";
  try {
    const plotResult = await getPlot(plotId.value);
    farmId.value = plotResult.farmId;
    const [productionPage, memberPage, user, operationPage, operationTypePage] = await Promise.all([
      getPlotProductions(plotResult.id, "ACTIVE"),
      getFarmMembers(plotResult.farmId),
      getCurrentUser(),
      operationId.value ? getPlotOperations(plotResult.id) : Promise.resolve(null),
      getOperationTypes(),
    ]);
    if (operationId.value) {
      operation.value = operationPage?.items.find((item) => item.id === operationId.value) || null;
      if (operation.value === null) {
        loadError.value = "农事记录不存在或无法编辑";
        return;
      }
      if (
        operation.value.productionId !== null &&
        !productionPage.items.some((item) => item.id === operation.value?.productionId)
      ) {
        loadError.value = "关联种养已结束，农事记录无法编辑";
        return;
      }
    }
    plot.value = plotResult;
    activeProductions.value = productionPage.items;
    operationTypes.value = operationTypePage.items;
    if (operation.value) {
      selectedOperationTypeId.value = operation.value.operationType.id;
      selectedProductionId.value = operation.value.productionId;
    }
    members.value = memberPage.items;
    currentUserId.value = user.id;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "农事表单加载失败，请稍后再试";
  } finally {
    if (showFullPageLoading) loading.value = false;
  }
}

function openPlotSelector(): void {
  if (operationId.value || !farmId.value) return;
  const selectedParameter = plot.value ? `&selectedPlotId=${plot.value.id}` : "";
  uni.navigateTo({
    url: `/pages/plots/index?farmId=${farmId.value}${selectedParameter}`,
    events: {
      selected: (selectedPlot: Plot) => {
        if (selectedPlot.id === plotId.value) return;
        plotId.value = selectedPlot.id;
        farmId.value = selectedPlot.farmId;
        operationId.value = 0;
        operation.value = null;
        selectedProductionId.value = null;
        loadForm();
      },
    },
  });
}

function openProductionSelector(): void {
  if (!plot.value) return;
  uni.navigateTo({
    url: `/pages/operations/productions?plotId=${plot.value.id}`,
    events: {
      selected: (production: Production | null) => {
        selectedProductionId.value = production?.id || null;
      },
    },
  });
}

function openOperationTypeSelector(): void {
  uni.navigateTo({
    url: "/pages/operation-types/index",
    events: {
      selected: (operationType: OperationType) => {
        selectedOperationTypeId.value = operationType.id;
      },
    },
  });
}

async function handleSubmit(input: OperationInput): Promise<void> {
  if (!plot.value || submitting.value) return;
  submitting.value = true;
  try {
    if (operationId.value) {
      await updateOperation(operationId.value, input);
    } else {
      await createOperation(plot.value.id, input);
    }
    uni.showToast({ title: operationId.value ? "已保存" : "记录成功", icon: "none" });
    setTimeout(() => uni.navigateBack(), 400);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "保存失败，请稍后再试");
    }
  } finally {
    submitting.value = false;
  }
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
  operationId.value = Number(options?.operationId || 0);
  farmId.value = Number(options?.farmId || 0);
  loadForm();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.operation-form-page {
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.page-intro {
  padding: 12rpx 4rpx 28rpx;
}

.page-title,
.page-description {
  display: block;
}

.plot-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
  padding: 20rpx 24rpx;
}

.plot-field--selectable {
  border-color: $pf-color-primary;
}

.plot-field--empty .plot-field__name {
  color: $pf-color-text-muted;
  font-weight: 400;
}

.plot-field__label,
.plot-field__name {
  display: block;
}

.plot-field__label,
.plot-field__locked {
  color: $pf-color-text-muted;
  font-size: 21rpx;
}

.field-required {
  margin-left: 4rpx;
  color: #c96a45;
}

.plot-field__name {
  margin-top: 5rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
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
}

.state-card text {
  margin-top: 16rpx;
}

</style>
