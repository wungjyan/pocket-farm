<template>
  <view class="pf-page home-page">
    <PfPageHeader
      :title="hasFarm ? currentFarmName : '未选择农场'"
      variant="tab"
    />

    <view class="pf-page-content">
      <view class="welcome-panel">
        <view class="welcome-date">
          <uv-icon name="calendar" size="14" color="#006C49" />
          <text>{{ dateLabel }}</text>
        </view>
        <text class="welcome-title">{{ greeting }}，{{ displayName }}</text>
      </view>

      <template v-if="hasFarm">
        <view class="hero-action pf-tappable" @tap="openCreateProduction">
          <view class="hero-action__copy">
            <text class="hero-action__title">开始种养</text>
            <text class="hero-action__description">开始新的种养</text>
          </view>
          <view class="hero-action__icon">
            <PfBusinessIcon name="sprout" size="empty" variant="plain" />
          </view>
        </view>

        <view class="quick-actions">
          <view class="quick-action pf-tappable" @tap="openCreateOperation">
            <PfBusinessIcon name="shovel" />
            <view class="quick-action__copy">
              <text class="quick-action__title">记农事</text>
              <text class="quick-action__description">记录作业过程</text>
            </view>
          </view>
          <view class="quick-action pf-tappable" @tap="openCreateHarvest">
            <PfBusinessIcon name="shopping-basket" />
            <view class="quick-action__copy">
              <text class="quick-action__title">记收获</text>
              <text class="quick-action__description">产量录入</text>
            </view>
          </view>
          <view class="quick-action pf-tappable" @tap="openPlotList">
            <PfBusinessIcon name="land-plot" />
            <view class="quick-action__copy">
              <text class="quick-action__title">地块管理</text>
              <text class="quick-action__description">规划分区</text>
            </view>
          </view>
        </view>

        <view class="pf-section-heading activity-heading">
          <view class="activity-heading__left">
            <text class="pf-section-title">最近动态</text>
            <text class="activity-heading__hint">
              仅展示 {{ ACTIVITY_LIMIT }} 条
            </text>
          </view>
          <view
            v-if="activityGroups.length"
            class="activity-heading__more pf-tappable"
            @tap="openAllActivities"
          >
            <text>查看全部</text>
            <PfRowChevron />
          </view>
        </view>
        <view v-if="loadingActivities" class="state-card">
          <uv-loading-icon mode="circle" color="#006C49" />
          <text>正在整理最近工作</text>
        </view>
        <view v-else-if="activitiesError" class="state-card">
          <uv-icon name="warning" size="25" color="#A9433B" />
          <text>{{ activitiesError }}</text>
          <text class="retry-action" @tap="loadActivities">重新加载</text>
        </view>
        <view v-else-if="activityGroups.length" class="activity-feed">
          <view
            v-for="group in activityGroups"
            :key="group.key"
            class="feed-day"
          >
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
                <view
                  class="feed-item__icon"
                  :class="{
                    'feed-item__icon--operation':
                      item.type === 'OPERATION_CREATED',
                  }"
                >
                  <PfBusinessIcon :name="activityIcon(item)" />
                </view>
                <view class="feed-body">
                  <view class="feed-title-line">
                    <text class="feed-time">{{ formatActivityTime(item.occurredAt) }}</text>
                    <text class="feed-title">{{ activityTitle(item) }}</text>
                  </view>
                  <text class="feed-meta">{{ plotContextLabel(item.plotName) }}</text>
                </view>
                <view class="feed-chevron"><PfRowChevron /></view>
              </view>
            </view>
          </view>
        </view>
        <PfEmptyState
          v-else
          variant="inline"
          icon="clock-3"
          title="还没有生产动态"
        />
      </template>

      <view v-else class="empty-state">
        <PfBusinessIcon name="map" size="empty" />
        <text class="empty-state__title">先创建一个农场</text>
        <uv-button
          type="primary"
          shape="square"
          custom-style="width: 100%; height: 96rpx; margin-top: 32rpx; border-radius: 16rpx;"
          @click="openCreateFarm"
          >创建农场</uv-button
        >
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow, onUnload } from "@dcloudio/uni-app";
import PfBusinessIcon from "../../components/PfBusinessIcon.vue";
import PfEmptyState from "../../components/PfEmptyState.vue";
import PfPageHeader from "../../components/PfPageHeader.vue";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import {
  FARM_ACTIVITIES_CHANGED_EVENT,
  getFarmActivities,
  type FarmActivity,
} from "../../services/home";
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

// 首页最近动态最多展示的条数，与标题旁提示文案联动。
const ACTIVITY_LIMIT = 10;

