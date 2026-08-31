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

        <view class="pf-section-heading activity-heading">
          <text class="pf-section-title">最近动态</text>
          <view v-if="activityGroups.length" class="activity-heading__more pf-tappable" @tap="openAllActivities">
            <text>查看全部</text>
            <PfRowChevron />
          </view>
        </view>
        <view v-if="loadingActivities" class="state-card pf-card">
          <uv-loading-icon mode="circle" color="#286B46" />
          <text>正在整理最近工作</text>
        </view>
        <view v-else-if="activitiesError" class="state-card pf-card">
          <uv-icon name="warning" size="25" color="#A9433B" />
          <text>{{ activitiesError }}</text>
          <text class="retry-action" @tap="loadActivities">重新加载</text>
        </view>
        <view v-else-if="activityGroups.length" class="activity-feed">
          <view v-for="group in activityGroups" :key="group.key" class="feed-day">
            <view class="feed-day__head">
              <view class="feed-day__dot" />
              <text class="feed-day__label">{{ group.label }}</text>
            </view>
            <view class="feed-card">
              <view
                v-for="item in group.items"
                :key="activityKey(item)"
                class="feed-item pf-tappable"
                @tap="openActivity(item)"
              >
                <text class="feed-time">{{ formatActivityTime(item.occurredAt) }}</text>
                <view class="feed-body">
                  <text class="feed-title">{{ activityTitle(item) }}</text>
                  <text class="feed-meta">{{ plotContextLabel(item.plotName) }}</text>
                </view>
                <view class="feed-chevron"><PfRowChevron /></view>
              </view>
            </view>
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
import { useFarmContext } from "../../services/farm-context";
import { getFarmActivities, type FarmActivity } from "../../services/home";
import { ApiRequestError } from "../../services/http";
import { useUserContext } from "../../services/user-context";
import { formatNumber } from "../../utils/number";
import type { QuantityUnit } from "../../services/harvest";
import type { Industry } from "../../services/species";

interface ActivityDayGroup {
  key: string;
  label: string;
  items: FarmActivity[];
}

