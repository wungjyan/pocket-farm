<template>
  <view class="pf-page production-form-page">
    <PfPageHeader title="编辑种养" :show-back="true" :back-handler="handleBack" />

    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#2F7D4A" />
      <text>正在加载种养信息</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button
        type="primary"
        size="small"
        shape="square"
        custom-style="margin-top: 22rpx; border-radius: 12rpx;"
        @click="loadProduction"
      >
        重试
      </uv-button>
    </view>
    <ProductionForm
      v-else-if="production"
      :initial-production="production"
      :submitting="saving"
      @change="dirty = true"
      @submit="saveProduction"
    />

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import PfPageHeader from "../../components/PfPageHeader.vue";
import ProductionForm from "../../components/ProductionForm.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import {
  getProduction,
  updateProduction,
  type Production,
  type ProductionInput,
} from "../../services/production";

const productionId = ref(0);
const production = ref<Production | null>(null);
const loading = ref(true);
const saving = ref(false);
const dirty = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void; success: (message: string) => void } | null>(null);

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
    production.value = await getProduction(productionId.value);
    dirty.value = false;
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

async function saveProduction(input: ProductionInput): Promise<void> {
  if (!productionId.value) return;
  saving.value = true;
  try {
    production.value = await updateProduction(productionId.value, input);
    dirty.value = false;
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

function handleBack(): void {
  if (!dirty.value) {
    uni.navigateBack();
    return;
  }
  uni.showModal({
    title: "放弃修改？",
    content: "当前内容尚未保存，确定要离开吗？",
    confirmColor: "#C96A45",
    success: (result) => {
      if (result.confirm) uni.navigateBack();
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

.production-form-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding-bottom: $pf-space-page-bottom;
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
