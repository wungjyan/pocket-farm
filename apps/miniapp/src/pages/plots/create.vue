<template>
  <view class="pf-page plot-form-page">
    <PlotForm
      :framed="false"
      require-all-fields
      default-area-unit="MU"
      submit-label="创建地块"
      loading-text="创建中"
      :submitting="submitting"
      @submit="handleCreate"
    />

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import PlotForm from "../../components/PlotForm.vue";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { createPlot, type AreaUnit, type PlotType } from "../../services/plot";

const farmId = ref(0);
const submitting = ref(false);
const toastRef = ref<{ error: (message: string) => void; success: (message: string) => void } | null>(null);

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function handleCreate(input: { name: string; type: PlotType | null; areaValue: number | null; areaUnit: AreaUnit | null }): Promise<void> {
  if (!input.name) {
    toastRef.value?.error("请输入地块名称");
    return;
  }
  if (!input.type) {
    toastRef.value?.error("请选择地块类型");
    return;
  }
  if (input.areaValue === null || input.areaValue <= 0) {
    toastRef.value?.error("请输入大于 0 的面积");
    return;
  }
  if (!input.areaUnit) {
    toastRef.value?.error("请选择面积单位");
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
  padding: 40rpx $pf-space-page-x $pf-space-page-bottom;
}
</style>
