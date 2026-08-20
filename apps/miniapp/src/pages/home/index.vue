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
          <view class="action-card action-card--primary pf-tappable" @tap="openCreateProduction">
            <view class="action-icon action-icon--primary"><uv-icon name="plus" size="24" color="#FFFFFF" /></view>
            <view class="action-copy">
              <text class="action-title">开始种养</text>
              <text class="action-description">建立一批新的种养档案</text>
            </view>
            <uv-icon name="arrow-right" size="18" color="#FFFFFF" />
          </view>
          <view class="action-card pf-card pf-tappable" @tap="openCreateOperation">
            <view class="action-icon"><uv-icon name="edit-pen" size="21" color="#286B46" /></view>
            <view class="action-copy">
              <text class="action-title">记农事</text>
              <text class="action-description">记录今天的作业</text>
            </view>
          </view>
          <view class="action-card pf-card pf-tappable" @tap="openCreateHarvest">
            <view class="action-icon"><uv-icon name="order" size="21" color="#286B46" /></view>
            <view class="action-copy">
              <text class="action-title">记收获</text>
              <text class="action-description">登记采收或出栏</text>
            </view>
          </view>
          <view class="action-card pf-card pf-tappable" @tap="openPlotList">
            <view class="action-icon"><uv-icon name="grid" size="21" color="#286B46" /></view>
            <view class="action-copy">
              <text class="action-title">地块管理</text>
              <text class="action-description">查看生产现场</text>
            </view>
          </view>
        </view>

        <view class="farm-glance pf-card pf-tappable" @tap="openFarm">
          <view class="farm-glance__copy">
            <text class="farm-glance__eyebrow">当前农场</text>
            <text class="farm-glance__name">{{ currentFarmName }}</text>
          </view>
          <view class="farm-glance__stat">
            <text class="farm-glance__value">{{ loadingDashboard ? "–" : plots.length }}</text>
            <text class="farm-glance__label">地块</text>
          </view>
          <view class="farm-glance__stat">
            <text class="farm-glance__value">{{ loadingDashboard ? "–" : activeProductionCount }}</text>
            <text class="farm-glance__label">进行中</text>
          </view>
          <uv-icon name="arrow-right" size="17" color="#7F8B82" />
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">最近动态</text>
          <text class="pf-section-note">{{ recentActivities.length ? "最近 5 条" : "暂无记录" }}</text>
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
            v-for="(item, index) in recentActivities"
            :key="`${item.type}-${item.id}`"
            class="activity-row pf-tappable"
            @tap="openActivity(item)"
          >
            <view class="activity-timeline">
              <view class="activity-icon">
                <uv-icon :name="item.type === 'harvest' ? 'order' : 'calendar'" size="18" color="#286B46" />
              </view>
              <view v-if="index < recentActivities.length - 1" class="activity-line" />
            </view>
            <view class="activity-copy">
              <text class="activity-title">{{ activityTitle(item) }}</text>
              <text class="activity-meta">{{ formatActivityTime(item.timestamp) }} · {{ memberName(item.operatorId) }}</text>
            </view>
            <uv-icon name="arrow-right" size="16" color="#7F8B82" />
          </view>
        </view>
        <view v-else class="empty-activity pf-card">
          <view class="empty-activity__icon"><uv-icon name="clock" size="22" color="#536158" /></view>
          <view>
            <text class="empty-activity__title">还没有生产动态</text>
            <text class="empty-activity__description">完成一条农事或收获记录后，会显示在这里。</text>
          </view>
        </view>
      </template>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon"><uv-icon name="map" size="27" color="#286B46" /></view>
        <text class="empty-state__title">先创建一个农场</text>
        <text class="empty-state__description">农场建立后，工作台会汇总你的生产入口与最近动态。</text>
        <uv-button type="primary" shape="square" custom-style="width: 100%; height: 88rpx; margin-top: 32rpx; border-radius: 16rpx;" @click="openCreateFarm">创建农场</uv-button>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
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
const plots = ref<Plot[]>([]);
const recentActivities = ref<HomeActivity[]>([]);
const members = ref<FarmMember[]>([]);
const activeProductionCount = ref(0);
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
    plots.value = [];
    recentActivities.value = [];
    activeProductionCount.value = 0;
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
    plots.value = plotPage.items;
    members.value = memberPage.items;
    activeProductionCount.value = plotData.reduce(
      (total, item) => total + item.productions.filter((production) => production.status === "ACTIVE").length,
      0,
    );
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
    uni.navigateTo({ url: `/pages/species/index?purpose=production&farmId=${currentFarm.value.id}` });
  }
}

function openCreateOperation(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/operations/form?farmId=${currentFarm.value.id}` });
}

function openCreateHarvest(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/harvests/form?farmId=${currentFarm.value.id}` });
}

function openFarm(): void {
  uni.switchTab({ url: "/pages/farm/index" });
}

