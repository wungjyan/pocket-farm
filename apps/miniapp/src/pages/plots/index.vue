<template>
  <view class="pf-page plot-list-page">
    <view class="pf-page-content">
      <view class="list-toolbar">
        <picker
          class="filter-picker-wrap"
          mode="selector"
          :range="filterLabels"
          :value="filterIndex"
          @change="handleFilterChange"
        >
          <view
            class="filter-picker pf-tappable"
            :class="{ 'filter-picker--active': filterValue !== 'ALL' }"
            hover-class="filter-picker--pressed"
          >
            <text class="filter-picker__label">{{ selectedFilterLabel }}</text>
            <uv-icon name="arrow-down" size="14" :color="filterValue !== 'ALL' ? '#006C49' : '#53645A'" />
          </view>
        </picker>
        <view class="list-toolbar__right">
          <text class="list-toolbar__count">{{ loading ? "–" : `${plotTotal} 个地块` }}</text>
          <view v-if="canManagePlots" class="create-button pf-tappable" @tap="openCreatePlot">
            <uv-icon name="plus" size="14" color="#006C49" />
            <text>创建地块</text>
          </view>
        </view>
      </view>

      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#006C49" />
        <text>正在加载地块</text>
      </view>
      <view v-else-if="plots.length" class="plot-list">
        <view
          v-for="plot in plots"
          :key="plot.id"
          class="plot-row pf-card pf-tappable"
          :class="{ 'plot-row--selected': plot.id === selectedPlotId }"
          @tap="handlePlot(plot)"
        >
          <view class="plot-copy">
            <text class="plot-name">{{ plot.name }}</text>
            <view class="plot-meta">
              <text>{{ plotTypeLabel(plot.type) }}</text>
              <text class="plot-meta__separator">·</text>
              <text :class="{ 'plot-meta__incomplete': !hasArea(plot) }">{{ areaLabel(plot) }}</text>
            </view>
            <view class="species-tags">
              <text v-if="!plot.activeSpecies.length" class="species-tag species-tag--idle">空闲</text>
              <text v-for="species in plot.activeSpecies" :key="species.id" class="species-tag">{{ species.name }}</text>
            </view>
          </view>
          <view class="plot-selection" :class="{ 'plot-selection--selected': plot.id === selectedPlotId }">
            <uv-icon v-if="plot.id === selectedPlotId" name="checkmark" size="15" color="#006C49" />
          </view>
        </view>
      </view>
      <PfEmptyState
        v-else
        :icon="filterValue === 'ALL' ? 'land-plot' : 'search-x'"
        :title="filterValue === 'ALL' ? '还没有地块' : '没有符合条件的地块'"
        :action-text="filterValue === 'ALL' ? '' : '查看全部地块'"
        action-type="text"
        @action="clearFilter"
      />
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PfEmptyState from "../../components/PfEmptyState.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import {
  getFarmPlotFilterOptions,
  getFarmPlotSummaries,
  type ActiveSpeciesSummary,
  type Plot,
  type PlotSummary,
  type PlotSummaryFilter,
  type PlotType,
} from "../../services/plot";
import { formatNumber } from "../../utils/number";

type FilterValue = "ALL" | "IDLE" | `SPECIES:${number}`;

interface FilterOption {
  value: FilterValue;
  label: string;
}

const farmId = ref<number | null>(null);
const plots = ref<PlotSummary[]>([]);
const plotTotal = ref(0);
const filterValue = ref<FilterValue>("ALL");
const activeSpecies = ref<ActiveSpeciesSummary[]>([]);
const idlePlotCount = ref(0);
const loading = ref(false);
const selectedPlotId = ref<number | null>(null);
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const { currentFarm } = useFarmContext();
let openerEventChannel: { emit: (eventName: string, data: Plot) => void } | null = null;
const canManagePlots = computed(
  () => currentFarm.value?.id === farmId.value && (currentFarm.value.role === "OWNER" || currentFarm.value.role === "ADMIN"),
);
const filterOptions = computed<FilterOption[]>(() => [
  { value: "ALL", label: "全部种类" },
  ...activeSpecies.value.map((species) => ({
    value: `SPECIES:${species.id}` as const,
    label: species.name,
  })),
  ...(idlePlotCount.value > 0 ? [{ value: "IDLE" as const, label: "空闲地块" }] : []),
]);
const filterLabels = computed(() => filterOptions.value.map((item) => item.label));
const filterIndex = computed(() => Math.max(0, filterOptions.value.findIndex((item) => item.value === filterValue.value)));
const selectedFilterLabel = computed(() => filterOptions.value.find((item) => item.value === filterValue.value)?.label || "全部种类");

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

