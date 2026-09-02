<template>
  <view class="pf-page farm-settings-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#2F7D4A" />
      <text>正在加载农场设置</text>
    </view>

    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadSettings"
      >
        重试
      </uv-button>
    </view>

    <template v-else-if="farm">
      <view class="settings-summary">
        <view class="settings-summary__topline">
          <text class="settings-summary__name">{{ farm.name }}</text>
          <text class="role-badge">{{ roleLabel(farm.myRole) }}</text>
        </view>
        <text class="settings-summary__code">农场编号 {{ farm.farmCode }}</text>
      </view>

      <view v-if="canEdit" class="section-label">基本设置</view>
      <view v-if="canEdit" class="menu-card pf-card">
        <view class="menu-row" @tap="openEdit">
          <view class="menu-icon">
            <uv-icon name="edit-pen" size="20" color="#2F7D4A" />
          </view>
          <view class="menu-copy">
            <text class="menu-title">基本信息</text>
            <text class="menu-description">农场名称、所在地区</text>
          </view>
          <PfRowChevron />
        </view>
      </view>

      <view v-if="canManageMembers" class="section-label">成员与权限</view>
      <view v-if="canManageMembers" class="menu-card pf-card">
        <view class="menu-row" @tap="openMembers">
          <view class="menu-icon">
            <uv-icon name="account" size="20" color="#2F7D4A" />
          </view>
          <view class="menu-copy">
            <text class="menu-title">成员管理</text>
            <text class="menu-description">添加成员并设置农场角色</text>
          </view>
          <PfRowChevron />
        </view>
      </view>

      <view class="danger-section">
        <view class="section-label">危险操作</view>
        <view class="danger-card pf-card">
          <view
            class="danger-row"
            @click="handleLeave"
          >
            <view class="danger-icon">
              <uv-icon name="close-circle" size="20" color="#C96A45" />
            </view>
            <view class="danger-copy">
              <text class="danger-title">退出农场</text>
            </view>
            <PfRowChevron />
          </view>
        </view>
      </view>
    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { clearAuthToken } from "../../services/auth";
import { getFarm, getFarmMembers, leaveFarm, type Farm, type FarmRole } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import { toFarmSummary, useFarmContext } from "../../services/farm-context";

const farmId = ref(0);
const farm = ref<Farm | null>(null);
const ownerCount = ref(0);
const loading = ref(true);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const { currentFarm, clearFarm, initializeFarmSession } = useFarmContext();

const canEdit = computed(() => farm.value?.myRole === "OWNER");
const canManageMembers = computed(
  () => farm.value?.myRole === "OWNER" || farm.value?.myRole === "ADMIN",
);
const canLeave = computed(() => farm.value?.myRole !== "OWNER" || ownerCount.value > 1);

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

function roleLabel(role?: FarmRole | null): string {
  if (role === "OWNER") return "农场主";
  if (role === "ADMIN") return "管理员";
  return "成员";
}

async function loadSettings(): Promise<void> {
  if (!farmId.value) {
    loadError.value = "农场信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const [farmResult, memberPage] = await Promise.all([
      getFarm(farmId.value),
      getFarmMembers(farmId.value),
    ]);
    farm.value = farmResult;
    ownerCount.value = memberPage.items.filter((member) => member.role === "OWNER").length;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "农场设置加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openEdit(): void {
  uni.navigateTo({ url: "/pages/farms/edit" });
}

function openMembers(): void {
  uni.navigateTo({ url: `/pages/farms/members?farmId=${farmId.value}` });
}

function handleLeave(): void {
  if (!canLeave.value) {
    uni.showModal({
      title: "暂时无法退出",
      content: "请先在成员管理中设置其他农场主。",
      confirmText: "去成员管理",
      cancelText: "取消",
      confirmColor: "#2F7D4A",
      success: (result) => {
        if (result.confirm) openMembers();
      },
    });
    return;
  }
  uni.showModal({
    title: "退出农场",
    content: "退出后将无法继续查看这个农场，确定要退出吗？",
    confirmColor: "#C96A45",
    success: async (result) => {
      if (!result.confirm) return;
      try {
        await leaveFarm(farmId.value);
        if (currentFarm.value?.id === farmId.value) {
          clearFarm();
          await initializeFarmSession();
        }
        uni.showToast({ title: "已退出农场", icon: "none" });
        setTimeout(() => uni.navigateBack(), 500);
      } catch (error) {
        if (error instanceof ApiRequestError && error.statusCode === 401) {
          handleUnauthorized();
        } else {
          toastRef.value?.error(error instanceof ApiRequestError ? error.message : "退出失败，请稍后再试");
        }
      }
    },
  });
}

onLoad((options) => {
  farmId.value = Number(options?.farmId || 0);
});

onShow(() => {
  if (farmId.value) loadSettings();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.farm-settings-page {
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.settings-summary {
  padding: 12rpx 4rpx 4rpx;
}

.settings-summary__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.settings-summary__name {
  min-width: 0;
  overflow: hidden;
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-badge {
  flex-shrink: 0;
  margin-left: 16rpx;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: 22rpx;
}

.settings-summary__code {
  display: block;
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 23rpx;
  letter-spacing: 1rpx;
}

.section-label {
  margin: 38rpx 8rpx 14rpx;
  color: $pf-color-text-muted;
  font-size: 23rpx;
  font-weight: 600;
}

.danger-card {
  overflow: hidden;
}

.menu-row,
.danger-row {
  display: flex;
  align-items: center;
}

.menu-card {
  overflow: hidden;
}

.menu-row {
  min-height: 96rpx;
  padding: 0 22rpx;
}

.menu-icon,
.danger-icon {
  display: flex;
  width: 52rpx;
  height: 52rpx;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: $pf-color-primary-soft;
}

.menu-copy,
.danger-copy {
  min-width: 0;
  flex: 1;
  margin: 0 18rpx;
}

.menu-title,
.menu-description,
.danger-title {
  display: block;
}

.menu-title,
.danger-title {
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 500;
}

.menu-description {
  margin-top: 6rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.danger-section {
  margin-top: 6rpx;
}

.danger-card {
  border-color: #f1d9d0;
}

.danger-row {
  min-height: 96rpx;
  padding: 0 22rpx;
}

.danger-icon {
  background: #fff1ec;
}

.danger-title {
  color: #c96a45;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