function openPlotList(): void {
  if (currentFarm.value) uni.navigateTo({ url: `/pages/plots/index?farmId=${currentFarm.value.id}` });
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

.welcome-panel { padding: 34rpx 4rpx 28rpx; }
.welcome-eyebrow, .welcome-title, .action-title, .action-description, .farm-glance__eyebrow, .farm-glance__name, .farm-glance__value, .farm-glance__label, .activity-title, .activity-meta, .empty-activity__title, .empty-activity__description, .empty-state__title, .empty-state__description { display: block; }
.welcome-eyebrow { color: $pf-color-primary; font-size: 22rpx; font-weight: 600; }
.welcome-title { margin-top: 10rpx; color: $pf-color-text; font-size: 43rpx; font-weight: 720; letter-spacing: -1rpx; }
.action-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16rpx; }
.action-card { display: flex; min-height: 126rpx; box-sizing: border-box; align-items: center; padding: 24rpx; }
.action-card--primary { grid-column: 1 / -1; min-height: 118rpx; border-radius: $pf-radius-card-lg; background: $pf-color-primary; box-shadow: $pf-shadow-raised; color: $pf-white; }
.action-icon { display: flex; width: 52rpx; height: 52rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 16rpx; background: $pf-color-primary-soft; }
.action-icon--primary { width: 58rpx; height: 58rpx; background: rgba(255, 255, 255, 0.14); }
.action-copy { min-width: 0; flex: 1; margin-left: 16rpx; }
.action-title { color: $pf-color-text; font-size: 27rpx; font-weight: 650; }
.action-description { margin-top: 6rpx; color: $pf-color-text-muted; font-size: 20rpx; line-height: 1.35; }
.action-card--primary .action-title { color: $pf-white; font-size: 29rpx; }
.action-card--primary .action-description { color: rgba(255, 255, 255, 0.72); font-size: 21rpx; }
.farm-glance { display: flex; min-height: 104rpx; align-items: center; margin-top: 20rpx; padding: 18rpx 22rpx; }
.farm-glance__copy { min-width: 0; flex: 1; }
.farm-glance__eyebrow { color: $pf-color-text-muted; font-size: 20rpx; }
.farm-glance__name { max-width: 220rpx; margin-top: 5rpx; overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.farm-glance__stat { width: 88rpx; text-align: center; }
.farm-glance__value { color: $pf-color-text; font-size: 29rpx; font-weight: 700; }
.farm-glance__label { margin-top: 3rpx; color: $pf-color-text-muted; font-size: 19rpx; }
.activity-list { padding: 8rpx 0; }
.activity-row { display: flex; min-height: 108rpx; align-items: center; padding: 0 22rpx; }
.activity-timeline { position: relative; align-self: stretch; display: flex; width: 56rpx; flex-shrink: 0; align-items: center; justify-content: center; }
.activity-icon { z-index: 1; display: flex; width: 48rpx; height: 48rpx; align-items: center; justify-content: center; border-radius: 50%; background: $pf-color-primary-soft; }
.activity-line { position: absolute; top: 78rpx; bottom: -30rpx; left: 50%; width: 1rpx; background: $pf-color-divider; }
.activity-copy { min-width: 0; flex: 1; margin: 0 16rpx; }
.activity-title { overflow: hidden; color: $pf-color-text; font-size: 26rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.activity-meta { margin-top: 7rpx; overflow: hidden; color: $pf-color-text-muted; font-size: 21rpx; text-overflow: ellipsis; white-space: nowrap; }
.state-card { display: flex; min-height: 144rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 24rpx; color: $pf-color-text-secondary; font-size: 23rpx; }
.state-card text { margin-top: 12rpx; }
.retry-action { color: $pf-color-primary; font-weight: 600; }
.empty-activity { display: flex; min-height: 126rpx; align-items: center; padding: 24rpx; }
.empty-activity__icon { display: flex; width: 54rpx; height: 54rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 17rpx; background: $pf-color-surface-muted; }
.empty-activity > view:last-child { margin-left: 16rpx; }
.empty-activity__title { color: $pf-color-text; font-size: 25rpx; font-weight: 600; }
.empty-activity__description { margin-top: 6rpx; color: $pf-color-text-muted; font-size: 21rpx; line-height: 1.45; }
.empty-state { margin-top: 32rpx; padding: 40rpx 28rpx 30rpx; text-align: center; }
.empty-state__icon { display: flex; width: 72rpx; height: 72rpx; align-items: center; justify-content: center; margin: 0 auto; border-radius: 22rpx; background: $pf-color-primary-soft; }
.empty-state__title { margin-top: 24rpx; color: $pf-color-text; font-size: 31rpx; font-weight: 650; }
.empty-state__description { margin-top: 10rpx; color: $pf-color-text-secondary; font-size: 24rpx; line-height: 1.55; }
</style>
