<template>
  <view class="pf-page home-page">
    <PfPageHeader :title="currentFarmName" />

    <view class="pf-page-content">
      <view class="welcome-panel">
        <text class="eyebrow">今日工作台</text>
        <text class="welcome-title">{{ greeting }}，{{ displayName }}</text>
        <text class="welcome-description">记录今天的种养和农事，让生产过程清清楚楚。</text>
      </view>

      <template v-if="hasFarm">
        <view class="overview-card pf-card">
          <view class="overview-item" @click="openFarm">
            <text class="overview-value">{{ loadingDashboard ? "-" : plots.length }}</text>
            <text class="overview-label">地块</text>
          </view>
          <view class="overview-divider" />
          <view class="overview-item" @click="openFarm">
            <text class="overview-value">{{ loadingDashboard ? "-" : activeProductionCount }}</text>
            <text class="overview-label">进行中种养</text>
          </view>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">当前种养</text>
          <text class="pf-section-action" @tap="openFarm">查看全部</text>
        </view>
        <view v-if="loadingDashboard" class="state-card pf-card">
          <uv-loading-icon mode="circle" color="#2F7D4A" />
          <text>正在加载生产现场</text>
        </view>
        <view v-else-if="dashboardError" class="state-card pf-card">
          <uv-icon name="warning" size="26" color="#C96A45" />
          <text>{{ dashboardError }}</text>
          <text class="retry-action" @click="loadDashboard">重试</text>
        </view>
        <view v-else-if="activeProductions.length" class="production-list">
          <view
            v-for="item in activeProductions"
            :key="item.id"
            class="production-card pf-card"
            @tap="openProduction(item.id)"
          >
            <view class="production-card__copy">
              <text class="production-card__name">{{ productionName(item) }}</text>
              <text class="production-card__plot">{{ item.plotName }}</text>
              <text class="production-card__meta">{{ productionMeta(item) }}</text>
            </view>
            <uv-icon name="arrow-right" size="17" color="#929A93" />
          </view>
        </view>
        <view v-else class="empty-card pf-card">
          <uv-icon name="list" size="27" color="#2F7D4A" />
          <view>
            <text class="empty-card__title">当前还没有种养</text>
            <text class="empty-card__description">选择一个地块，开始记录这次种养。</text>
          </view>
          <text class="empty-card__action" @tap="openCreateProduction">开始种养</text>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">快捷记录</text>
          <text class="pf-section-note">随手记下今天的工作</text>
        </view>
        <view class="quick-actions">
          <view class="quick-action" @tap="openCreateProduction">
            <uv-icon name="plus" size="20" color="#2F7D4A" />
            <text>开始种养</text>
          </view>
          <view class="quick-action" @tap="openCreateOperation">
            <uv-icon name="edit-pen" size="20" color="#2F7D4A" />
            <text>记农事</text>
          </view>
          <view class="quick-action" @tap="showHarvestComingSoon">
            <uv-icon name="order" size="20" color="#2F7D4A" />
            <text>收获</text>
          </view>
        </view>

        <view class="pf-section-heading">
          <text class="pf-section-title">最近动态</text>
          <text class="pf-section-note">{{ recentOperations.length ? "最新农事记录" : "暂无记录" }}</text>
        </view>
        <view v-if="loadingDashboard" class="state-card state-card--compact pf-card">
          <uv-loading-icon mode="circle" color="#2F7D4A" />
        </view>
        <view v-else-if="!dashboardError && recentOperations.length" class="operation-list pf-card">
          <view
            v-for="item in recentOperations"
            :key="item.operation.id"
            class="operation-row"
            @tap="openPlotOperations(item.plot.id)"
          >
            <view class="operation-icon"><uv-icon name="calendar" size="19" color="#2F7D4A" /></view>
            <view class="operation-copy">
              <text class="operation-title">{{ item.operation.operationType.name }} · {{ item.plot.name }}</text>
              <text class="operation-meta">{{ formatOperationTime(item.operation.operatedAt) }} · {{ memberName(item.operation.operatorId) }}</text>
            </view>
            <uv-icon name="arrow-right" size="16" color="#929A93" />
          </view>
        </view>
        <view v-else-if="!dashboardError" class="empty-card empty-card--plain pf-card">
          <uv-icon name="clock" size="23" color="#929A93" />
          <text class="empty-card__description">完成第一条农事记录后，动态会显示在这里。</text>
        </view>
      </template>

      <view v-else class="empty-state pf-card">
        <view class="empty-state__icon"><uv-icon name="map" size="28" color="#2F7D4A" /></view>
        <text class="empty-state__title">还没有农场</text>
        <text class="empty-state__description">创建一个农场，开始记录你的生产现场。</text>
        <uv-button type="primary" shape="square" custom-style="width: 100%; height: 84rpx; margin-top: 28rpx; border-radius: 16rpx;" @click="openCreateFarm">创建农场</uv-button>
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
import { ApiRequestError } from "../../services/http";
import { getPlotOperations, type FarmOperation } from "../../services/operation";
import { getFarmPlots, type Plot } from "../../services/plot";
import { getPlotProductions, type Production } from "../../services/production";
import { getCurrentUser, type User } from "../../services/user";

