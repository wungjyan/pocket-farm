<template>
  <view class="pf-page operation-types-page">
    <view class="pf-page-content">
      <view v-if="loading" class="state-card">
        <uv-loading-icon mode="circle" color="#006C49" />
        <text>正在加载农事类型</text>
      </view>
      <view v-else-if="loadError" class="state-card">
        <uv-icon name="warning" size="28" color="#A9433B" />
        <text>{{ loadError }}</text>
        <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 16rpx;" @click="loadTypes">重试</uv-button>
      </view>
      <template v-else-if="operationTypes.length">
        <view class="list-toolbar">
          <text class="list-toolbar__count">共 {{ operationTypes.length }} 个农事类型</text>
        </view>
        <view class="type-list">
          <view
            v-for="(item, index) in operationTypes"
            :key="item.id"
            class="type-row"
            :class="{ 'type-row--selected': item.id === selectedOperationTypeId }"
            hover-class="type-row--pressed"
            @tap="chooseType(item)"
          >
            <text class="type-row__name">{{ item.name }}</text>
            <view
              class="type-row__selection"
              :class="{ 'type-row__selection--selected': item.id === selectedOperationTypeId }"
            >
              <uv-icon v-if="item.id === selectedOperationTypeId" name="checkmark" size="15" color="#006C49" />
            </view>
            <view v-if="index < operationTypes.length - 1" class="type-row__divider" />
          </view>
        </view>
      </template>
      <view v-else class="state-card">
        <uv-icon name="calendar" size="30" color="#748178" />
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
const selectedOperationTypeId = ref(0);
let openerEventChannel: OpenerEventChannel | null = null;

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

onLoad((options) => {
  const currentSelection = Number(options?.selectedOperationTypeId);
  selectedOperationTypeId.value = Number.isInteger(currentSelection) && currentSelection > 0
    ? currentSelection
    : 0;
  const page = getCurrentInstance()?.proxy as unknown as { getOpenerEventChannel?: () => OpenerEventChannel } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
  loadTypes();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.operation-types-page .pf-page-content {
  padding-top: $pf-space-4;
}

.list-toolbar {
  display: flex;
  min-height: 48rpx;
  align-items: center;
  justify-content: flex-end;
  padding: 0 4rpx $pf-space-2;
}

.list-toolbar__count {
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
}

.type-list {
  overflow: hidden;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
}

.type-row {
  position: relative;
  display: flex;
  min-height: 104rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 $pf-space-3;
}

.type-row--selected,
.type-row--pressed {
  background: $pf-color-primary-soft;
}

.type-row__name {
  min-width: 0;
  flex: 1;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.type-row__selection {
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

.type-row__selection--selected {
  border-color: $pf-color-primary;
}

.type-row__divider {
  position: absolute;
  right: 0;
  bottom: 0;
  left: $pf-space-3;
  height: 1rpx;
  background: $pf-color-divider;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: $pf-space-4;
  padding: $pf-space-4;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
}

.state-card text {
  margin-top: $pf-space-2;
}
</style>