function handleFilterChange(event: { detail: { value: number | string } }): void {
  const selected = filterOptions.value[Number(event.detail.value)];
  if (!selected || selected.value === filterValue.value) return;
  filterValue.value = selected.value;
  loadPlots();
}

function clearFilter(): void {
  if (filterValue.value === "ALL") return;
  filterValue.value = "ALL";
  loadPlots();
}

async function loadPlots(): Promise<void> {
  if (!farmId.value) return;
  loading.value = true;
  try {
    const speciesId = filterValue.value.startsWith("SPECIES:")
      ? Number(filterValue.value.slice("SPECIES:".length))
      : undefined;
    const filter: PlotSummaryFilter = speciesId
      ? "SPECIES"
      : filterValue.value === "IDLE"
        ? "IDLE"
        : "ALL";
    const page = await getFarmPlotSummaries(farmId.value, {
      page: 1,
      pageSize: 100,
      filter,
      speciesId,
    });
    plots.value = page.items;
    plotTotal.value = page.total;
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

async function loadPageData(): Promise<void> {
  if (!farmId.value) return;
  loading.value = true;
  try {
    const options = await getFarmPlotFilterOptions(farmId.value);
    activeSpecies.value = options.activeSpecies;
    idlePlotCount.value = options.idlePlotCount;
    if (!filterOptions.value.some((item) => item.value === filterValue.value)) {
      filterValue.value = "ALL";
    }
    await loadPlots();
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

function handlePlot(plot: Plot): void {
  openerEventChannel?.emit("selected", plot);
  uni.navigateBack();
}

onLoad((query) => {
  uni.setNavigationBarTitle({ title: "选择地块" });
  const currentSelection = Number(query?.selectedPlotId);
  selectedPlotId.value = Number.isInteger(currentSelection) && currentSelection > 0 ? currentSelection : null;
  const id = Number(query?.farmId);
  farmId.value = Number.isInteger(id) && id > 0 ? id : currentFarm.value?.id || null;
  const page = getCurrentInstance()?.proxy as unknown as {
    getOpenerEventChannel?: () => { emit: (eventName: string, data: Plot) => void };
  } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
});

onShow(() => loadPageData());
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.list-toolbar {
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
  min-height: 72rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 $pf-space-3;
  border: 1rpx solid $pf-color-outline;
  border-radius: $pf-radius-pill;
  background: $pf-color-surface;
}

.filter-picker--pressed {
  background: $pf-color-surface-muted;
}

.filter-picker--active {
  background: $pf-color-primary-soft;
}

.filter-picker--active .filter-picker__label {
  color: $pf-color-primary;
}

.filter-picker__label {
  color: $pf-color-text;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
}

.filter-picker .uv-icon {
  margin-left: 8rpx;
}

.list-toolbar__count,
.plot-name {
  display: block;
}

.list-toolbar__right {
  display: flex;
  align-items: center;
}

.list-toolbar__count {
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.create-button {
  display: flex;
  min-height: 72rpx;
  align-items: center;
  margin-left: $pf-space-2;
  padding: 0 $pf-space-3;
  border-radius: $pf-radius-pill;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
}

.create-button .uv-icon {
  margin-right: 6rpx;
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

.plot-row--selected {
  background: $pf-color-primary-soft;
}

.plot-row--selected .species-tag {
  background: $pf-color-surface;
}

.plot-selection {
  display: flex;
  width: 36rpx;
  height: 36rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 2rpx solid $pf-color-border;
  border-radius: 50%;
  background: $pf-color-surface;
}

.plot-selection--selected {
  border-color: $pf-color-primary;
  background: $pf-color-surface;
}

.plot-copy {
  min-width: 0;
  flex: 1;
  margin-right: 16rpx;
}

.plot-name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plot-meta {
  display: flex;
  align-items: center;
  margin-top: 7rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.plot-meta__separator {
  margin: 0 $pf-space-1;
}

.plot-meta__incomplete {
  color: $pf-color-warning;
}

.species-tags {
  display: flex;
  flex-wrap: wrap;
  gap: $pf-space-1;
  margin-top: $pf-space-2;
}

.species-tag {
  display: block;
  padding: 5rpx 14rpx;
  border-radius: $pf-radius-pill;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: $pf-font-size-caption;
  line-height: 1.25;
}

.species-tag--idle {
  background: $pf-color-surface-muted;
  color: $pf-color-text-muted;
}

.state-card {
  display: flex;
  min-height: 160rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
}

.state-card text {
  margin-top: $pf-space-2;
}

</style>
