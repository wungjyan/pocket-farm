<template>
  <view class="pf-page plot-form-page">
    <view class="page-intro">
      <text class="page-description">地块是农场里的生产区域。</text>
    </view>

    <PlotForm submit-label="创建地块" loading-text="创建中" :submitting="submitting" @submit="handleCreate" />

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import PlotForm from "../../components/PlotForm.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { createPlot } from "../../services/plot";

const farmId = ref(0);
const submitting = ref(false);
const toastRef = ref<{ error: (message: string) => void; success: (message: string) => void } | null>(null);

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function handleCreate(input: { name: string; type: "FIELD" | "PADDY" | "GREENHOUSE" | "ORCHARD" | "FOREST" | "POND" | "BARN" | "OTHER" | null; areaValue: number | null; areaUnit: "MU" | "SQUARE_METER" | "HECTARE" | null }): Promise<void> {
  if (!input.name) {
    toastRef.value?.error("请输入地块名称");
    return;
  }
  if ((input.areaValue === null) !== (input.areaUnit === null)) {
    toastRef.value?.error("请同时填写面积和单位");
    return;
  }
  if (!farmId.value) {
    toastRef.value?.error("农场信息无效");
    return;
  }
  submitting.value = true;
  try {
    await createPlot(farmId.value, {
      name: input.name,
      type: input.type,
      areaValue: input.areaValue,
      areaUnit: input.areaUnit,
    });
    toastRef.value?.success("地块创建成功");
    setTimeout(() => uni.navigateBack(), 400);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "创建失败，请稍后再试");
    }
  } finally {
    submitting.value = false;
  }
}

onLoad((options) => {
  farmId.value = Number(options?.farmId || 0);
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.plot-form-page {
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.page-intro {
  padding: 12rpx 4rpx 28rpx;
}

.page-description {
  display: block;
  color: $pf-color-text-secondary;
  font-size: 25rpx;
}
</style>
