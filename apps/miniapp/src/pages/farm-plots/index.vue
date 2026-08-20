<template>
  <view class="pf-page farm-plots-page">
    <view class="pf-page-content">
      <view class="filter-toolbar">
        <picker
          class="filter-picker-wrap"
          mode="selector"
          :range="filterLabels"
          :value="filterIndex"
          @change="handleFilterChange"
        >
          <view class="filter-picker pf-tappable" hover-class="filter-picker--pressed">
            <text class="filter-picker__label">{{ selectedFilterLabel }}</text>
            <uv-icon name="arrow-down" size="15" color="#7F8B82" />
          </view>
        </picker>
        <text class="filter-count">{{ loading ? "–" : `${filteredPlotItems.length} 个地块` }}</text>
      </view>

      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#286B46" />
        <text>正在加载地块</text>
      </view>
      <view v-else-if="filteredPlotItems.length" class="plot-list">
        <view
          v-for="item in filteredPlotItems"
          :key="item.plot.id"
          class="plot-row pf-card pf-tappable"
          @tap="openPlot(item.plot.id)"
        >
          <view class="plot-copy">
            <text class="plot-name">{{ item.plot.name }}</text>
            <text class="plot-meta">{{ plotTypeLabel(item.plot.type) }} · {{ areaLabel(item.plot) }}</text>
            <view class="species-tags">
              <text v-if="!item.activeProductions.length" class="species-tag species-tag--idle">空闲</text>
              <text v-for="species in item.species" :key="species.id" class="species-tag">{{ species.name }}</text>
            </view>
          </view>
          <PfRowChevron />
        </view>
      </view>
      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon"><uv-icon name="grid" size="25" color="#286B46" /></view>
        <text class="empty-state__title">没有符合条件的地块</text>
        <text v-if="filterValue !== 'ALL'" class="empty-state__action pf-tappable" @tap="clearFilter">查看全部地块</text>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import { getFarmPlots, type Plot, type PlotType } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import { formatNumber } from "../../utils/number";

type FilterValue = "ALL" | "IDLE" | `SPECIES:${number}`;

interface SpeciesOption {
  id: number;
  name: string;
}

interface FarmPlotItem {
  plot: Plot;
  activeProductions: Production[];
  species: SpeciesOption[];
}

interface FilterOption {
  value: FilterValue;
  label: string;
}

const farmId = ref(0);
const filterValue = ref<FilterValue>("ALL");
const plotItems = ref<FarmPlotItem[]>([]);
const loading = ref(false);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm } = useFarmContext();

const plotTypeLabels: Record<PlotType, string> = {
  FIELD: "大田",
  PADDY: "水田",
  GREENHOUSE: "大棚",
  ORCHARD: "果园",
  FOREST: "林地",
  POND: "鱼塘",
  BARN: "栏舍",
  OTHER: "其他",
};

const speciesOptions = computed<SpeciesOption[]>(() => {
  const species = new Map<number, string>();
  plotItems.value.forEach((item) => item.activeProductions.forEach((production) => species.set(production.speciesId, production.speciesName)));
  return Array.from(species, ([id, name]) => ({ id, name })).sort((left, right) => left.name.localeCompare(right.name, "zh-CN"));
});

const filterOptions = computed<FilterOption[]>(() => [
  { value: "ALL", label: "全部种类" },
  ...speciesOptions.value.map((species) => ({ value: `SPECIES:${species.id}` as const, label: species.name })),
  { value: "IDLE", label: "空闲地块" },
]);
const filterLabels = computed(() => filterOptions.value.map((item) => item.label));
const filterIndex = computed(() => Math.max(0, filterOptions.value.findIndex((item) => item.value === filterValue.value)));
const selectedFilterLabel = computed(() => filterOptions.value.find((item) => item.value === filterValue.value)?.label || "全部种类");
const filteredPlotItems = computed(() => {
  if (filterValue.value === "ALL") return plotItems.value;
  if (filterValue.value === "IDLE") return plotItems.value.filter((item) => !item.activeProductions.length);
  const speciesId = Number(filterValue.value.slice("SPECIES:".length));
  return plotItems.value.filter((item) => item.activeProductions.some((production) => production.speciesId === speciesId));
});

