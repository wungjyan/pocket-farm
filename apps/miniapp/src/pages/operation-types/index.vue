<template>
  <view class="pf-page operation-types-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#2F7D4A" />
        <text>正在加载农事类型</text>
      </view>
      <view v-else-if="loadError" class="state-card pf-card">
        <uv-icon name="warning" size="28" color="#C96A45" />
        <text>{{ loadError }}</text>
        <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadTypes">重试</uv-button>
      </view>
      <view v-else-if="operationTypes.length" class="type-grid">
        <view v-for="item in operationTypes" :key="item.id" class="type-card pf-card" @click="chooseType(item)">
          <uv-icon :name="operationIcon(item.code)" size="22" color="#2F7D4A" />
          <text>{{ item.name }}</text>
        </view>
      </view>
      <view v-else class="state-card pf-card">
        <uv-icon name="calendar" size="30" color="#929A93" />
        <text>暂无可用农事类型</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getOperationTypes, type OperationType } from "../../services/operation";

interface OpenerEventChannel { emit: (eventName: string, data: OperationType) => void }

const operationTypes = ref<OperationType[]>([]);
const loading = ref(false);
const loadError = ref("");
let openerEventChannel: OpenerEventChannel | null = null;

function operationIcon(code: string): string {
  return ({ FERTILIZE: "bag", PESTICIDE: "warning", IRRIGATE: "clock", DISINFECT: "shield", CHANGE_WATER: "reload" } as Record<string, string>)[code] || "calendar";
}

async function loadTypes(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    operationTypes.value = (await getOperationTypes()).items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      clearAuthToken();
      uni.reLaunch({ url: "/pages/auth/login" });
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "农事类型加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function chooseType(operationType: OperationType): void {
  openerEventChannel?.emit("selected", operationType);
  uni.navigateBack();
}

onLoad(() => {
  const page = getCurrentInstance()?.proxy as unknown as { getOpenerEventChannel?: () => OpenerEventChannel } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
  loadTypes();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.type-grid { display: flex; flex-wrap: wrap; gap: 16rpx; }
.type-card { display: flex; width: calc(33.333% - 11rpx); min-height: 142rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; color: $pf-color-text; font-size: 25rpx; font-weight: 600; }
.type-card text { margin-top: 12rpx; }
.state-card { display: flex; min-height: 220rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; color: $pf-color-text-secondary; font-size: 24rpx; }
.state-card text { margin-top: 16rpx; }
</style>
