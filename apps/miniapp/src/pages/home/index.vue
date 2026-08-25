<template>
  <view class="pf-page home-page">
    <PfPageHeader :title="hasFarm ? currentFarmName : '未选择农场'" variant="tab" />

    <view class="pf-page-content">
      <view class="welcome-panel">
        <text class="welcome-eyebrow">{{ dateLabel }}</text>
        <text class="welcome-title">{{ greeting }}，{{ displayName }}</text>
      </view>

      <template v-if="hasFarm">
        <view class="action-grid">
          <view class="action-card pf-tappable" @tap="openCreateProduction">
            <PfBusinessIcon name="sprout" />
            <text class="action-title">开始种养</text>
          </view>
          <view class="action-card pf-tappable" @tap="openCreateOperation">
            <PfBusinessIcon name="shovel" />
            <text class="action-title">记农事</text>
          </view>
          <view class="action-card pf-tappable" @tap="openCreateHarvest">
            <PfBusinessIcon name="shopping-basket" />
            <text class="action-title">记收获</text>
          </view>
          <view class="action-card pf-tappable" @tap="openPlotList">
            <PfBusinessIcon name="land-plot" />
            <text class="action-title">地块管理</text>
          </view>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">最近动态</text>
        </view>
        <view v-if="loadingDashboard" class="state-card pf-card">
          <uv-loading-icon mode="circle" color="#286B46" />
          <text>正在整理最近工作</text>
        </view>
        <view v-else-if="dashboardError" class="state-card pf-card">
          <uv-icon name="warning" size="25" color="#A9433B" />
          <text>{{ dashboardError }}</text>
          <text class="retry-action" @tap="loadDashboard">重新加载</text>
        </view>
        <view v-else-if="recentActivities.length" class="activity-list pf-list-card">
          <view
            v-for="item in recentActivities"
            :key="`${item.type}-${item.id}`"
            class="activity-row pf-tappable"
            @tap="openActivity(item)"
          >
            <PfBusinessIcon :name="item.type === 'harvest' ? 'shopping-basket' : 'shovel'" />
            <view class="activity-copy">
              <text class="activity-title">{{ activityTitle(item) }}</text>
              <text class="activity-meta">{{ formatActivityTime(item.timestamp) }} · {{ memberName(item.operatorId) }}</text>
            </view>
            <PfRowChevron />
          </view>
        </view>
        <view v-else class="empty-activity">
          <PfBusinessIcon name="clock-3" />
          <text class="empty-activity__title">还没有生产动态</text>
        </view>
      </template>

      <view v-else class="empty-state pf-card">
        <PfBusinessIcon name="map" size="empty" />
        <text class="empty-state__title">先创建一个农场</text>
        <uv-button type="primary" shape="square" custom-style="width: 100%; height: 88rpx; margin-top: 32rpx; border-radius: 16rpx;" @click="openCreateFarm">创建农场</uv-button>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfPageHeader from "../../components/PfPageHeader.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { getFarmMembers, type FarmMember } from "../../services/farm";
import { useFarmContext } from "../../services/farm-context";
import { getPlotHarvests, type HarvestRecord, type QuantityUnit } from "../../services/harvest";
import { ApiRequestError } from "../../services/http";
import { getPlotOperations, type FarmOperation } from "../../services/operation";
import { getFarmPlots, type Plot } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import { getCurrentUser, type User } from "../../services/user";
import { formatNumber } from "../../utils/number";
import type { Industry } from "../../services/species";

type HomeActivity =
  | { type: "operation"; id: number; timestamp: string; operatorId: number; plot: Plot; operation: FarmOperation }
  | { type: "harvest"; id: number; timestamp: string; operatorId: number; plot: Plot; harvest: HarvestRecord; production: Production | null };

interface PlotDashboardData {
  plot: Plot;
  productions: Production[];
  operations: FarmOperation[];
  harvests: HarvestRecord[];
}

const user = ref<User | null>(null);
const { currentFarm, currentFarmName, hasCurrentFarm, refreshFromApi } = useFarmContext();
const hasFarm = hasCurrentFarm;
const recentActivities = ref<HomeActivity[]>([]);
const members = ref<FarmMember[]>([]);
const loadingDashboard = ref(false);
const dashboardError = ref("");
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const displayName = computed(() => user.value?.nickname || maskPhone(user.value?.phoneNumber || "用户"));
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 11) return "早上好";
  if (hour < 13) return "中午好";
  if (hour < 18) return "下午好";
  return "晚上好";
});
const dateLabel = computed(() => {
  const date = new Date();
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  return `${date.getMonth() + 1}月${date.getDate()}日 · ${weekdays[date.getDay()]}`;
});

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function formatActivityTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  const today = new Date();
  const isToday = date.toDateString() === today.toDateString();
  const time = `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
  return isToday ? `今天 ${time}` : `${date.getMonth() + 1}月${date.getDate()}日 ${time}`;
}

function memberName(userId: number): string {
  return members.value.find((member) => member.userId === userId)?.nickname?.trim() || "未设置昵称";
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadDashboard(): Promise<void> {
  const farm = currentFarm.value;
  if (!farm) {
    recentActivities.value = [];
    members.value = [];
    return;
  }
  loadingDashboard.value = true;
  dashboardError.value = "";
  try {
    const [plotPage, memberPage] = await Promise.all([getFarmPlots(farm.id), getFarmMembers(farm.id)]);
    const plotData: PlotDashboardData[] = await Promise.all(
      plotPage.items.map(async (plot) => {
        const [productionPage, operationPage, harvestPage] = await Promise.all([
          getPlotProductions(plot.id, undefined, 1, 100),
          getPlotOperations(plot.id, 1, 5),
          getPlotHarvests(plot.id, 1, 5),
        ]);
        return { plot, productions: productionPage.items, operations: operationPage.items, harvests: harvestPage.items };
      }),
    );
    if (currentFarm.value?.id !== farm.id) return;
    members.value = memberPage.items;
    recentActivities.value = plotData
      .flatMap(({ plot, productions, operations, harvests }): HomeActivity[] => [
        ...operations.map((operation) => ({ type: "operation" as const, id: operation.id, timestamp: operation.operatedAt, operatorId: operation.operatorId, plot, operation })),
        ...harvests.map((harvest) => ({ type: "harvest" as const, id: harvest.id, timestamp: harvest.harvestedAt, operatorId: harvest.operatorId, plot, harvest, production: productions.find((production) => production.id === harvest.productionId) || null })),
      ])
      .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime())
      .slice(0, 5);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    dashboardError.value = error instanceof ApiRequestError ? error.message : "首页数据加载失败，请稍后重试";
  } finally {
    loadingDashboard.value = false;
  }
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

function openCreateProduction(): void {
  if (currentFarm.value) {
    uni.navigateTo({ url: `/pages/productions/start?farmId=${currentFarm.value.id}` });
  }
}

function openCreateOperation(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/operations/form?farmId=${currentFarm.value.id}` });
}

