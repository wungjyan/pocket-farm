<template>
  <view class="pf-page edit-plot-page">
    <PfPageHeader title="编辑地块" :show-back="true" :back-handler="handleBack" />

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

    <PlotForm
      v-else-if="plot"
      :initial-name="plot.name"
      :initial-type="plot.type"
      :initial-area-value="plot.areaValue"
      :initial-area-unit="plot.areaUnit"
      :submitting="saving"
      @change="dirty = true"
      @submit="savePlot"
    />

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PlotForm from "../../components/PlotForm.vue";
import PfPageHeader from "../../components/PfPageHeader.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getPlot, updatePlot, type AreaUnit, type Plot, type PlotType } from "../../services/plot";

const plotId = ref(0);
const plot = ref<Plot | null>(null);
const loading = ref(true);
const saving = ref(false);
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
    dirty.value = false;
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

async function savePlot(input: { name: string; type: PlotType | null; areaValue: number | null; areaUnit: AreaUnit | null }): Promise<void> {
  if (!input.name) {
    toastRef.value?.error("请输入地块名称");
    return;
  }
  if ((input.areaValue === null) !== (input.areaUnit === null)) {
    toastRef.value?.error("请同时填写面积和单位");
    return;
  }
  saving.value = true;
  try {
    plot.value = await updatePlot(plotId.value, input);
    dirty.value = false;
    toastRef.value?.success("保存成功");
    setTimeout(() => uni.navigateBack(), 400);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "保存失败，请稍后再试");
    }
  } finally {
    saving.value = false;
  }
}

function handleBack(): void {
  if (!dirty.value) {
    uni.navigateBack();
    return;
  }
  uni.showModal({
    title: "放弃修改？",
    content: "当前内容尚未保存，确定要离开吗？",
    confirmColor: "#C96A45",
    success: (result) => {
      if (result.confirm) uni.navigateBack();
    },
  });
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
});

onShow(() => {
  if (plotId.value && !saving.value) loadPlot();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.edit-plot-page {
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
  margin: 28rpx $pf-space-page-x 0;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