function plotTypeLabel(type: PlotType | null): string {
  return type ? plotTypeLabels[type] : "未分类";
}

function areaLabel(plot: Plot): string {
  if (plot.areaValue === null || plot.areaValue === undefined || !plot.areaUnit) return "面积未填写";
  const units: Record<string, string> = { MU: "亩", SQUARE_METER: "平方米", HECTARE: "公顷" };
  return `${formatNumber(plot.areaValue)}${units[plot.areaUnit] || ""}`;
}

function handleFilterChange(event: { detail: { value: number | string } }): void {
  const selected = filterOptions.value[Number(event.detail.value)];
  if (selected) filterValue.value = selected.value;
}

function clearFilter(): void {
  filterValue.value = "ALL";
}

function openPlot(plotId: number): void {
  uni.navigateTo({ url: `/pages/plots/detail?plotId=${plotId}` });
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadPlots(): Promise<void> {
  const currentFarmId = currentFarm.value?.id || 0;
  if (currentFarmId && farmId.value && currentFarmId !== farmId.value) {
    farmId.value = currentFarmId;
    filterValue.value = "ALL";
  }
  const targetFarmId = currentFarmId || farmId.value;
  if (!targetFarmId) {
    plotItems.value = [];
    return;
  }
  farmId.value = targetFarmId;
  loading.value = true;
  try {
    const page = await getFarmPlots(targetFarmId);
    const activeProductions = await Promise.all(
      page.items.map(async (plot) => {
        const productionPage = await getPlotProductions(plot.id, "ACTIVE", 1, 100);
        return productionPage.items;
      }),
    );
    if (currentFarm.value?.id && currentFarm.value.id !== targetFarmId) return;
    plotItems.value = page.items.map((plot, index) => {
      const productions = activeProductions[index] || [];
      const species = Array.from(
        new Map(productions.map((production) => [production.speciesId, { id: production.speciesId, name: production.speciesName }])).values(),
      );
      return { plot, activeProductions: productions, species };
    });
    if (!filterOptions.value.some((item) => item.value === filterValue.value)) filterValue.value = "ALL";
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    toastRef.value?.show({ type: "default", message: error instanceof ApiRequestError ? error.message : "地块加载失败" });
  } finally {
    loading.value = false;
  }
}

onLoad((query) => {
  const parsedFarmId = Number(query?.farmId || 0);
  farmId.value = Number.isInteger(parsedFarmId) && parsedFarmId > 0 ? parsedFarmId : currentFarm.value?.id || 0;
  filterValue.value = query?.filter === "IDLE" ? "IDLE" : "ALL";
  uni.setNavigationBarTitle({ title: "地块列表" });
});

onShow(() => loadPlots());
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.filter-toolbar {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  justify-content: space-between;
  padding: 0 4rpx 10rpx;
}

.filter-picker-wrap {
  display: block;
}

.filter-picker {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 16rpx;
  border-radius: $pf-radius-control;
}

.filter-picker--pressed {
  background: $pf-color-surface-muted;
}

.filter-picker__label {
  color: $pf-color-text-secondary;
  font-size: 25rpx;
  font-weight: 550;
}

.filter-picker .uv-icon {
  margin-left: 8rpx;
}

.filter-count {
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.plot-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.plot-row {
  display: flex;
  min-height: 148rpx;
  align-items: center;
  padding: 0 22rpx;
}

.plot-copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}

.plot-name,
.plot-meta,
.empty-state__title,
.empty-state__action {
  display: block;
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
  margin-top: 7rpx;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.species-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 12rpx;
}

.species-tag {
  display: block;
  padding: 5rpx 14rpx;
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 20rpx;
  line-height: 1.25;
}

.species-tag--idle {
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
}

.state-card {
  display: flex;
  min-height: 180rpx;
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
  padding: 42rpx 28rpx 36rpx;
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
  font-size: 28rpx;
  font-weight: 650;
}

.empty-state__action {
  margin-top: 16rpx;
  color: $pf-color-primary;
  font-size: 23rpx;
  font-weight: 600;
}
</style>
