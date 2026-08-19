<template>
  <view class="pf-page production-form-page">
    <PfPageHeader title="填写种养信息" :show-back="true" :back-handler="handleBack" />

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
    <view v-else-if="!selectedSpecies" class="state-card pf-card">
      <uv-icon name="info-circle" size="28" color="#929A93" />
      <text>请返回重新选择种类</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="handleBack">
        返回
      </uv-button>
    </view>
    <template v-else-if="plot">
      <view class="plot-summary">
        <text class="plot-summary__label">当前地块</text>
        <text class="plot-summary__name">{{ plot.name }}</text>
      </view>
      <ProductionForm
        :initial-species="selectedSpecies"
        :initial-variety="variety"
        submit-label="开始种养"
        loading-text="提交中"
        :submitting="submitting"
        @change="dirty = true"
        @submit="handleCreate"
      />
    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import ProductionForm from "../../components/ProductionForm.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { createProduction, type ProductionInput } from "../../services/production";
import { getPlot, type Plot } from "../../services/plot";
import type { Species } from "../../services/species";

interface SetupEventChannel {
  on: (eventName: string, callback: (data: { species: Species; variety: string }) => void) => void;
}

const plotId = ref(0);
const plot = ref<Plot | null>(null);
const selectedSpecies = ref<Species | null>(null);
const variety = ref("");
const loading = ref(true);
const submitting = ref(false);
const dirty = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void; success: (message: string) => void } | null>(null);

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
    plot.value = await getPlot(plotId.value);
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

async function handleCreate(input: ProductionInput): Promise<void> {
  if (!plotId.value) {
    toastRef.value?.error("地块信息无效");
    return;
  }
  submitting.value = true;
  try {
    await createProduction(plotId.value, input);
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

function handleBack(): void {
  if (!dirty.value) {
    uni.navigateBack();
    return;
  }
  uni.showModal({
    title: "放弃填写？",
    content: "表单内容尚未保存，确定要返回吗？",
    confirmColor: "#C96A45",
    success: (result) => {
      if (result.confirm) uni.navigateBack();
    },
  });
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
  const page = getCurrentInstance()?.proxy as unknown as {
    getOpenerEventChannel?: () => SetupEventChannel;
  } | null;
  page?.getOpenerEventChannel?.().on("setup", (data) => {
    selectedSpecies.value = data.species;
    variety.value = data.variety;
  });
  loadPlot();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.production-form-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding-bottom: $pf-space-page-bottom;
}

.plot-summary {
  display: flex;
  align-items: baseline;
  padding: 20rpx $pf-space-page-x 24rpx;
}

.plot-summary__label {
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}

.plot-summary__name {
  margin-left: 14rpx;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 600;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 28rpx $pf-space-page-x 0;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
