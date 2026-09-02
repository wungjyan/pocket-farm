<template>
  <view class="pf-page edit-farm-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#2F7D4A" />
      <text>正在加载农场信息</text>
    </view>

    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadFarm"
      >
        重试
      </uv-button>
    </view>

    <template v-else-if="farm">
      <FarmForm
        :initial-name="farm.name"
        :initial-region="farm.region"
        :framed="false"
        submit-label="保存修改"
        loading-text="保存中"
        :submitting="saving"
        @change="dirty = true"
        @submit="saveFarm"
      />
    </template>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import FarmForm from "../../components/FarmForm.vue";
import { useUnsavedChangesGuard } from "../../composables/useUnsavedChangesGuard";
import { clearAuthToken } from "../../services/auth";
import { getFarm, updateFarm, type Farm } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import { toFarmSummary, useFarmContext } from "../../services/farm-context";

const farm = ref<Farm | null>(null);
const loading = ref(true);
const saving = ref(false);
const dirty = ref(false);
const loadError = ref("");
const toastRef = ref<{
  error: (message: string) => void;
  success: (message: string) => void;
} | null>(null);
const { currentFarm, selectFarm } = useFarmContext();
useUnsavedChangesGuard(dirty);

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadFarm(): Promise<void> {
  const farmId = currentFarm.value?.id;
  if (!farmId) {
    loadError.value = "请先选择当前农场";
    loading.value = false;
    return;
  }
  loading.value = true;
  loadError.value = "";
  try {
    farm.value = await getFarm(farmId);
    dirty.value = false;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "农场信息加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

async function saveFarm(input: { name: string; region: string | null }): Promise<void> {
  if (!input.name) {
    toastRef.value?.error("请输入农场名称");
    return;
  }
  const farmId = currentFarm.value?.id;
  if (!farmId) {
    toastRef.value?.error("请先选择当前农场");
    return;
  }
  saving.value = true;
  try {
    const result = await updateFarm(farmId, input);
    farm.value = result;
    dirty.value = false;
    if (currentFarm.value?.id === result.id) {
      selectFarm(toFarmSummary(result));
    }
    toastRef.value?.success("保存成功");
    setTimeout(() => uni.navigateBack(), 400);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "保存失败，请稍后再试");
    }
  } finally {
    saving.value = false;
  }
}

onShow(() => {
  if (!saving.value) loadFarm();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.edit-farm-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 40rpx $pf-space-page-x $pf-space-page-bottom;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 28rpx $pf-space-page-x 0;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
