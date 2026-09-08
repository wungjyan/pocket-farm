<template>
  <view class="pf-page production-end-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#006C49" />
      <text>正在加载种养信息</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 24rpx; border-radius: 16rpx;"
        @click="loadProduction"
      >重试</uv-button>
    </view>
    <view v-else-if="production && plot" class="pf-page-content">
      <view class="production-summary">
        <view class="production-summary__icon">
          <image src="/static/icons/lucide/sprout.svg" mode="aspectFit" />
        </view>
        <view class="production-summary__copy">
          <text class="production-summary__name">{{ productionName }}</text>
          <text class="production-summary__meta">{{ plot.name }} · {{ production.startedOn }} 开始</text>
        </view>
        <text class="production-summary__status">进行中</text>
      </view>

      <view class="end-form">
        <view class="field-group">
          <text class="field-label">结束日期</text>
          <picker
            mode="date"
            :value="endedOn"
            :start="production.startedOn"
            :end="today"
            @change="handleDateChange"
          >
            <view class="select-shell" hover-class="select-shell--pressed">
              <text>{{ endedOn }}</text>
              <uv-icon name="calendar" size="17" color="#748178" />
            </view>
          </picker>
        </view>

        <uv-button
          type="primary"
          size="large"
          shape="square"
          :loading="submitting"
          loading-text="结束中"
          custom-style="height: 96rpx; margin-top: 40rpx; border-radius: 16rpx;"
          @click="confirmEnd"
        >确认{{ endActionName }}</uv-button>
      </view>
    </view>
    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot } from "../../services/plot";
import { endProduction, getProduction, type Production } from "../../services/production";

const productionId = ref(0);
const production = ref<Production | null>(null);
const plot = ref<Plot | null>(null);
const loading = ref(true);
const submitting = ref(false);
const loadError = ref("");
const today = formatToday();
const endedOn = ref(today);
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const productionName = computed(() => {
  const value = production.value;
  if (!value) return "";
  return `${value.speciesName}${value.variety ? ` · ${value.variety}` : ""}`;
});
const endActionName = computed(() => {
  if (production.value?.industry === "AGRICULTURE" || production.value?.industry === "FORESTRY") {
    return "结束种植";
  }
  return "结束养殖";
});

function formatToday(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadProduction(): Promise<void> {
  if (!productionId.value) {
    loadError.value = "种养信息无效";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    const productionResult = await getProduction(productionId.value);
    if (productionResult.status !== "ACTIVE") {
      loadError.value = "该种养已结束";
      return;
    }
    production.value = productionResult;
    plot.value = await getPlot(productionResult.plotId);
    if (endedOn.value < productionResult.startedOn) endedOn.value = productionResult.startedOn;
    uni.setNavigationBarTitle({ title: endActionName.value });
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "种养信息加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function handleDateChange(event: { detail: { value: string } }): void {
  endedOn.value = event.detail.value;
}

function confirmEnd(): void {
  if (!production.value || submitting.value) return;
  uni.showModal({
    title: `确认${endActionName.value}？`,
    content: endedOn.value,
    confirmColor: "#006C49",
    success: async (result) => {
      if (!result.confirm || !production.value) return;
      submitting.value = true;
      try {
        await endProduction(production.value.id, { endedOn: endedOn.value });
        uni.showToast({ title: "已结束", icon: "none" });
        setTimeout(() => uni.navigateBack(), 400);
      } catch (error) {
        if (error instanceof ApiRequestError && error.statusCode === 401) {
          handleUnauthorized();
        } else {
          toastRef.value?.error(error instanceof ApiRequestError ? error.message : "结束失败，请稍后再试");
        }
      } finally {
        submitting.value = false;
      }
    },
  });
}

onLoad((options) => {
  productionId.value = Number(options?.productionId || 0);
  loadProduction();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.production-end-page {
  padding-bottom: $pf-space-page-bottom;
}

.production-end-page .pf-page-content {
  padding-top: $pf-space-4;
}

.production-summary {
  display: flex;
  min-height: 120rpx;
  box-sizing: border-box;
  align-items: center;
  padding: $pf-space-3;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.production-summary__icon {
  display: flex;
  width: 64rpx;
  height: 64rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: $pf-radius-control;
  background: $pf-color-primary-soft;
}

.production-summary__icon image {
  width: 36rpx;
  height: 36rpx;
}

.production-summary__copy {
  min-width: 0;
  flex: 1;
  margin-left: $pf-space-2;
}

.production-summary__name,
.production-summary__meta,
.field-label {
  display: block;
}

.production-summary__name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-summary__meta {
  overflow: hidden;
  margin-top: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.production-summary__status {
  flex-shrink: 0;
  margin-left: $pf-space-2;
  padding: 6rpx 16rpx;
  border-radius: $pf-radius-pill;
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-size: $pf-font-size-label;
  font-weight: $pf-font-weight-medium;
}

.end-form {
  margin-top: $pf-space-5;
}

.field-label {
  margin-bottom: $pf-space-2;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.select-shell {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  padding: 0 $pf-space-3;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  color: $pf-color-text;
  font-size: $pf-font-size-body;
}

.select-shell--pressed {
  background: $pf-color-surface-muted;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: $pf-space-4 $pf-space-page-x 0;
  padding: $pf-space-4;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
  text-align: center;
}

.state-card text {
  margin-top: $pf-space-2;
}
</style>
