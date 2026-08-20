<template>
  <view class="pf-page production-end-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#286B46" />
      <text>正在加载种养信息</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadProduction"
      >重试</uv-button>
    </view>
    <template v-else-if="production && plot">
      <view class="production-summary">
        <text class="production-summary__name">{{ production.speciesName }}</text>
        <text class="production-summary__plot">{{ plot.name }}</text>
      </view>

      <view class="end-form pf-card">
        <view class="field-group">
          <text class="field-label">结束日期</text>
          <picker mode="date" :value="endedOn" :start="production.startedOn" :end="today" @change="handleDateChange">
            <view class="select-shell">
              <text>{{ endedOn }}</text>
              <uv-icon name="calendar" size="17" color="#7F8B82" />
            </view>
          </picker>
        </view>

        <uv-button
          type="primary"
          size="large"
          shape="square"
          :loading="submitting"
          loading-text="结束中"
          custom-style="height: 88rpx; margin-top: 42rpx; border-radius: 16rpx;"
          @click="confirmEnd"
        >确认{{ endActionName }}</uv-button>
      </view>
    </template>
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
    confirmColor: "#286B46",
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
  min-height: 100vh;
  box-sizing: border-box;
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.production-summary {
  padding: 12rpx 4rpx 28rpx;
}

.production-summary__name,
.production-summary__plot,
.field-label {
  display: block;
}

.production-summary__name {
  color: $pf-color-text;
  font-size: 38rpx;
  font-weight: 700;
}

.production-summary__plot {
  margin-top: 10rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.end-form {
  padding: 28rpx 24rpx;
}

.field-label {
  margin-bottom: 14rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.select-shell {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  padding: 0 20rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  color: $pf-color-text;
  font-size: 25rpx;
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
  text-align: center;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
