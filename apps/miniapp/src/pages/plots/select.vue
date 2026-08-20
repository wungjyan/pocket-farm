<template>
  <view class="pf-page plot-select-page">
    <PfPageHeader title="选择地块" :show-back="true" />
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card"><uv-loading-icon mode="circle" color="#2F7D4A" /><text>正在加载地块</text></view>
      <view v-else-if="loadError" class="state-card pf-card"><uv-icon name="warning" size="28" color="#C96A45" /><text>{{ loadError }}</text><uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadPlots">重试</uv-button></view>
      <view v-else-if="plots.length" class="plot-list pf-card">
        <view v-for="item in plots" :key="item.id" class="plot-row" @click="choosePlot(item)">
          <view><text class="plot-name">{{ item.name }}</text><text class="plot-meta">{{ plotMeta(item) }}</text></view>
          <uv-icon name="arrow-right" size="17" color="#929A93" />
        </view>
      </view>
      <view v-else class="state-card pf-card"><uv-icon name="map" size="30" color="#929A93" /><text>当前农场还没有地块</text></view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getFarmPlots, type Plot } from "../../services/plot";
import { formatNumber } from "../../utils/number";

interface OpenerEventChannel { emit: (eventName: string, data: Plot) => void }
const plots = ref<Plot[]>([]);
const farmId = ref(0);
const loading = ref(false);
const loadError = ref("");
let openerEventChannel: OpenerEventChannel | null = null;
const plotTypeLabels: Record<string, string> = { FIELD: "旱地", PADDY: "水田", GREENHOUSE: "大棚", ORCHARD: "果园", FOREST: "林地", POND: "鱼塘", BARN: "圈舍", OTHER: "其他" };
const areaUnitLabels: Record<string, string> = { MU: "亩", SQUARE_METER: "㎡", HECTARE: "公顷" };

function plotMeta(plot: Plot): string {
  const type = plot.type ? plotTypeLabels[plot.type] || "地块" : "地块";
  const area = plot.areaValue !== null && plot.areaUnit ? ` · ${formatNumber(plot.areaValue)}${areaUnitLabels[plot.areaUnit] || ""}` : "";
  return `${type}${area}`;
}

async function loadPlots(): Promise<void> {
  if (!farmId.value) { loadError.value = "农场信息无效"; return; }
  loading.value = true; loadError.value = "";
  try { plots.value = (await getFarmPlots(farmId.value)).items; }
  catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) { clearAuthToken(); uni.reLaunch({ url: "/pages/auth/login" }); return; }
    loadError.value = error instanceof ApiRequestError ? error.message : "地块加载失败，请稍后再试";
  } finally { loading.value = false; }
}
function choosePlot(plot: Plot): void { openerEventChannel?.emit("selected", plot); uni.navigateBack(); }
onLoad((options) => { farmId.value = Number(options?.farmId || 0); const page = getCurrentInstance()?.proxy as unknown as { getOpenerEventChannel?: () => OpenerEventChannel } | null; openerEventChannel = page?.getOpenerEventChannel?.() || null; loadPlots(); });
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";
.plot-list { overflow: hidden; }.plot-row { display: flex; min-height: 104rpx; align-items: center; justify-content: space-between; padding: 0 24rpx; }.plot-row + .plot-row { border-top: 1rpx solid $pf-color-divider; }.plot-name,.plot-meta { display:block; }.plot-name { color:$pf-color-text; font-size:28rpx; font-weight:600; }.plot-meta { margin-top:6rpx; color:$pf-color-text-muted; font-size:22rpx; }.state-card { display:flex; min-height:220rpx; box-sizing:border-box; flex-direction:column; align-items:center; justify-content:center; color:$pf-color-text-secondary; font-size:24rpx; }.state-card text { margin-top:16rpx; }
</style>
