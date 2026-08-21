<template>
  <view class="pf-page plot-list-page">
    <view class="pf-page-content">
      <view class="list-toolbar">
        <view class="list-toolbar__copy">
          <text class="list-toolbar__eyebrow">{{ selectionMode ? "用于本次记录" : "当前农场" }}</text>
          <text class="list-toolbar__title">{{ selectionMode ? "选择一个地块" : `共 ${loading ? "–" : plots.length} 个地块` }}</text>
          <text class="list-toolbar__description">
            {{ selectionMode ? `当前农场共 ${loading ? "–" : plots.length} 个可选地块` : "点击地块查看生产详情" }}
          </text>
        </view>
        <view v-if="canManagePlots" class="create-button pf-tappable" @tap="openCreatePlot">
          <uv-icon name="plus" size="18" color="#286B46" />
          <text>创建地块</text>
        </view>
      </view>

      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#286B46" />
        <text>正在加载地块</text>
      </view>
      <view v-else-if="plots.length" class="plot-list pf-list-card">
        <view
          v-for="plot in plots"
          :key="plot.id"
          class="plot-row pf-tappable"
          :class="{ 'plot-row--selected': selectionMode && plot.id === selectedPlotId }"
          @tap="handlePlot(plot)"
        >
          <view class="plot-copy">
            <text class="plot-name">{{ plot.name }}</text>
            <view class="plot-meta">
              <text>{{ plotTypeLabel(plot.type) }}</text>
              <text class="plot-meta__separator">·</text>
              <text :class="{ 'plot-meta__incomplete': !hasArea(plot) }">{{ areaLabel(plot) }}</text>
            </view>
          </view>
          <uv-icon
            :name="selectionMode && plot.id === selectedPlotId ? 'checkmark-circle' : 'arrow-right'"
            size="17"
            :color="selectionMode && plot.id === selectedPlotId ? '#286B46' : '#7F8B82'"
          />
        </view>
      </view>
      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon"><uv-icon name="grid" size="25" color="#286B46" /></view>
        <text class="empty-state__title">还没有地块</text>
        <text class="empty-state__description">{{ emptyDescription }}</text>
        <uv-button
          v-if="canManagePlots"
          type="primary"
          shape="square"
          custom-style="width: 100%; height: 88rpx; margin-top: 32rpx; border-radius: 16rpx;"
          @click="openCreatePlot"
        >创建地块</uv-button>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import { getFarmPlots, type Plot, type PlotType } from "../../services/plot";
import { formatNumber } from "../../utils/number";

const farmId = ref<number | null>(null);
const plots = ref<Plot[]>([]);
const loading = ref(false);
const selectionMode = ref(false);
const selectedPlotId = ref<number | null>(null);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm } = useFarmContext();
let openerEventChannel: { emit: (eventName: string, data: Plot) => void } | null = null;
const emptyDescription = computed(() => selectionMode.value ? "请先创建地块，再继续当前操作。" : "建立地块后，就可以开始种养和记录生产。");
const canManagePlots = computed(
  () => currentFarm.value?.id === farmId.value && (currentFarm.value.role === "OWNER" || currentFarm.value.role === "ADMIN"),
);

const plotTypeLabels: Record<PlotType, string> = {
  FIELD: "大田", PADDY: "水田", GREENHOUSE: "大棚", ORCHARD: "果园",
  FOREST: "林地", POND: "鱼塘", BARN: "栏舍", OTHER: "其他",
};

function plotTypeLabel(type: PlotType | null): string {
  return type ? plotTypeLabels[type] : "未分类";
}

function areaLabel(plot: Plot): string {
  if (plot.areaValue === null || plot.areaValue === undefined || !plot.areaUnit) return "面积未填写";
  const units: Record<string, string> = { MU: "亩", SQUARE_METER: "平方米", HECTARE: "公顷" };
  return `${formatNumber(plot.areaValue)}${units[plot.areaUnit] || ""}`;
}

function hasArea(plot: Plot): boolean {
  return plot.areaValue !== null && plot.areaValue !== undefined && Boolean(plot.areaUnit);
}