function openCreateHarvest(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/harvests/form?farmId=${currentFarm.value.id}` });
}

function openPlotList(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/farm-plots/index?farmId=${currentFarm.value.id}&filter=ALL` });
}

function openPlotOperations(plotId: number): void {
  uni.navigateTo({ url: `/pages/operations/index?plotId=${plotId}` });
}

function harvestActionLabel(industry?: Industry): string {
  if (industry === "LIVESTOCK") return "出栏";
  if (industry === "FISHERY") return "捕捞";
  return "采收";
}

function quantityUnitLabel(unit: QuantityUnit): string {
  const labels: Record<QuantityUnit, string> = { KG: "公斤", HEAD: "头", FEATHER: "羽", PIECE: "只/个", PLANT: "株", TAIL: "尾" };
  return labels[unit];
}

function activityTitle(activity: HomeActivity): string {
  if (activity.type === "operation") return `${activity.operation.operationType.name} · ${activity.plot.name}`;
  return `${harvestActionLabel(activity.production?.industry)} ${formatNumber(activity.harvest.quantity)} ${quantityUnitLabel(activity.harvest.unit)} · ${activity.plot.name}`;
}

function openActivity(activity: HomeActivity): void {
  if (activity.type === "operation") {
    openPlotOperations(activity.plot.id);
    return;
  }
  uni.navigateTo({ url: `/pages/harvests/index?productionId=${activity.harvest.productionId}` });
}

onShow(async () => {
  try {
    const [currentUser] = await Promise.all([getCurrentUser(), refreshFromApi()]);
    user.value = currentUser;
    await loadDashboard();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) handleUnauthorized();
  }
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.welcome-panel { padding: 30rpx 4rpx 26rpx; }
.welcome-eyebrow, .welcome-title, .action-title, .activity-title, .activity-meta, .empty-activity__title, .empty-state__title { display: block; }
.welcome-eyebrow { color: $pf-color-primary; font-size: 22rpx; font-weight: 600; }
.welcome-title { margin-top: 10rpx; color: $pf-color-text; font-size: 43rpx; font-weight: 720; letter-spacing: -1rpx; }
.action-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16rpx; }
.action-card { display: flex; min-height: 112rpx; box-sizing: border-box; align-items: center; padding: 20rpx 22rpx; border-radius: 20rpx; background: $pf-color-surface; box-shadow: $pf-shadow-card; }
.action-title { min-width: 0; margin-left: 16rpx; overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.activity-list { overflow: hidden; padding: 0; border: none; border-radius: 20rpx; box-shadow: $pf-shadow-card; }
.activity-row { display: flex; min-height: 116rpx; align-items: center; padding: 0 22rpx; }
.activity-row + .activity-row { border-top: 1rpx solid $pf-color-divider; }
.activity-copy { min-width: 0; flex: 1; margin: 0 18rpx; }
.activity-title { overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.activity-meta { margin-top: 7rpx; overflow: hidden; color: $pf-color-text-secondary; font-size: 22rpx; text-overflow: ellipsis; white-space: nowrap; }
.state-card { display: flex; min-height: 144rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 24rpx; border: none; color: $pf-color-text-secondary; font-size: 23rpx; }
.state-card text { margin-top: 12rpx; }
.retry-action { color: $pf-color-primary; font-weight: 600; }
.empty-activity { display: flex; min-height: 112rpx; align-items: center; padding: 0 24rpx; border-radius: 20rpx; background: $pf-color-surface; box-shadow: $pf-shadow-card; }
.empty-activity__title { margin-left: 16rpx; color: $pf-color-text; font-size: 25rpx; font-weight: 600; }
.empty-state { display: flex; flex-direction: column; align-items: center; margin-top: 32rpx; padding: 40rpx 28rpx 30rpx; border: none; text-align: center; }
.empty-state__title { margin-top: 24rpx; color: $pf-color-text; font-size: 31rpx; font-weight: 650; }
</style>
