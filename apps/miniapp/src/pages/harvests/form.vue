<template>
  <view class="pf-page harvest-form-page">
    <view v-if="loading" class="state-card pf-card">
      <uv-loading-icon mode="circle" color="#D79532" />
      <text>正在加载收获表单</text>
    </view>
    <view v-else-if="loadError" class="state-card pf-card">
      <uv-icon name="warning" size="28" color="#C96A45" />
      <text>{{ loadError }}</text>
      <uv-button type="primary" size="small" shape="square" custom-style="margin-top: 22rpx; border-radius: 12rpx;" @click="loadForm">重试</uv-button>
    </view>
    <template v-else>
      <view class="page-intro">
        <text class="page-title">{{ harvestId ? `编辑${actionLabel}` : production ? `记录${actionLabel}` : "记录收获" }}</text>
        <text class="page-description">收获必须关联某一次具体种养，保存后不会自动结束种养</text>
      </view>
      <view
        class="production-field pf-card"
        :class="{ 'production-field--selectable': !harvestId, 'production-field--empty': !production }"
        @click="openProductionSelector"
      >
        <view class="production-field__copy">
          <text class="production-field__label">种养 <text v-if="!harvestId" class="field-required">*</text></text>
          <text class="production-field__name">{{ productionName }}</text>
          <text v-if="production && plot" class="production-field__meta">{{ plot.name }} · {{ production.startedOn }} 开始</text>
        </view>
        <text v-if="harvestId" class="production-field__locked">编辑时不可变更</text>
        <uv-icon v-else name="arrow-right" size="17" color="#929A93" />
      </view>
      <HarvestForm
        :production="production"
        :members="members"
        :current-user-id="currentUserId"
        :initial-harvest="harvest"
        :submitting="submitting"
        :submit-label="harvestId ? '保存修改' : `保存${actionLabel}`"
        :loading-text="harvestId ? '保存中' : '记录中'"
        @submit="handleSubmit"
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
  getProductionHarvests,
  updateHarvest,
  type HarvestInput,
  type HarvestProductionSelection,
  type HarvestRecord,
} from "../../services/harvest";
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
const productionName = computed(() => {
  if (!production.value) return "请选择具体种养";
  return `${production.value.speciesName}${production.value.variety ? ` · ${production.value.variety}` : ""}`;
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
  const showFullPageLoading = !members.value.length;
  if (showFullPageLoading) loading.value = true;
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
    const [memberPage, user, harvestPage] = await Promise.all([
      getFarmMembers(plotResult.farmId),
      getCurrentUser(),
      harvestId.value ? getProductionHarvests(productionResult.id) : Promise.resolve(null),
    ]);
    if (harvestId.value) {
      harvest.value = harvestPage?.items.find((item) => item.id === harvestId.value) || null;
      if (!harvest.value) {
        loadError.value = "收获记录不存在或无法编辑";
        return;
      }
      if (productionResult.status !== "ACTIVE") {
        loadError.value = "种养已结束，收获记录无法编辑";
        return;
      }
    }
    production.value = productionResult;
    plot.value = plotResult;
    plotId.value = plotResult.id;
    farmId.value = plotResult.farmId;
    members.value = memberPage.items;
    currentUserId.value = user.id;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "收获表单加载失败，请稍后再试";
  } finally {
    if (showFullPageLoading) loading.value = false;
  }
}

function openProductionSelector(): void {
  if (harvestId.value || !farmId.value) return;
  const plotParameter = selectionPlotId.value ? `&plotId=${selectionPlotId.value}` : "";
  uni.navigateTo({
    url: `/pages/harvests/productions?farmId=${farmId.value}${plotParameter}`,
    events: {
      selected: (selection: HarvestProductionSelection) => {
        if (selection.production.id === productionId.value) return;
        productionId.value = selection.production.id;
        production.value = selection.production;
        plotId.value = selection.plot.id;
        plot.value = selection.plot;
        farmId.value = selection.plot.farmId;
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

.harvest-form-page { padding: 28rpx $pf-space-page-x $pf-space-page-bottom; }
.page-intro { padding: 12rpx 4rpx 28rpx; }
.page-title, .page-description, .production-field__label, .production-field__name, .production-field__meta { display: block; }
.page-title { color: $pf-color-text; font-size: 38rpx; font-weight: 700; }
.page-description { margin-top: 10rpx; color: $pf-color-text-secondary; font-size: 24rpx; line-height: 1.5; }
.production-field { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20rpx; padding: 20rpx 24rpx; }
.production-field--selectable { border-color: $pf-color-harvest; }
.production-field--empty .production-field__name { color: $pf-color-text-muted; font-weight: 400; }
.production-field__copy { min-width: 0; flex: 1; }
.production-field__label, .production-field__locked { color: $pf-color-text-muted; font-size: 21rpx; }
.field-required { margin-left: 4rpx; color: #c96a45; }
.production-field__name { margin-top: 5rpx; overflow: hidden; color: $pf-color-text; font-size: 27rpx; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.production-field__meta { margin-top: 5rpx; color: $pf-color-harvest; font-size: 21rpx; }
.state-card { display: flex; min-height: 220rpx; box-sizing: border-box; flex-direction: column; align-items: center; justify-content: center; padding: 28rpx; color: $pf-color-text-secondary; font-size: 24rpx; text-align: center; }
.state-card text { margin-top: 16rpx; }
</style>
