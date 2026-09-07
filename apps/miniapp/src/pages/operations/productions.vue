<template>
  <view class="pf-page production-select-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card">
        <uv-loading-icon mode="circle" color="#006C49" />
        <text>正在加载种养</text>
      </view>
      <view v-else-if="loadError" class="state-card">
        <uv-icon name="warning" size="28" color="#A9433B" />
        <text>{{ loadError }}</text>
        <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 16rpx;" @click="loadProductions">重试</uv-button>
      </view>
      <template v-else>
        <view v-if="productions.length" class="list-toolbar">
          <text class="list-toolbar__count">{{ productions.length }} 个进行中种养</text>
        </view>
        <view class="production-list">
          <view
            class="production-row"
            :class="{ 'production-row--selected': selectedProductionId === null }"
            hover-class="production-row--pressed"
            @tap="chooseProduction(null)"
          >
            <view class="production-copy">
              <text class="production-name">整个地块</text>
              <text class="production-meta">不关联具体种养</text>
            </view>
            <view class="production-selection" :class="{ 'production-selection--selected': selectedProductionId === null }">
              <uv-icon v-if="selectedProductionId === null" name="checkmark" size="15" color="#006C49" />
            </view>
            <view v-if="productions.length" class="production-row__divider" />
          </view>
          <view
            v-for="(item, index) in productions"
            :key="item.id"
            class="production-row"
            :class="{ 'production-row--selected': item.id === selectedProductionId }"
            hover-class="production-row--pressed"
            @tap="chooseProduction(item)"
          >
            <view class="production-copy">
              <text class="production-name">{{ productionName(item) }}</text>
              <text class="production-meta">{{ productionMeta(item) }}</text>
            </view>
            <view class="production-selection" :class="{ 'production-selection--selected': item.id === selectedProductionId }">
              <uv-icon v-if="item.id === selectedProductionId" name="checkmark" size="15" color="#006C49" />
            </view>
            <view v-if="index < productions.length - 1" class="production-row__divider" />
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getPlotProductions, type Production } from "../../services/production";
import { formatNumber } from "../../utils/number";

interface OpenerEventChannel { emit: (eventName: string, data: Production | null) => void }
const plotId = ref(0); const selectedProductionId = ref<number | null>(null); const productions = ref<Production[]>([]); const loading = ref(false); const loadError = ref(""); let openerEventChannel: OpenerEventChannel | null = null;
const unitLabels: Record<string, string> = { PLANT: "株", HEAD: "头", FEATHER: "羽", PIECE: "只", TAIL: "尾" };

function productionName(item: Production): string {
  return `${item.speciesName}${item.variety ? ` · ${item.variety}` : ""}`;
}

function productionMeta(item: Production): string {
  const quantity = item.initialQuantity === null
    ? ""
    : ` · 初始${formatNumber(item.initialQuantity)}${unitLabels[item.individualUnit] || ""}`;
  return `${item.startedOn} 开始${quantity}`;
}

async function loadProductions(): Promise<void> {
  if (!plotId.value) {
    loadError.value = "地块信息无效";
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    productions.value = (await getPlotProductions(plotId.value, "ACTIVE")).items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "种养加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function chooseProduction(production: Production | null): void {
  openerEventChannel?.emit("selected", production);
  uni.navigateBack();
}

onLoad((options) => {
  plotId.value = Number(options?.plotId || 0);
  const currentSelection = Number(options?.selectedProductionId);
  selectedProductionId.value = Number.isInteger(currentSelection) && currentSelection > 0 ? currentSelection : null;
  const page = getCurrentInstance()?.proxy as unknown as {
    getOpenerEventChannel?: () => OpenerEventChannel;
  } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
  loadProductions();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";
.production-select-page .pf-page-content {
  padding-top: $pf-space-4;
}

.list-toolbar {
  display: flex;
  min-height: 48rpx;
  align-items: center;
  justify-content: flex-end;
  padding: 0 4rpx $pf-space-2;
}

.list-toolbar__count {
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.production-list {
  overflow: hidden;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.production-row {
  position: relative;
  display: flex;
  min-height: 104rpx;
  box-sizing: border-box;
  align-items: center;
  padding: $pf-space-2 $pf-space-3;
}

.production-row--selected,
.production-row--pressed {
  background: $pf-color-primary-soft;
}

.production-copy {
  min-width: 0;
  flex: 1;
}

.production-name,
.production-meta {
  display: block;
}

.production-name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-meta {
  overflow: hidden;
  margin-top: 5rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-selection {
  display: flex;
  width: 36rpx;
  height: 36rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-left: $pf-space-2;
  border: 2rpx solid $pf-color-border;
  border-radius: 50%;
  background: $pf-color-surface;
}

.production-selection--selected {
  border-color: $pf-color-primary;
}

.production-row__divider {
  position: absolute;
  right: 0;
  bottom: 0;
  left: $pf-space-3;
  height: 1rpx;
  background: $pf-color-divider;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: $pf-space-4;
  padding: $pf-space-4;
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
