<template>
  <view class="pf-page create-farm-page">
    <view class="page-intro">
      <text class="page-description">创建后，你会自动成为这个农场的农场主。</text>
    </view>

    <FarmForm submit-label="创建农场" loading-text="创建中" :submitting="submitting" @submit="handleCreate" />

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import FarmForm from "../../components/FarmForm.vue";
import { clearAuthToken } from "../../services/auth";
import { createFarm } from "../../services/farm";
import { ApiRequestError } from "../../services/http";
import { toFarmSummary, useFarmContext } from "../../services/farm-context";

const submitting = ref(false);
const toastRef = ref<{
  error: (message: string) => void;
  success: (message: string) => void;
} | null>(null);
const { currentFarm, selectFarmAndPersist } = useFarmContext();

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function handleCreate(input: { name: string; region: string | null }): Promise<void> {
  if (!input.name) {
    toastRef.value?.error("请输入农场名称");
    return;
  }

  submitting.value = true;
  let created = false;
  try {
    const farm = await createFarm(input);
    created = true;
    if (!currentFarm.value) {
      await selectFarmAndPersist(toFarmSummary(farm));
    }
    toastRef.value?.success("农场创建成功");
    setTimeout(() => uni.redirectTo({ url: "/pages/farms/index" }), 400);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(
        created
          ? "农场已创建，请在农场列表选择当前农场"
          : error instanceof ApiRequestError
            ? error.message
            : "创建失败，请稍后再试",
      );
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.create-farm-page {
  padding: 28rpx $pf-space-page-x $pf-space-page-bottom;
}

.page-intro {
  padding: 12rpx 4rpx 28rpx;
}

.page-description {
  display: block;
  color: $pf-color-text-secondary;
  font-size: 25rpx;
  line-height: 1.55;
}
</style>