async function loadPlots(): Promise<void> {
  if (!farmId.value) return;
  loading.value = true;
  try {
    const page = await getFarmPlots(farmId.value);
    plots.value = page.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
      return;
    }
    toastRef.value?.show({ type: "default", message: error instanceof ApiRequestError ? error.message : "地块加载失败" });
  } finally {
    loading.value = false;
  }
}

function openCreatePlot(): void {
  if (farmId.value) uni.navigateTo({ url: `/pages/plots/create?farmId=${farmId.value}` });
}

function openPlot(plotId: number): void {
  uni.navigateTo({ url: `/pages/plots/detail?plotId=${plotId}` });
}

function handlePlot(plot: Plot): void {
  if (!selectionMode.value) {
    openPlot(plot.id);
    return;
  }
  openerEventChannel?.emit("selected", plot);
  uni.navigateBack();
}

onLoad((query) => {
  selectionMode.value = query?.mode === "select";
  uni.setNavigationBarTitle({ title: selectionMode.value ? "选择地块" : "地块列表" });
  const currentSelection = Number(query?.selectedPlotId);
  selectedPlotId.value = Number.isInteger(currentSelection) && currentSelection > 0 ? currentSelection : null;
  const id = Number(query?.farmId);
  farmId.value = Number.isInteger(id) && id > 0 ? id : currentFarm.value?.id || null;
  const page = getCurrentInstance()?.proxy as unknown as {
    getOpenerEventChannel?: () => { emit: (eventName: string, data: Plot) => void };
  } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
});

onShow(() => loadPlots());
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.list-toolbar {
  display: flex;
  min-height: 142rpx;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 4rpx 22rpx;
}

.list-toolbar__copy {
  min-width: 0;
  flex: 1;
}

.list-toolbar__eyebrow,
.list-toolbar__title,
.list-toolbar__description,
.plot-name,
.empty-state__title,
.empty-state__description {
  display: block;
}

.list-toolbar__eyebrow {
  color: $pf-color-primary;
  font-size: 21rpx;
  font-weight: 600;
}

.list-toolbar__title {
  margin-top: 5rpx;
  color: $pf-color-text;
  font-size: 34rpx;
  font-weight: 700;
  line-height: 1.3;
}

.list-toolbar__description {
  margin-top: 7rpx;
  color: $pf-color-text-muted;
  font-size: 21rpx;
}

.create-button {
  display: flex;
  min-height: 80rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  margin-left: 24rpx;
  padding: 0 22rpx;
  border: 1rpx solid rgba(40, 107, 70, 0.12);
  border-radius: 18rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 23rpx;
  font-weight: 600;
}

.create-button text {
  margin-left: 7rpx;
}

.plot-list {
  padding: 6rpx 0;
}

.plot-row {
  display: flex;
  min-height: 116rpx;
  align-items: center;
  padding: 0 22rpx;
}

.plot-row + .plot-row {
  border-top: 1rpx solid $pf-color-divider;
}

.plot-row--selected {
  background: $pf-color-primary-soft;
}

.plot-copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}

.plot-name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-meta {
  display: flex;
  align-items: center;
  margin-top: 7rpx;
  color: $pf-color-text-muted;
  font-size: 21rpx;
}

.plot-meta__separator {
  margin: 0 8rpx;
}

.plot-meta__incomplete {
  color: $pf-color-warning;
}

.state-card {
  display: flex;
  min-height: 160rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}

.state-card text {
  margin-top: 14rpx;
}

.empty-state {
  padding: 42rpx 28rpx 30rpx;
  text-align: center;
}

.empty-state__icon {
  display: flex;
  width: 72rpx;
  height: 72rpx;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  border-radius: 22rpx;
  background: $pf-color-primary-soft;
}

.empty-state__title {
  margin-top: 24rpx;
  color: $pf-color-text;
  font-size: 30rpx;
  font-weight: 650;
}

.empty-state__description {
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
  line-height: 1.55;
}
</style>
