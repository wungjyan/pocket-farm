<template>
  <view class="pf-page harvest-form-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#006C49" />
      <text>正在加载收获表单</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#A9433B" />
      <text>{{ loadError }}</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 16rpx;" @click="loadForm">重试</uv-button>
    </view>
    <template v-else>
      <HarvestForm
        :production="production"
        :production-selectable="!harvestId"
        :members="members"
        :current-user-id="currentUserId"
        :initial-harvest="harvest"
        :submitting="submitting"
        :submit-label="harvestId ? '保存修改' : `保存${actionLabel}`"
        :loading-text="harvestId ? '保存中' : '记录中'"
        @submit="handleSubmit"
        @select-production="openProductionSelector"
      />
    </template>
    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import HarvestForm from "../../components/HarvestForm.vue";
import { clearAuthToken } from "../../services/auth";
import { getFarmMembers, type FarmMember } from "../../services/farm";
import {
  createHarvest,
  getHarvest,
  updateHarvest,
  type HarvestInput,
  type HarvestProductionSelection,
  type HarvestRecord,
} from "../../services/harvest";
import { notifyFarmActivitiesChanged } from "../../services/home";
import { ApiRequestError } from "../../services/http";
import { getPlot, type Plot } from "../../services/plot";
import { getProduction, type Production } from "../../services/production";
import { getCurrentUser } from "../../services/user";

const productionId = ref(0);
const harvestId = ref(0);
const farmId = ref(0);
const plotId = ref(0);
const selectionPlotId = ref(0);
const production = ref<Production | null>(null);
const plot = ref<Plot | null>(null);
const harvest = ref<HarvestRecord | null>(null);
const members = ref<FarmMember[]>([]);
const currentUserId = ref(0);
const loading = ref(true);
const submitting = ref(false);
const loadError = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const actionLabel = computed(() => {
  if (production.value?.industry === "LIVESTOCK") return "出栏";
  if (production.value?.industry === "FISHERY") return "捕捞";
  return production.value ? "采收" : "收获";
});

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadContext(targetFarmId: number): Promise<void> {
  const [memberPage, user] = await Promise.all([
    getFarmMembers(targetFarmId),
    getCurrentUser(),
  ]);
  members.value = memberPage.items;
  currentUserId.value = user.id;
}

async function loadForm(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    if (!productionId.value) {
      if (plotId.value) {
        plot.value = await getPlot(plotId.value);
        farmId.value = plot.value.farmId;
      }
      if (!farmId.value) {
        loadError.value = "农场信息无效";
        return;
      }
      await loadContext(farmId.value);
      return;
    }
    const productionResult = await getProduction(productionId.value);
    const plotResult = await getPlot(productionResult.plotId);
    const [existingHarvest] = await Promise.all([
      harvestId.value ? getHarvest(harvestId.value) : Promise.resolve(null),
      !members.value.length || farmId.value !== plotResult.farmId
        ? loadContext(plotResult.farmId)
        : Promise.resolve(),
    ]);
    if (harvestId.value) {
      if (!existingHarvest || existingHarvest.productionId !== productionResult.id) {
        loadError.value = "收获记录不存在或无法编辑";
        return;
      }
      harvest.value = existingHarvest;
      if (productionResult.status !== "ACTIVE") {
        loadError.value = "种养已结束，收获记录无法编辑";
        return;
      }
    }
    production.value = productionResult;
    plot.value = plotResult;
    plotId.value = plotResult.id;
    farmId.value = plotResult.farmId;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "收获表单加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function openProductionSelector(): void {
  if (harvestId.value || !farmId.value) return;
  const plotParameter = selectionPlotId.value ? `&plotId=${selectionPlotId.value}` : "";
  const selectedParameter = productionId.value ? `&selectedProductionId=${productionId.value}` : "";
  uni.navigateTo({
    url: `/pages/harvests/productions?farmId=${farmId.value}${plotParameter}${selectedParameter}`,
    events: {
      selected: (selection: HarvestProductionSelection) => {
        if (selection.productionId === productionId.value) return;
        productionId.value = selection.productionId;
        production.value = null;
        plot.value = null;
        void loadForm();
      },
    },
  });
}

async function handleSubmit(input: HarvestInput): Promise<void> {
  if (!production.value || submitting.value) return;
  submitting.value = true;
  try {
    if (harvestId.value) {
      await updateHarvest(harvestId.value, input);
    } else {
      await createHarvest(production.value.id, input);
      notifyFarmActivitiesChanged(farmId.value);
    }
    uni.showToast({ title: harvestId.value ? "已保存" : `${actionLabel.value}记录成功`, icon: "none" });
    setTimeout(() => uni.navigateBack(), 400);
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    } else {
      toastRef.value?.error(error instanceof ApiRequestError ? error.message : "保存失败，请稍后再试");
    }
  } finally {
    submitting.value = false;
  }
}

onLoad((options) => {
  productionId.value = Number(options?.productionId || 0);
  harvestId.value = Number(options?.harvestId || 0);
  farmId.value = Number(options?.farmId || 0);
  plotId.value = Number(options?.plotId || 0);
  selectionPlotId.value = plotId.value;
  loadForm();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.harvest-form-page { min-height: 100vh; box-sizing: border-box; padding-bottom: $pf-space-page-bottom; }
.state-card { display: flex; min-height: 220rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; margin: $pf-space-4 $pf-space-page-x 0; padding: $pf-space-4; border: 1rpx solid $pf-color-border; border-radius: $pf-radius-card; background: $pf-color-surface; color: $pf-color-text-secondary; font-size: $pf-font-size-body; text-align: center; }
.state-card text { margin-top: $pf-space-2; }
</style>