const { currentUser } = useUserContext();
const { currentFarm, currentFarmName, hasCurrentFarm } = useFarmContext();
const hasFarm = hasCurrentFarm;
const activities = ref<FarmActivity[]>([]);
const loadingActivities = ref(false);
const activitiesError = ref("");
let activityRequestId = 0;
const toastRef = ref<{
  show: (options: { type?: string; message: string }) => void;
} | null>(null);
const displayName = computed(
  () =>
    currentUser.value?.nickname ||
    maskPhone(currentUser.value?.phoneNumber || "用户"),
);
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
  return phone.length === 11
    ? `${phone.slice(0, 3)}****${phone.slice(-4)}`
    : phone;
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
  const requestId = ++activityRequestId;
  const farm = currentFarm.value;
  if (!farm) {
    if (requestId === activityRequestId) activities.value = [];
    return;
  }
  loadingActivities.value = true;
  activitiesError.value = "";
  try {
    const response = await getFarmActivities(farm.id, ACTIVITY_LIMIT);
    if (requestId !== activityRequestId || currentFarm.value?.id !== farm.id) return;
    activities.value = response.items;
  } catch (error) {
    if (requestId !== activityRequestId) return;
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    activitiesError.value =
      error instanceof ApiRequestError
        ? error.message
        : "首页数据加载失败，请稍后重试";
  } finally {
    if (requestId === activityRequestId) loadingActivities.value = false;
  }
}

