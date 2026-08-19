<template>
  <view class="pf-page production-setup-page">
    <PfPageHeader title="开始种养" :show-back="true" />

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
      <view class="plot-summary">
        <text class="plot-summary__label">当前地块</text>
        <text class="plot-summary__name">{{ plot.name }}</text>
      </view>

      <view class="setup-card pf-card">
        <view class="field-group">
          <text class="field-label">种类 <text class="field-required">*</text></text>
          <view class="select-shell" @click="openSpeciesSelector">
            <view v-if="selectedSpecies" class="species-copy">
              <text class="species-copy__name">{{ selectedSpecies.name }}</text>
              <text class="species-copy__industry">{{ industryLabel(selectedSpecies.industry) }}</text>
            </view>
            <text v-else class="select-placeholder">请选择种类</text>
            <uv-icon name="arrow-right" size="17" color="#929A93" />
          </view>
        </view>

        <view v-if="selectedSpecies" class="field-group">
          <text class="field-label">品种 <text class="field-optional">选填</text></text>
          <view class="input-shell">
            <uv-input
              v-model="variety"
              maxlength="100"
              clearable
              border="none"
              placeholder="例如：水果黄瓜"
              placeholder-style="color: #929A93;"
              color="#202821"
            />
          </view>
        </view>

        <uv-button
          type="primary"
          size="large"
          shape="square"
          :disabled="!selectedSpecies"
          custom-style="height: 88rpx; margin-top: 42rpx; border-radius: 16rpx;"
          @click="startProduction"
        >
          开始种养
        </uv-button>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot } from "../../services/plot";
import type { Industry, Species } from "../../services/species";

interface FormEventChannel {
  emit: (eventName: string, data: { species: Species; variety: string }) => void;
}

const industryLabels: Record<Industry, string> = {
  AGRICULTURE: "农业",
  FORESTRY: "林业",
  LIVESTOCK: "牧业",
  FISHERY: "渔业",
};
const plotId = ref(0);
const plot = ref<Plot | null>(null);
const selectedSpecies = ref<Species | null>(null);
const variety = ref("");
const loading = ref(true);
const loadError = ref("");

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function industryLabel(industry: Industry): string {
  return industryLabels[industry];
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

function openSpeciesSelector(): void {
  uni.navigateTo({
    url: "/pages/species/index",
    events: {
      selected: (item: Species) => {
        if (selectedSpecies.value?.id !== item.id) {
          variety.value = "";
        }
        selectedSpecies.value = item;
      },
    },
  });
}

function startProduction(): void {
  if (!selectedSpecies.value || !plotId.value) return;
  uni.navigateTo({
    url: `/pages/productions/form?plotId=${plotId.value}`,
    success: (result) => {
      const eventChannel = result.eventChannel as unknown as FormEventChannel;
      eventChannel.emit("setup", {
        species: selectedSpecies.value as Species,
        variety: variety.value.trim(),
      });
    },
  });
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
  loadPlot();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.production-setup-page {
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

.setup-card {
  margin: 0 $pf-space-page-x;
  padding: 28rpx 24rpx;
}

.field-group + .field-group {
  margin-top: 32rpx;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.field-required {
  margin-left: 6rpx;
  color: #c96a45;
}

.field-optional {
  margin-left: 8rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 400;
}

.select-shell,
.input-shell {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  padding: 0 20rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.select-shell {
  color: $pf-color-text;
  font-size: 25rpx;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}

.select-placeholder {
  color: $pf-color-text-muted;
}

.species-copy,
.species-copy__name,
.species-copy__industry {
  display: block;
}

.species-copy__name {
  color: $pf-color-text;
  font-size: 26rpx;
  font-weight: 600;
}

.species-copy__industry {
  margin-top: 4rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
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
