<template>
  <view class="pf-page production-select-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card">
        <uv-loading-icon mode="circle" color="#006C49" />
        <text>正在加载当前种养</text>
      </view>
      <view v-else-if="loadError" class="state-card">
        <uv-icon name="warning" size="28" color="#A9433B" />
        <text>{{ loadError }}</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 22rpx; border-radius: 16rpx;"
          @click="loadProductions"
        >
          重试
        </uv-button>
      </view>
      <template v-else>
        <view v-if="total" class="list-toolbar">
          <text class="list-toolbar__count">{{ total }} 个进行中种养</text>
        </view>
        <view v-if="options.length" class="production-list">
          <view
            v-for="(item, index) in options"
            :key="item.id"
            class="production-row"
            :class="{ 'production-row--selected': item.id === selectedProductionId }"
            hover-class="production-row--pressed"
            @tap="chooseProduction(item)"
          >
            <view class="production-copy">
              <text class="production-name">{{ productionName(item) }}</text>
              <text class="production-plot">{{ item.plotName }}</text>
              <text class="production-meta">{{ productionMeta(item) }}</text>
            </view>
            <view
              class="production-selection"
              :class="{ 'production-selection--selected': item.id === selectedProductionId }"
            >
              <uv-icon v-if="item.id === selectedProductionId" name="checkmark" size="15" color="#006C49" />
            </view>
            <view v-if="index < options.length - 1" class="production-row__divider" />
          </view>
        </view>
        <PfEmptyState
          v-else
          icon="sprout"
          title="当前范围内没有进行中的种养"
        />
        <uv-load-more
          v-if="options.length && (hasMore || loadingMore)"
          :status="loadingMore ? 'loading' : 'loadmore'"
          icon-color="#006C49"
          color="#748178"
        />
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad, onReachBottom } from "@dcloudio/uni-app";
import PfEmptyState from "../../components/PfEmptyState.vue";
import { clearAuthToken } from "../../services/auth";
import type { HarvestProductionSelection } from "../../services/harvest";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot } from "../../services/plot";
import {
  getFarmProductions,
  getPlotProductions,
  type Production,
} from "../../services/production";
import type { IndividualUnit } from "../../services/species";
import { formatNumber } from "../../utils/number";

interface OpenerEventChannel {
  emit: (eventName: string, data: HarvestProductionSelection) => void;
}

interface ProductionOption {
  id: number;
  plotName: string;
  speciesName: string;
  variety: string | null;
  startedOn: string;
  initialQuantity: number | string | null;
  individualUnit: IndividualUnit;
}

const PAGE_SIZE = 100;
const unitLabels: Record<IndividualUnit, string> = {
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只",
  PLANT: "株",
  TAIL: "尾",
};

const farmId = ref(0);
const plotId = ref(0);
const selectedProductionId = ref<number | null>(null);
const options = ref<ProductionOption[]>([]);
const selectedPlot = ref<Plot | null>(null);
const total = ref(0);
const currentPage = ref(1);
const hasMore = ref(false);
const loading = ref(true);
const loadingMore = ref(false);
const loadError = ref("");
let openerEventChannel: OpenerEventChannel | null = null;

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function toProductionOption(production: Production, plotName: string): ProductionOption {
  return {
    id: production.id,
    plotName,
    speciesName: production.speciesName,
    variety: production.variety,
    startedOn: production.startedOn,
    initialQuantity: production.initialQuantity,
    individualUnit: production.individualUnit,
  };
}

async function fetchProductionPage(page: number): Promise<void> {
  if (plotId.value) {
    if (!selectedPlot.value) selectedPlot.value = await getPlot(plotId.value);
    const result = await getPlotProductions(plotId.value, "ACTIVE", page, PAGE_SIZE);
    const items = result.items.map((item) => toProductionOption(item, selectedPlot.value?.name || ""));
    options.value = page === 1 ? items : [...options.value, ...items];
    total.value = result.total;
  } else {
    const result = await getFarmProductions(farmId.value, {
      status: "ACTIVE",
      page,
      pageSize: PAGE_SIZE,
    });
    options.value = page === 1 ? result.items : [...options.value, ...result.items];
    total.value = result.total;
  }
  currentPage.value = page;
  hasMore.value = options.value.length < total.value;
}

async function loadProductions(): Promise<void> {
  if (!farmId.value && !plotId.value) {
    loadError.value = "农场信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  options.value = [];
  total.value = 0;
  currentPage.value = 1;
  hasMore.value = false;
  try {
    await fetchProductionPage(1);
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

async function loadMoreProductions(): Promise<void> {
  if (loading.value || loadingMore.value || !hasMore.value || loadError.value) return;
  loadingMore.value = true;
  try {
    await fetchProductionPage(currentPage.value + 1);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    uni.showToast({
      title: error instanceof ApiRequestError ? error.message : "更多种养加载失败",
      icon: "none",
    });
  } finally {
    loadingMore.value = false;
  }
}

function productionName(item: ProductionOption): string {
  return `${item.speciesName}${item.variety ? ` · ${item.variety}` : ""}`;
}

function productionMeta(item: ProductionOption): string {
  const quantity = item.initialQuantity === null
    ? ""
    : ` · 初始${formatNumber(item.initialQuantity)}${unitLabels[item.individualUnit]}`;
  return `${item.startedOn} 开始${quantity}`;
}

function chooseProduction(selection: ProductionOption): void {
  openerEventChannel?.emit("selected", { productionId: selection.id });
  uni.navigateBack();
}

onLoad((optionsValue) => {
  farmId.value = Number(optionsValue?.farmId || 0);
  plotId.value = Number(optionsValue?.plotId || 0);
  const currentSelection = Number(optionsValue?.selectedProductionId);
  selectedProductionId.value = Number.isInteger(currentSelection) && currentSelection > 0 ? currentSelection : null;
  const page = getCurrentInstance()?.proxy as unknown as {
    getOpenerEventChannel?: () => OpenerEventChannel;
  } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
  void loadProductions();
});

onReachBottom(() => {
  void loadMoreProductions();
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
  min-height: 128rpx;
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
.production-plot,
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

.production-plot {
  overflow: hidden;
  margin-top: 5rpx;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-label;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-meta {
  overflow: hidden;
  margin-top: 4rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-caption;
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