function handleFarmActivitiesChanged(farmId: number): void {
  if (currentFarm.value?.id === farmId) void loadActivities();
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

function openCreateProduction(): void {
  if (currentFarm.value) {
    uni.navigateTo({
      url: `/pages/productions/start?farmId=${currentFarm.value.id}`,
    });
  }
}

function openCreateOperation(): void {
  if (currentFarm.value)
    uni.navigateTo({
      url: `/pages/operations/form?farmId=${currentFarm.value.id}`,
    });
}

function openCreateHarvest(): void {
  if (currentFarm.value)
    uni.navigateTo({
      url: `/pages/harvests/form?farmId=${currentFarm.value.id}`,
    });
}

function openPlotList(): void {
  if (currentFarm.value)
    uni.navigateTo({
      url: `/pages/farm-plots/index?farmId=${currentFarm.value.id}&filter=ALL`,
    });
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
  const labels: Record<QuantityUnit, string> = {
    KG: "公斤",
    HEAD: "头",
    FEATHER: "羽",
    PIECE: "只/个",
    PLANT: "株",
    TAIL: "尾",
  };
  return labels[unit];
}

function productionActionLabel(
  industry: Industry | null,
  isEnding: boolean,
): string {
  const action =
    industry === "LIVESTOCK" || industry === "FISHERY" ? "养殖" : "种植";
  return `${isEnding ? "结束" : "开始"}${action}`;
}

function activityTitle(activity: FarmActivity): string {
  const species = activity.speciesName || "";
  if (
    activity.type === "PRODUCTION_STARTED" ||
    activity.type === "PRODUCTION_ENDED"
  ) {
    const action = productionActionLabel(
      activity.industry,
      activity.type === "PRODUCTION_ENDED",
    );
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

function activityIcon(
  activity: FarmActivity,
): "sprout" | "shovel" | "shopping-basket" {
  if (activity.type === "OPERATION_CREATED") return "shovel";
  if (activity.type === "HARVEST_CREATED") return "shopping-basket";
  return "sprout";
}

function activityKey(activity: FarmActivity): string {
  return `${activity.type}-${activity.productionId || activity.operationId || activity.harvestId}`;
}

function openActivity(activity: FarmActivity): void {
  if (activity.type === "OPERATION_CREATED" && activity.operationId) {
    uni.navigateTo({
      url: `/pages/operations/detail?operationId=${activity.operationId}`,
    });
    return;
  }
  if (activity.type === "HARVEST_CREATED" && activity.harvestId) {
    uni.navigateTo({
      url: `/pages/harvests/detail?harvestId=${activity.harvestId}`,
    });
    return;
  }
  if (activity.productionId) {
    uni.navigateTo({
      url: `/pages/productions/detail?productionId=${activity.productionId}`,
    });
  }
}

onLoad(() => {
  uni.$on(FARM_ACTIVITIES_CHANGED_EVENT, handleFarmActivitiesChanged);
});

onUnload(() => {
  uni.$off(FARM_ACTIVITIES_CHANGED_EVENT, handleFarmActivitiesChanged);
});

onShow(() => {
  void loadActivities();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.home-page {
  background: $pf-color-page;
}

.home-page .pf-page-content {
  padding: 24rpx 32rpx 128rpx;
}

.welcome-panel {
  padding: 12rpx 0 30rpx;
}

.welcome-date {
  display: inline-flex;
  min-height: 44rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 14rpx;
  border: 1rpx solid rgba($pf-color-primary, 0.16);
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 21rpx;
  font-weight: 650;
}

.welcome-date text {
  margin-left: 8rpx;
}

.welcome-title,
.feed-day__label,
.feed-title,
.feed-meta,
.empty-state__title {
  display: block;
}

.welcome-title {
  margin-top: 18rpx;
  color: $pf-color-text;
  font-size: 46rpx;
  font-weight: 720;
  letter-spacing: -1.2rpx;
  line-height: 1.2;
}

.hero-action {
  position: relative;
  display: flex;
  min-height: 176rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;
  padding: 28rpx 32rpx;
  border-radius: 28rpx;
  background: $pf-gradient-action;
  box-shadow: $pf-shadow-action;
}

.hero-action::after {
  position: absolute;
  top: -80rpx;
  right: -48rpx;
  width: 250rpx;
  height: 250rpx;
  border-radius: 50%;
  background: rgba($pf-mint-200, 0.12);
  content: "";
}

.hero-action__copy {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.hero-action__title {
  display: block;
  color: $pf-color-on-primary;
  font-size: 36rpx;
  font-weight: 750;
  letter-spacing: 0.5rpx;
}

.hero-action__description {
  display: block;
  margin-top: 10rpx;
  color: rgba($pf-color-on-primary, 0.75);
  font-size: 23rpx;
  font-weight: 500;
}

.hero-action__icon {
  position: relative;
  z-index: 1;
  display: flex;
  width: 96rpx;
  height: 96rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-left: 24rpx;
  border-radius: 30rpx;
  background: rgba($pf-color-on-primary, 0.14);
}

.hero-action__icon :deep(.pf-business-icon__image) {
  width: 52rpx;
  height: 52rpx;
  filter: brightness(0) invert(1);
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 16rpx;
}

.quick-action {
  display: flex;
  min-height: 184rpx;
  box-sizing: border-box;
  flex-direction: column;
  padding: 22rpx;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}

.quick-action :deep(.pf-business-icon) {
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
  background: $pf-color-primary-soft;
}

.quick-action__copy {
  min-width: 0;
  margin-top: 16rpx;
}

.quick-action__title {
  display: block;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-action__description {
  display: block;
  margin-top: 6rpx;
  overflow: hidden;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  font-weight: 500;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-heading {
  margin-top: 52rpx;
  margin-bottom: 20rpx;
}

.activity-heading :deep(.pf-section-title) {
  color: $pf-color-text;
  font-size: 32rpx;
  font-weight: 720;
}

.activity-heading__left {
  display: flex;
  min-width: 0;
  align-items: baseline;
}

.activity-heading__hint {
  overflow: hidden;
  margin-left: 12rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-heading__more {
  display: flex;
  min-height: 56rpx;
  align-items: center;
  color: $pf-color-primary;
  font-size: 24rpx;
  font-weight: 650;
}

.activity-heading__more .pf-row-chevron {
  width: 26rpx;
  height: 26rpx;
  margin-left: 2rpx;
  opacity: 0.7;
}
.activity-feed {
  display: flex;
  flex-direction: column;
}
.feed-day + .feed-day {
  margin-top: 34rpx;
}
.feed-day__head {
  display: flex;
  align-items: center;
  margin-bottom: 14rpx;
}
.feed-day__dot {
  width: 10rpx;
  height: 10rpx;
  margin-right: 10rpx;
  border: 3rpx solid $pf-mint-200;
  border-radius: 50%;
  background: $pf-color-primary;
}
.feed-day__label {
  color: $pf-color-text;
  font-size: 25rpx;
  font-weight: 700;
}
.feed-card {
  overflow: hidden;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  box-shadow: $pf-shadow-card;
}
.feed-item {
  display: flex;
  min-height: 112rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 18rpx 22rpx;
  transition: background 160ms ease;
}
.feed-item:active {
  background: $pf-color-primary-soft;
}
.feed-item + .feed-item {
  border-top: 1rpx solid $pf-color-divider;
}
.feed-item__icon {
  flex-shrink: 0;
}
.feed-item__icon :deep(.pf-business-icon) {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  background: $pf-color-primary-soft;
}
.feed-item__icon :deep(.pf-business-icon__image) {
  width: 36rpx;
  height: 36rpx;
}
.feed-item__icon--operation :deep(.pf-business-icon__image) {
  width: 30rpx;
  height: 30rpx;
}
.feed-body {
  min-width: 0;
  flex: 1;
  margin-left: 18rpx;
}
.feed-title-line {
  display: flex;
  min-width: 0;
  align-items: baseline;
}
.feed-time {
  flex-shrink: 0;
  margin-right: 12rpx;
  color: $pf-color-text-muted;
  font-size: 21rpx;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.feed-title {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 680;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.feed-meta {
  margin-top: 5rpx;
  overflow: hidden;
  color: $pf-color-text-secondary;
  font-size: 22rpx;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.feed-chevron {
  flex-shrink: 0;
  margin-left: 12rpx;
  opacity: 0.42;
}
.state-card {
  display: flex;
  min-height: 160rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24rpx;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
}
.state-card text {
  margin-top: 12rpx;
}
.retry-action {
  color: $pf-color-primary;
  font-weight: 650;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 32rpx;
  padding: 56rpx 32rpx 44rpx;
  border: 1rpx solid $pf-color-divider;
  border-radius: 24rpx;
  background: $pf-color-surface;
  text-align: center;
}
.empty-state :deep(.pf-business-icon) {
  background: $pf-color-primary-soft;
}
.empty-state__title {
  margin-top: 24rpx;
  color: $pf-color-text;
  font-size: 32rpx;
  font-weight: 700;
}
</style>