interface HomeProduction extends Production {
  plotName: string;
}

interface HomeOperation {
  operation: FarmOperation;
  plot: Plot;
}

const user = ref<User | null>(null);
const { currentFarm, currentFarmName, hasCurrentFarm, refreshFromApi } = useFarmContext();
const hasFarm = hasCurrentFarm;
const plots = ref<Plot[]>([]);
const activeProductions = ref<HomeProduction[]>([]);
const recentOperations = ref<HomeOperation[]>([]);
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

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function productionName(production: HomeProduction): string {
  return `${production.speciesName}${production.variety ? ` · ${production.variety}` : ""}`;
}

function productionMeta(production: HomeProduction): string {
  const startedOn = new Date(`${production.startedOn}T00:00:00`);
  const days = Math.max(0, Math.floor((Date.now() - startedOn.getTime()) / 86_400_000));
  return `${formatMonthDay(production.startedOn)}开始 · 已种养 ${days} 天`;
}

function formatMonthDay(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function formatOperationTime(value: string): string {
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
    activeProductions.value = [];
    recentOperations.value = [];
    activeProductionCount.value = 0;
    return;
  }
  loadingDashboard.value = true;
  dashboardError.value = "";
  try {
    const [plotPage, memberPage] = await Promise.all([
      getFarmPlots(farm.id),
      getFarmMembers(farm.id),
    ]);
    const plotData = await Promise.all(
      plotPage.items.map(async (plot) => {
        const [productionPage, operationPage] = await Promise.all([
          getPlotProductions(plot.id, "ACTIVE", 1, 5),
          getPlotOperations(plot.id, 1, 5),
        ]);
        return { plot, productionPage, operationPage };
      }),
    );
    if (currentFarm.value?.id !== farm.id) return;
    plots.value = plotPage.items;
    members.value = memberPage.items;
    activeProductionCount.value = plotData.reduce((total, item) => total + item.productionPage.total, 0);
    activeProductions.value = plotData
      .flatMap(({ plot, productionPage }) => productionPage.items.map((item) => ({ ...item, plotName: plot.name })))
      .sort((left, right) => right.startedOn.localeCompare(left.startedOn))
      .slice(0, 5);
    recentOperations.value = plotData
      .flatMap(({ plot, operationPage }) => operationPage.items.map((operation) => ({ operation, plot })))
      .sort((left, right) => new Date(right.operation.operatedAt).getTime() - new Date(left.operation.operatedAt).getTime())
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

function choosePlot(callback: (plot: Plot) => void): void {
  const farm = currentFarm.value;
  if (!farm) return;
  uni.navigateTo({
    url: `/pages/plots/select?farmId=${farm.id}`,
    events: { selected: callback },
  });
}

function openCreateProduction(): void {
  choosePlot((plot) => uni.navigateTo({ url: `/pages/productions/create?plotId=${plot.id}` }));
}

function openCreateOperation(): void {
  const farm = currentFarm.value;
  if (farm) uni.navigateTo({ url: `/pages/operations/form?farmId=${farm.id}` });
}

function openFarm(): void {
  uni.switchTab({ url: "/pages/farm/index" });
}

function openProduction(productionId: number): void {
  uni.navigateTo({ url: `/pages/productions/detail?productionId=${productionId}` });
}

function openPlotOperations(plotId: number): void {
  uni.navigateTo({ url: `/pages/operations/index?plotId=${plotId}` });
}

function showHarvestComingSoon(): void {
  toastRef.value?.show({ type: "default", message: "收获将在 Phase 6 开放" });
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

.welcome-panel { padding: 28rpx 4rpx 20rpx; }
.eyebrow, .welcome-title, .welcome-description, .overview-value, .overview-label, .production-card__name, .production-card__plot, .production-card__meta, .empty-card__title, .empty-card__description, .operation-title, .operation-meta { display: block; }
.eyebrow { color: $pf-color-primary; font-size: 24rpx; font-weight: 600; }
.welcome-title { margin-top: 10rpx; color: $pf-color-text; font-size: 38rpx; font-weight: 700; }
.welcome-description { margin-top: 10rpx; color: $pf-color-text-secondary; font-size: 24rpx; line-height: 1.5; }
.overview-card { display: flex; align-items: center; padding: 20rpx 0; }
.overview-item { flex: 1; padding: 0 28rpx; }.overview-divider { width: 1rpx; height: 54rpx; background: $pf-color-divider; }
.overview-value { color: $pf-color-text; font-size: 34rpx; font-weight: 700; }.overview-label { margin-top: 5rpx; color: $pf-color-text-secondary; font-size: 22rpx; }
.production-list { display: flex; flex-direction: column; gap: 14rpx; }.production-card { display: flex; min-height: 108rpx; align-items: center; justify-content: space-between; padding: 18rpx 24rpx; }.production-card__copy { min-width: 0; }.production-card__name { overflow: hidden; color: $pf-color-text; font-size: 28rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }.production-card__plot { margin-top: 5rpx; color: $pf-color-primary; font-size: 22rpx; }.production-card__meta { margin-top: 5rpx; color: $pf-color-text-muted; font-size: 21rpx; }
.quick-actions { display: flex; }.quick-action { display: flex; min-height: 84rpx; flex: 1; align-items: center; padding: 0 16rpx; border: 1rpx solid $pf-color-border; border-radius: $pf-radius-list; background: $pf-color-surface; color: $pf-color-text; font-size: 24rpx; }.quick-action + .quick-action { margin-left: 12rpx; }.quick-action text { margin-left: 8rpx; }
.empty-card { display: flex; min-height: 100rpx; align-items: center; padding: 20rpx 24rpx; }.empty-card > view { flex: 1; margin-left: 16rpx; }.empty-card--plain { justify-content: flex-start; color: $pf-color-text-muted; }.empty-card--plain .empty-card__description { margin-left: 14rpx; }.empty-card__title { color: $pf-color-text; font-size: 26rpx; font-weight: 600; }.empty-card__description { margin-top: 5rpx; color: $pf-color-text-muted; font-size: 21rpx; line-height: 1.45; }.empty-card__action { margin-left: 16rpx; flex-shrink: 0; color: $pf-color-primary; font-size: 24rpx; }
.operation-list { overflow: hidden; }.operation-row { display: flex; min-height: 100rpx; align-items: center; padding: 0 22rpx; }.operation-row + .operation-row { border-top: 1rpx solid $pf-color-divider; }.operation-icon { display: flex; width: 52rpx; height: 52rpx; flex-shrink: 0; align-items: center; justify-content: center; border-radius: 16rpx; background: $pf-color-primary-soft; }.operation-copy { min-width: 0; flex: 1; margin: 0 14rpx; }.operation-title { overflow: hidden; color: $pf-color-text; font-size: 26rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }.operation-meta { margin-top: 6rpx; overflow: hidden; color: $pf-color-text-muted; font-size: 21rpx; text-overflow: ellipsis; white-space: nowrap; }
.state-card { display: flex; min-height: 180rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 26rpx; color: $pf-color-text-secondary; font-size: 23rpx; }.state-card text { margin-top: 14rpx; }.state-card--compact { min-height: 100rpx; }.retry-action { color: $pf-color-primary; }
.empty-state { margin-top: 32rpx; padding: 32rpx 28rpx 28rpx; text-align: center; }.empty-state__icon { display: flex; width: 68rpx; height: 68rpx; align-items: center; justify-content: center; margin: 0 auto; border-radius: 18rpx; background: $pf-color-primary-soft; }.empty-state__title, .empty-state__description { display: block; }.empty-state__title { margin-top: 22rpx; color: $pf-color-text; font-size: 30rpx; font-weight: 600; }.empty-state__description { margin-top: 8rpx; color: $pf-color-text-secondary; font-size: 24rpx; line-height: 1.5; }
</style>
