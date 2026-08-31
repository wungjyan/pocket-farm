<template>
  <view class="pf-page farms-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card">
        <!-- uv-loading-icon 的 color 只接受字符串，取值对应 $pf-color-primary -->
        <uv-loading-icon mode="circle" color="#286B46" />
        <text>正在加载农场</text>
      </view>

      <view v-else-if="loadError" class="state-card pf-card">
        <!-- 取值对应 $pf-color-danger -->
        <uv-icon name="warning" size="28" color="#A9433B" />
        <text>{{ loadError }}</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 22rpx; border-radius: 12rpx;"
          @click="loadFarms"
        >
          重试
        </uv-button>
      </view>

      <view v-else-if="farms.length" class="farm-list">
        <view
          v-for="farm in farms"
          :key="farm.id"
          class="farm-row pf-card pf-tappable"
          :class="{ 'farm-row--selected': currentFarm?.id === farm.id }"
          @tap="selectCurrentFarm(farm)"
        >
          <view class="farm-row__copy">
            <text class="farm-row__name">{{ farm.name }}</text>
            <text class="farm-row__meta">{{ roleLabel(farm.myRole) }}</text>
          </view>
          <view class="farm-row__selection" :class="{ 'farm-row__selection--selected': currentFarm?.id === farm.id }">
            <uv-icon v-if="currentFarm?.id === farm.id" name="checkmark" size="13" color="#FFFFFF" />
          </view>
        </view>
      </view>

      <PfEmptyState v-else icon="land-plot" text="还没有可用农场" />

      <view
        v-if="!loading && !loadError"
        class="create-action pf-tappable"
        @click="openCreateFarm"
      >
        <uv-icon name="plus" size="14" color="#286B46" />
        <text>创建农场</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import PfEmptyState from "../../components/PfEmptyState.vue";
import { clearAuthToken } from "../../services/auth";
import { getMyFarms, type Farm } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import { toFarmSummary, useFarmContext } from "../../services/farm-context";

const farms = ref<Farm[]>([]);
const loading = ref(false);
const loadError = ref("");
const { currentFarm, selectFarm, syncAvailableFarms } = useFarmContext();

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadFarms(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    const page = await getMyFarms();
    farms.value = page.items;
    syncAvailableFarms(page.items.map(toFarmSummary));
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "农场加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function selectCurrentFarm(farm: Farm): void {
  selectFarm(toFarmSummary(farm));
  uni.navigateBack();
}

function openCreateFarm(): void {
  uni.navigateTo({ url: "/pages/farms/create" });
}

function roleLabel(role?: Farm["myRole"]): string {
  if (role === "OWNER") return "农场主";
  if (role === "ADMIN") return "管理员";
  return "成员";
}

onShow(loadFarms);
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.farm-row {
  display: flex;
  min-height: 132rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 24rpx;
  transition: background $pf-duration-fast ease;
}

.farm-row + .farm-row {
  margin-top: 12rpx;
}

.farm-row--selected {
  border-color: $pf-color-primary;
  background: $pf-color-surface-accent;
}

.farm-row__copy {
  min-width: 0;
  flex: 1;
  margin-right: 18rpx;
}

.farm-row__name {
  display: block;
  overflow: hidden;
  max-width: 100%;
  color: $pf-color-text;
  font-size: 31rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.farm-row__meta {
  display: block;
  margin-top: 8rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.farm-row__selection {
  display: flex;
  width: 40rpx;
  height: 40rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 2rpx solid $pf-color-border;
  border-radius: 50%;
  background: $pf-color-surface;
}

.farm-row__selection--selected {
  border-color: $pf-color-primary;
  background: $pf-color-primary;
}

.create-action {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  margin-top: 24rpx;
  border: 2rpx dashed $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  color: $pf-color-primary;
  font-size: 27rpx;
  font-weight: 650;
}

.create-action text {
  margin-left: 10rpx;
}

.state-card {
  display: flex;
  min-height: 180rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 28rpx;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
