<template>
  <view class="pf-page production-select-page">
    <view class="pf-page-content">
      <text class="page-hint">默认记录整个地块；选择批次后可用于追溯。</text>
      <view class="production-list">
        <view class="whole-plot-card pf-card pf-tappable" :class="{ 'production-card--selected': selectedProductionId === null }" @click="chooseProduction(null)"><view><text class="production-name">整个地块</text><text class="production-meta">不关联具体种养批次</text></view><view class="production-selection" :class="{ 'production-selection--selected': selectedProductionId === null }"><uv-icon v-if="selectedProductionId === null" name="checkmark" size="15" color="#2F7D4A" /></view></view>
        <view v-if="loading" class="state-card pf-card"><uv-loading-icon mode="circle" color="#2F7D4A" /><text>正在加载种养批次</text></view>
        <view v-else-if="loadError" class="state-card pf-card"><uv-icon name="warning" size="28" color="#C96A45" /><text>{{ loadError }}</text><uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadProductions">重试</uv-button></view>
        <view v-else v-for="item in productions" :key="item.id" class="production-card pf-card pf-tappable" :class="{ 'production-card--selected': item.id === selectedProductionId }" @click="chooseProduction(item)"><view><text class="production-name">{{ productionName(item) }}</text><text class="production-meta">{{ productionMeta(item) }}</text></view><view class="production-selection" :class="{ 'production-selection--selected': item.id === selectedProductionId }"><uv-icon v-if="item.id === selectedProductionId" name="checkmark" size="15" color="#2F7D4A" /></view></view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getPlotProductions, type Production } from "../../services/production";

interface OpenerEventChannel { emit: (eventName: string, data: Production | null) => void }
const plotId = ref(0); const selectedProductionId = ref<number | null>(null); const productions = ref<Production[]>([]); const loading = ref(false); const loadError = ref(""); let openerEventChannel: OpenerEventChannel | null = null;
const unitLabels: Record<string, string> = { PLANT: "株", HEAD: "头", TAIL: "尾", CAGE: "笼", BOX: "箱", POND: "塘" };
function productionName(item: Production): string { return `${item.speciesName}${item.variety ? ` · ${item.variety}` : ""}`; }
function productionMeta(item: Production): string { const quantity = item.initialQuantity === null ? "" : ` · 初始${item.initialQuantity}${unitLabels[item.individualUnit] || ""}`; return `${item.startedOn} 开始${quantity}`; }
async function loadProductions(): Promise<void> { if (!plotId.value) { loadError.value = "地块信息无效"; return; } loading.value = true; loadError.value = ""; try { productions.value = (await getPlotProductions(plotId.value, "ACTIVE")).items; } catch (error) { if (error instanceof ApiRequestError && error.statusCode === 401) { clearAuthToken(); uni.reLaunch({ url: "/pages/auth/login" }); return; } loadError.value = error instanceof ApiRequestError ? error.message : "种养批次加载失败，请稍后再试"; } finally { loading.value = false; } }
function chooseProduction(production: Production | null): void { openerEventChannel?.emit("selected", production); uni.navigateBack(); }
onLoad((options) => { plotId.value = Number(options?.plotId || 0); const currentSelection = Number(options?.selectedProductionId); selectedProductionId.value = Number.isInteger(currentSelection) && currentSelection > 0 ? currentSelection : null; const page = getCurrentInstance()?.proxy as unknown as { getOpenerEventChannel?: () => OpenerEventChannel } | null; openerEventChannel = page?.getOpenerEventChannel?.() || null; loadProductions(); });
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";
.page-hint { display:block; margin-bottom:18rpx; color:$pf-color-text-muted; font-size:22rpx; }.production-list { display:flex; flex-direction:column; gap:14rpx; }.whole-plot-card,.production-card { display:flex; min-height:108rpx; align-items:center; justify-content:space-between; padding:0 24rpx; }.whole-plot-card { border-color:$pf-color-primary; }.production-card--selected { background:$pf-color-primary-soft; }.production-name,.production-meta { display:block; }.production-name { color:$pf-color-text; font-size:28rpx; font-weight:600; }.production-meta { margin-top:7rpx; color:$pf-color-text-muted; font-size:22rpx; }.production-selection { display:flex; width:36rpx; height:36rpx; box-sizing:border-box; flex-shrink:0; align-items:center; justify-content:center; margin-left:16rpx; border:2rpx solid $pf-color-border; border-radius:50%; background:$pf-color-surface; }.production-selection--selected { border-color:$pf-color-primary; }.state-card { display:flex; min-height:200rpx; box-sizing:border-box; flex-direction:column; align-items:center; justify-content:center; color:$pf-color-text-secondary; font-size:24rpx; }.state-card text { margin-top:16rpx; }
</style>
