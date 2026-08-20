<template>
  <view class="pf-page harvests-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#286B46" />
      <text>正在加载收获记录</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadHarvests">重试</uv-button>
    </view>
    <template v-else-if="plot">
      <view class="page-intro">
        <view>
          <text class="page-title">{{ production ? `${actionLabel}记录` : "收获记录" }}</text>
          <text class="page-description">{{ pageDescription }}</text>
        </view>
        <text v-if="canCreate" class="page-action" @click="openCreate">记录{{ production ? actionLabel : "收获" }}</text>
      </view>

      <view v-if="harvests.length" class="harvest-list">
        <view
          v-for="harvest in harvests"
          :key="harvest.id"
          class="harvest-card pf-card"
          :class="{ 'harvest-card--locked': isLocked(harvest) }"
          @click="openEdit(harvest)"
        >
          <view class="harvest-icon"><uv-icon name="order" size="21" color="#286B46" /></view>
          <view class="harvest-copy">
            <view class="harvest-title-line">
              <text class="harvest-name">{{ harvest.productName || productionFor(harvest)?.speciesName || "收获" }}</text>
              <text class="harvest-quantity">{{ formatNumber(harvest.quantity) }} {{ unitLabel(harvest.unit) }}</text>
              <text v-if="isLocked(harvest)" class="harvest-lock">已锁定</text>
            </view>
            <text class="harvest-meta">{{ harvestDateLabel(harvest.harvestedAt) }}{{ productionMeta(harvest) }}</text>
            <text class="harvest-meta">操作人：{{ memberName(harvest.operatorId) }}{{ creatorLabel(harvest) }}</text>
          </view>
          <view v-if="!isLocked(harvest)" class="harvest-delete" @click.stop="confirmDelete(harvest)">
            <uv-icon name="trash" size="18" color="#C96A45" />
          </view>
          <uv-icon v-else name="lock" size="17" color="#929A93" />
        </view>
      </view>
      <view v-else class="empty-card pf-card">
        <uv-icon name="order" size="30" color="#286B46" />
        <text class="empty-card__title">还没有收获记录</text>
        <text class="empty-card__description">每次采收、捕捞或出栏都可以单独记录。</text>
        <uv-button v-if="canCreate" type="primary" size="small" shape="square" custom-style="margin-top: 24rpx; border-radius: 12rpx;" @click="openCreate">记录收获</uv-button>
      </view>
    </template>
    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { getFarmMembers, type FarmMember } from "../../services/farm";
import {
  deleteHarvest,
  getPlotHarvests,
  getProductionHarvests,
  type HarvestRecord,
  type QuantityUnit,
} from "../../services/harvest";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot } from "../../services/plot";
import { getPlotProductions, getProduction, type Production } from "../../services/production";
import { formatNumber } from "../../utils/number";

const unitLabels: Record<QuantityUnit, string> = {
  KG: "公斤",
  HEAD: "头",
  FEATHER: "羽",
  PIECE: "只/个",
  PLANT: "株",
  TAIL: "尾",
};

const productionId = ref(0);
const plotId = ref(0);
const production = ref<Production | null>(null);
const plot = ref<Plot | null>(null);
const productions = ref<Production[]>([]);
const harvests = ref<HarvestRecord[]>([]);
const members = ref<FarmMember[]>([]);
const loading = ref(true);
const loadError = ref("");
const deletingId = ref(0);
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const actionLabel = computed(() => {
  if (production.value?.industry === "LIVESTOCK") return "出栏";
  if (production.value?.industry === "FISHERY") return "捕捞";
  return "采收";
});
const pageDescription = computed(() => production.value
  ? `${production.value.speciesName}${production.value.variety ? ` · ${production.value.variety}` : ""} · 共 ${harvests.value.length} 条`
  : `${plot.value?.name || "地块"} · 共 ${harvests.value.length} 条`);
const canCreate = computed(() => production.value
  ? production.value.status === "ACTIVE"
  : productions.value.some((item) => item.status === "ACTIVE"));

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function productionFor(harvest: HarvestRecord): Production | null {
  if (production.value?.id === harvest.productionId) return production.value;
  return productions.value.find((item) => item.id === harvest.productionId) || null;
}

function isLocked(harvest: HarvestRecord): boolean {
  return productionFor(harvest)?.status !== "ACTIVE";
}

function unitLabel(unit: QuantityUnit): string {
  return unitLabels[unit];
}

function harvestDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function productionMeta(harvest: HarvestRecord): string {
  if (production.value) return harvest.grade ? ` · ${harvest.grade}` : "";
  const target = productionFor(harvest);
  return target ? ` · ${target.speciesName}${target.variety ? ` · ${target.variety}` : ""}` : "";
}

function memberName(userId: number): string {
  return members.value.find((member) => member.userId === userId)?.nickname?.trim() || "未设置昵称";
}

function creatorLabel(harvest: HarvestRecord): string {
  return harvest.createdBy === harvest.operatorId ? "" : ` · 记录人：${memberName(harvest.createdBy)}`;
}

