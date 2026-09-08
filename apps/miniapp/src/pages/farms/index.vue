<template>
  <view class="pf-page farms-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#006C49" />
        <text>正在加载农场</text>
      </view>

      <view v-else-if="loadError" class="state-card pf-card">
        <uv-icon name="warning" size="28" color="#A9433B" />
        <text>{{ loadError }}</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 22rpx; border-radius: 16rpx;"
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

      <PfEmptyState v-else icon="land-plot" title="还没有可用农场" />

      <view
        v-if="!loading && !loadError"
        class="create-action pf-tappable"
        @click="openCreateFarm"
      >
        <uv-icon name="plus" size="14" color="#006C49" />
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
const selectingFarmId = ref<number | null>(null);
const { currentFarm, selectFarmAndPersist, syncAvailableFarms } = useFarmContext();

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

async function selectCurrentFarm(farm: Farm): Promise<void> {
  if (selectingFarmId.value !== null) return;
  selectingFarmId.value = farm.id;
  try {
    await selectFarmAndPersist(toFarmSummary(farm));
    uni.navigateBack();
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    uni.showToast({
      title: error instanceof ApiRequestError ? error.message : "农场切换失败，请稍后重试",
      icon: "none",
    });
  } finally {
    selectingFarmId.value = null;
  }
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

.farms-page .pf-page-content {
  padding-top: $pf-space-4;
}

.farm-row {
  display: flex;
  min-height: 128rpx;
  box-sizing: border-box;
  align-items: center;
  padding: $pf-space-3;
  transition: background $pf-duration-fast ease;
}

.farm-row + .farm-row {
  margin-top: $pf-space-2;
}

.farm-row--selected {
  border-color: $pf-color-primary;
  background: $pf-color-surface-accent;
}

.farm-row__copy {
  min-width: 0;
  flex: 1;
  margin-right: $pf-space-2;
}

.farm-row__name {
  display: block;
  overflow: hidden;
  max-width: 100%;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.farm-row__meta {
  display: block;
  margin-top: 6rpx;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.farm-row__selection {
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
  margin-top: $pf-space-2;
  border: 1rpx dashed $pf-color-outline;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  color: $pf-color-primary;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.create-action text {
  margin-left: $pf-space-1;
}

.state-card {
  display: flex;
  min-height: 180rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: $pf-space-4;
  padding: $pf-space-4;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
}

.state-card text {
  margin-top: $pf-space-2;
}
</style>