const { currentUser } = useUserContext();
const { currentFarm, currentFarmName, hasCurrentFarm } = useFarmContext();
const hasFarm = hasCurrentFarm;
const activities = ref<FarmActivity[]>([]);
const loadingActivities = ref(false);
const activitiesError = ref("");
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);
const displayName = computed(() => currentUser.value?.nickname || maskPhone(currentUser.value?.phoneNumber || "用户"));
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
const activityGroups = computed<ActivityDayGroup[]>(() => {
  const groups = new Map<string, ActivityDayGroup>();
  activities.value.forEach((activity) => {
    const date = new Date(activity.occurredAt);
    if (Number.isNaN(date.getTime())) return;
    const key = `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
    const existing = groups.get(key);
    if (existing) {
      existing.items.push(activity);
      return;
    }
    groups.set(key, { key, label: activityDayLabel(date), items: [activity] });
  });
  return [...groups.values()];
});

function maskPhone(phone: string): string {
  return phone.length === 11 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone;
}

function formatActivityTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未知时间";
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function activityDayLabel(date: Date): string {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (date.toDateString() === today.toDateString()) return "今天";
  if (date.toDateString() === yesterday.toDateString()) return "昨天";
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadActivities(): Promise<void> {
  const farm = currentFarm.value;
  if (!farm) {
    activities.value = [];
    return;
  }
  loadingActivities.value = true;
  activitiesError.value = "";
  try {
    const response = await getFarmActivities(farm.id, 5);
    if (currentFarm.value?.id !== farm.id) return;
    activities.value = response.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    activitiesError.value = error instanceof ApiRequestError ? error.message : "首页数据加载失败，请稍后重试";
  } finally {
    loadingActivities.value = false;
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

function openAllActivities(): void {
  uni.navigateTo({ url: "/pages/records/index" });
}

function harvestActionLabel(industry?: Industry | null): string {
  if (industry === "LIVESTOCK") return "出栏";
  if (industry === "FISHERY") return "捕捞";
  return "采收";
}

function quantityUnitLabel(unit: QuantityUnit): string {
  const labels: Record<QuantityUnit, string> = { KG: "公斤", HEAD: "头", FEATHER: "羽", PIECE: "只/个", PLANT: "株", TAIL: "尾" };
  return labels[unit];
}

function productionActionLabel(industry: Industry | null, isEnding: boolean): string {
  const action = industry === "LIVESTOCK" || industry === "FISHERY" ? "养殖" : "种植";
  return `${isEnding ? "结束" : "开始"}${action}`;
}

function activityTitle(activity: FarmActivity): string {
  const species = activity.speciesName || "";
  if (activity.type === "PRODUCTION_STARTED" || activity.type === "PRODUCTION_ENDED") {
    const action = productionActionLabel(activity.industry, activity.type === "PRODUCTION_ENDED");
    return species ? `${action} · ${species}` : action;
  }
  if (activity.type === "OPERATION_CREATED") {
    const action = activity.operationTypeName || "记录农事";
    return species ? `${action} · ${species}` : action;
  }
  // HARVEST_CREATED：动作 · 作物 数量单位，数量紧跟作物展示。
  const action = harvestActionLabel(activity.industry);
  const quantity =
    activity.quantity === null || activity.unit === null
      ? ""
      : ` ${formatNumber(activity.quantity)} ${quantityUnitLabel(activity.unit)}`;
  return species ? `${action} · ${species}${quantity}` : `${action}${quantity}`;
}

function plotContextLabel(plotName: string): string {
  const name = plotName.trim();
  return `地块：${name || "未命名"}`;
}

function activityKey(activity: FarmActivity): string {
  return `${activity.type}-${activity.productionId || activity.operationId || activity.harvestId}`;
}

function openActivity(activity: FarmActivity): void {
  if (activity.type === "OPERATION_CREATED" && activity.operationId) {
    uni.navigateTo({ url: `/pages/operations/detail?operationId=${activity.operationId}` });
    return;
  }
  if (activity.type === "HARVEST_CREATED" && activity.harvestId) {
    uni.navigateTo({ url: `/pages/harvests/detail?harvestId=${activity.harvestId}` });
    return;
  }
  if (activity.productionId) {
    uni.navigateTo({ url: `/pages/productions/detail?productionId=${activity.productionId}` });
  }
}

// 用户信息与农场上下文由共享上下文维护（登录/改名/农场变更时本地更新），
// 首页展示时只需刷新真正会变化的最近动态。
onShow(() => {
  loadActivities();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.welcome-panel { padding: 30rpx 4rpx 26rpx; }
.welcome-eyebrow, .welcome-title, .action-title, .feed-day__label, .feed-time, .feed-title, .feed-meta, .empty-activity__title, .empty-state__title { display: block; }
.welcome-eyebrow { color: $pf-color-primary; font-size: 22rpx; font-weight: 600; }
.welcome-title { margin-top: 10rpx; color: $pf-color-text; font-size: 43rpx; font-weight: 720; letter-spacing: -1rpx; }
.action-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16rpx; }
.action-card { display: flex; min-height: 112rpx; box-sizing: border-box; align-items: center; padding: 20rpx 22rpx; border-radius: 20rpx; background: $pf-color-surface; box-shadow: $pf-shadow-card; }
.action-title { min-width: 0; margin-left: 16rpx; overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.activity-heading__more { display: flex; align-items: center; color: $pf-color-primary; font-size: 23rpx; font-weight: 550; }
.activity-heading__more .pf-row-chevron { width: 26rpx; height: 26rpx; margin-left: 2rpx; opacity: 0.7; }
.activity-feed { display: flex; flex-direction: column; }
.feed-day + .feed-day { margin-top: 30rpx; }
.feed-day__head { display: flex; align-items: center; padding: 0 6rpx; margin-bottom: 14rpx; }
.feed-day__dot { width: 10rpx; height: 10rpx; margin-right: 10rpx; border-radius: 999rpx; background: $pf-color-primary; }
.feed-day__label { color: $pf-color-text; font-size: 24rpx; font-weight: 650; }
.feed-card { overflow: hidden; border-radius: $pf-radius-card; background: $pf-color-surface; box-shadow: $pf-shadow-card; }
.feed-item { display: flex; align-items: center; padding: 24rpx 24rpx 24rpx 26rpx; transition: background $pf-duration-fast ease; }
.feed-item:active { background: $pf-color-surface-muted; }
.feed-item + .feed-item { border-top: 1rpx solid $pf-color-divider; }
.feed-time { flex-shrink: 0; width: 82rpx; color: $pf-color-text-muted; font-size: 23rpx; font-weight: 500; }
.feed-body { min-width: 0; flex: 1; margin-left: 6rpx; }
.feed-title { overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.feed-meta { margin-top: 6rpx; overflow: hidden; color: $pf-color-text-secondary; font-size: 21rpx; line-height: 1.4; text-overflow: ellipsis; white-space: nowrap; }
.feed-chevron { margin-left: 12rpx; opacity: 0.35; }
.state-card { display: flex; min-height: 144rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 24rpx; border: none; color: $pf-color-text-secondary; font-size: 23rpx; }
.state-card text { margin-top: 12rpx; }
.retry-action { color: $pf-color-primary; font-weight: 600; }
.empty-activity { display: flex; min-height: 112rpx; align-items: center; padding: 0 24rpx; border-radius: 20rpx; background: $pf-color-surface; box-shadow: $pf-shadow-card; }
.empty-activity__title { margin-left: 16rpx; color: $pf-color-text; font-size: 25rpx; font-weight: 600; }
.empty-state { display: flex; flex-direction: column; align-items: center; margin-top: 32rpx; padding: 40rpx 28rpx 30rpx; border: none; text-align: center; }
.empty-state__title { margin-top: 24rpx; color: $pf-color-text; font-size: 31rpx; font-weight: 650; }
</style>
