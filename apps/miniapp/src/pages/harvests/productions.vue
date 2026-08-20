<template>
  <view class="pf-page production-select-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#2F7D4A" />
      <text>正在加载当前种养</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadProductions">重试</uv-button>
    </view>
    <template v-else>
      <view class="page-intro">
        <text class="page-title">选择种养</text>
        <text class="page-description">请选择本次采收、捕捞或出栏所属的具体种养</text>
      </view>
      <view v-if="options.length" class="production-list">
        <view v-for="item in options" :key="item.production.id" class="production-card pf-card" @click="chooseProduction(item)">
          <view class="production-copy">
            <text class="production-name">{{ item.production.speciesName }}{{ item.production.variety ? ` · ${item.production.variety}` : "" }}</text>
            <text class="production-plot">{{ item.plot.name }}</text>
            <text class="production-meta">{{ item.production.startedOn }} 开始{{ quantityLabel(item.production) }}</text>
          </view>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
      </view>
      <view v-else class="state-card pf-card">
        <uv-icon name="list" size="30" color="#929A93" />
        <text>当前范围内没有进行中的种养</text>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import type { HarvestProductionSelection } from "../../services/harvest";
import { ApiRequestError } from "../../services/http";
import { getFarmPlots, getPlot, type Plot } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import { formatNumber } from "../../utils/number";

interface OpenerEventChannel {
  emit: (eventName: string, data: HarvestProductionSelection) => void;
}

const farmId = ref(0);
const plotId = ref(0);
const options = ref<HarvestProductionSelection[]>([]);
const loading = ref(true);
const loadError = ref("");
let openerEventChannel: OpenerEventChannel | null = null;

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadProductions(): Promise<void> {
  if (!farmId.value && !plotId.value) {
    loadError.value = "农场信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const plots = plotId.value
      ? [await getPlot(plotId.value)]
      : (await getFarmPlots(farmId.value)).items;
    const results = await Promise.all(
      plots.map(async (plot) => ({
        plot,
        productions: (await getPlotProductions(plot.id, "ACTIVE")).items,
      })),
    );
    options.value = results.flatMap(({ plot, productions }) =>
      productions.map((production) => ({ plot, production })),
    );
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "种养加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function quantityLabel(production: Production): string {
  if (production.initialQuantity === null) return "";
  const units: Record<string, string> = {
    HEAD: "头",
    FEATHER: "羽",
    PIECE: "只",
    PLANT: "株",
    TAIL: "尾",
  };
  return ` · 初始 ${formatNumber(production.initialQuantity)}${units[production.individualUnit] || ""}`;
}

function chooseProduction(selection: HarvestProductionSelection): void {
  openerEventChannel?.emit("selected", selection);
  uni.navigateBack();
}

onLoad((optionsValue) => {
  farmId.value = Number(optionsValue?.farmId || 0);
  plotId.value = Number(optionsValue?.plotId || 0);
  const page = getCurrentInstance()?.proxy as unknown as {
    getOpenerEventChannel?: () => OpenerEventChannel;
  } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
  loadProductions();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.production-select-page { padding: 28rpx $pf-space-page-x $pf-space-page-bottom; }
.page-intro { padding: 12rpx 4rpx 28rpx; }
.page-title, .page-description, .production-name, .production-plot, .production-meta { display: block; }
.page-title { color: $pf-color-text; font-size: 38rpx; font-weight: 700; }
.page-description { margin-top: 10rpx; color: $pf-color-text-secondary; font-size: 24rpx; line-height: 1.5; }
.production-list { display: flex; flex-direction: column; gap: 14rpx; }
.production-card { display: flex; min-height: 122rpx; align-items: center; padding: 16rpx 22rpx; border-left: 5rpx solid $pf-color-harvest; }
.production-copy { min-width: 0; flex: 1; }
.production-name { overflow: hidden; color: $pf-color-text; font-size: 28rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.production-plot { margin-top: 5rpx; color: $pf-color-harvest; font-size: 22rpx; }
.production-meta { margin-top: 5rpx; color: $pf-color-text-muted; font-size: 21rpx; }
.state-card { display: flex; min-height: 220rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 28rpx; color: $pf-color-text-secondary; font-size: 24rpx; text-align: center; }
.state-card text { margin-top: 16rpx; }
</style>
