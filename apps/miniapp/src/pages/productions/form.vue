<template>
  <view class="pf-page production-form-page">
    <view v-if="loading" class="state-card">
      <uv-loading-icon mode="circle" color="#006C49" />
      <text>正在准备种养表单</text>
    </view>
    <view v-else-if="loadError" class="state-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 16rpx;" @click="loadInitialData">
        重试
      </uv-button>
    </view>
    <view v-else-if="!selectedSpecies" class="state-card">
      <uv-icon name="info-circle" size="28" color="#748178" />
      <text>请返回重新选择种类</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 16rpx;" @click="goBack">
        返回
      </uv-button>
    </view>
    <ProductionForm
      v-else-if="selectedSpecies"
      :initial-species="selectedSpecies"
      :initial-variety="variety"
      :initial-plot="plot"
      :show-plot-field="true"
      :plot-selectable="true"
      submit-label="开始种养"
      loading-text="提交中"
      :submitting="submitting"
      @select-plot="openPlotSelector"
      @change="dirty = true"
      @submit="handleCreate"
    />

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import ProductionForm from "../../components/ProductionForm.vue";
import { useUnsavedChangesGuard } from "../../composables/useUnsavedChangesGuard";
import { clearAuthToken } from "../../services/auth";
import { notifyFarmActivitiesChanged } from "../../services/home";
import { ApiRequestError } from "../../services/http";
import { createProduction, type ProductionInput } from "../../services/production";
import { getPlot, type Plot } from "../../services/plot";
import type { IndividualUnit, Industry, Species } from "../../services/species";

const farmId = ref(0);
const plotId = ref(0);
const speciesId = ref(0);
const plot = ref<Plot | null>(null);
const selectedSpecies = ref<Species | null>(null);
const variety = ref("");
const loading = ref(true);
const submitting = ref(false);
const dirty = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void; success: (message: string) => void } | null>(null);
useUnsavedChangesGuard(dirty);

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadPlot(): Promise<void> {
  if (!plotId.value) {
    plot.value = null;
    return;
  }
  plot.value = await getPlot(plotId.value);
  farmId.value = plot.value.farmId;
}

async function loadInitialData(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    await loadPlot();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "种养信息准备失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function parseIndustry(value: unknown): Industry | null {
  return value === "AGRICULTURE" || value === "FORESTRY" || value === "LIVESTOCK" || value === "FISHERY"
    ? value
    : null;
}

function parseIndividualUnit(value: unknown): IndividualUnit | null {
  return value === "HEAD" || value === "FEATHER" || value === "PIECE" || value === "PLANT" || value === "TAIL"
    ? value
    : null;
}

function decodeRouteText(value: unknown): string {
  if (typeof value !== "string") return "";
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

async function handleCreate(input: ProductionInput): Promise<void> {
  if (!plot.value) {
    toastRef.value?.error("请选择地块");
    return;
  }
  submitting.value = true;
  try {
    await createProduction(plot.value.id, input);
    notifyFarmActivitiesChanged(plot.value.farmId);
    dirty.value = false;
    toastRef.value?.success("已开始种养");
    setTimeout(() => uni.navigateBack({ delta: 2 }), 400);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "提交失败，请稍后再试");
    }
  } finally {
    submitting.value = false;
  }
}

function openPlotSelector(): void {
  if (!farmId.value) {
    toastRef.value?.error("农场信息无效");
    return;
  }
  const selectedParameter = plot.value ? `&selectedPlotId=${plot.value.id}` : "";
  uni.navigateTo({
    url: `/pages/plots/index?farmId=${farmId.value}${selectedParameter}`,
    events: {
      selected: (selectedPlot: Plot) => {
        plotId.value = selectedPlot.id;
        plot.value = selectedPlot;
        dirty.value = true;
      },
    },
  });
}

function goBack(): void {
  uni.navigateBack();
}

onLoad((options) => {
  farmId.value = Number(options?.farmId || 0);
  plotId.value = Number(options?.plotId || 0);
  const requestedSpeciesId = Number(options?.speciesId || 0);
  speciesId.value = Number.isInteger(requestedSpeciesId) && requestedSpeciesId > 0 ? requestedSpeciesId : 0;
  const industry = parseIndustry(options?.industry);
  const individualUnit = parseIndividualUnit(options?.individualUnit);
  const speciesName = decodeRouteText(options?.speciesName);
  selectedSpecies.value = speciesId.value && industry && individualUnit && speciesName
    ? { id: speciesId.value, name: speciesName, industry, individualUnit, createdAt: "" }
    : null;
  variety.value = decodeRouteText(options?.variety);
  loadInitialData();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.production-form-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding-bottom: $pf-space-page-bottom;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: $pf-space-4 $pf-space-page-x 0;
  padding: 28rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