async function loadHarvests(): Promise<void> {
  if (!productionId.value && !plotId.value) {
    loadError.value = "收获记录信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    if (productionId.value) {
      const productionResult = await getProduction(productionId.value);
      const plotResult = await getPlot(productionResult.plotId);
      const [harvestPage, memberPage] = await Promise.all([
        getProductionHarvests(productionResult.id),
        getFarmMembers(plotResult.farmId),
      ]);
      production.value = productionResult;
      productions.value = [productionResult];
      plot.value = plotResult;
      plotId.value = plotResult.id;
      harvests.value = harvestPage.items;
      members.value = memberPage.items;
      return;
    }
    const plotResult = await getPlot(plotId.value);
    const [harvestPage, productionPage, memberPage] = await Promise.all([
      getPlotHarvests(plotResult.id),
      getPlotProductions(plotResult.id),
      getFarmMembers(plotResult.farmId),
    ]);
    plot.value = plotResult;
    harvests.value = harvestPage.items;
    productions.value = productionPage.items;
    members.value = memberPage.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "收获记录加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openCreate(): void {
  if (production.value) {
    uni.navigateTo({ url: `/pages/harvests/form?productionId=${production.value.id}` });
  } else if (plot.value) {
    uni.navigateTo({ url: `/pages/harvests/form?farmId=${plot.value.farmId}&plotId=${plot.value.id}` });
  }
}

function openEdit(harvest: HarvestRecord): void {
  if (isLocked(harvest)) return;
  uni.navigateTo({ url: `/pages/harvests/form?productionId=${harvest.productionId}&harvestId=${harvest.id}` });
}

function confirmDelete(harvest: HarvestRecord): void {
  if (deletingId.value || isLocked(harvest)) return;
  uni.showModal({
    title: "删除收获记录？",
    content: "删除后无法恢复，确定要继续吗？",
    confirmColor: "#C96A45",
    success: async (result) => {
      if (!result.confirm) return;
      deletingId.value = harvest.id;
      try {
        await deleteHarvest(harvest.id);
        harvests.value = harvests.value.filter((item) => item.id !== harvest.id);
        uni.showToast({ title: "已删除", icon: "none" });
      } catch (error) {
        if (error instanceof ApiRequestError && error.statusCode === 401) {
          handleUnauthorized();
        } else {
          toastRef.value?.error(error instanceof ApiRequestError ? error.message : "删除失败，请稍后再试");
        }
      } finally {
        deletingId.value = 0;
      }
    },
  });
}

onLoad((options) => {
  productionId.value = Number(options?.productionId || 0);
  plotId.value = Number(options?.plotId || 0);
});

onShow(() => {
  if ((productionId.value || plotId.value) && !deletingId.value) loadHarvests();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.harvests-page { padding: 28rpx $pf-space-page-x $pf-space-page-bottom; }
.page-intro { display: flex; align-items: center; justify-content: space-between; padding: 12rpx 4rpx 28rpx; }
.page-title, .page-description { display: block; }
.page-title { color: $pf-color-text; font-size: 38rpx; font-weight: 700; }
.page-description { margin-top: 10rpx; color: $pf-color-text-secondary; font-size: 24rpx; }
.page-action { flex-shrink: 0; margin-left: 20rpx; color: $pf-color-harvest; font-size: 25rpx; }
.harvest-list { display: flex; flex-direction: column; gap: 14rpx; }
.harvest-card { display: flex; min-height: 126rpx; align-items: center; padding: 16rpx 20rpx; border-left: 5rpx solid $pf-color-harvest; }
.harvest-card--locked { border-left-color: $pf-color-border; background: $pf-color-surface-muted; }
.harvest-icon { display: flex; width: 60rpx; height: 60rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 18rpx; background: $pf-color-harvest-soft; }
.harvest-copy { min-width: 0; flex: 1; margin: 0 16rpx; }
.harvest-title-line { display: flex; min-width: 0; align-items: center; }
.harvest-name { overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.harvest-quantity { flex-shrink: 0; margin-left: 12rpx; color: $pf-color-harvest; font-size: 24rpx; font-weight: 600; }
.harvest-lock { flex-shrink: 0; margin-left: 10rpx; padding: 3rpx 8rpx; border-radius: 8rpx; background: #e2e6e0; color: $pf-color-text-muted; font-size: 19rpx; }
.harvest-meta { display: block; margin-top: 5rpx; overflow: hidden; color: $pf-color-text-muted; font-size: 21rpx; text-overflow: ellipsis; white-space: nowrap; }
.harvest-delete { display: flex; width: 48rpx; height: 48rpx; align-items: center; justify-content: center; }
.empty-card, .state-card { display: flex; min-height: 220rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 28rpx; color: $pf-color-text-secondary; font-size: 24rpx; text-align: center; }
.empty-card__title, .empty-card__description { display: block; }
.empty-card__title { margin-top: 14rpx; color: $pf-color-text; font-size: 27rpx; font-weight: 600; }
.empty-card__description { margin-top: 10rpx; color: $pf-color-text-muted; font-size: 22rpx; line-height: 1.5; }
.state-card text { margin-top: 16rpx; }
</style>
