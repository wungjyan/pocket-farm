<template>
  <view class="pf-page production-start-page">
    <view v-if="farmId" class="pf-page-content">
      <view class="start-form">
        <view class="field-group">
          <text class="field-label">种类 <text class="field-required">*</text></text>
          <view
            class="select-shell"
            hover-class="select-shell--pressed"
            @tap="openSpeciesSelector"
          >
            <text v-if="selectedSpecies" class="species-select__name">{{
              selectedSpecies.name
            }}</text>
            <text v-else class="select-placeholder">选择种类</text>
            <PfRowChevron />
          </view>
        </view>

        <view class="field-group">
          <text class="field-label">品种 <text class="field-optional">选填</text></text>
          <view class="input-shell">
            <uv-input
              v-model="variety"
              maxlength="100"
              clearable
              border="none"
              placeholder="填写品种"
              placeholder-style="color: #748178;"
              color="#17261F"
            />
          </view>
        </view>

        <uv-button
          type="primary"
          size="large"
          shape="square"
          :disabled="!selectedSpecies"
          custom-style="height: 96rpx; margin-top: 40rpx; border-radius: 16rpx;"
          @click="goNext"
        >
          下一步
        </uv-button>
      </view>
    </view>

    <view v-else class="state-card">
      <uv-icon name="info-circle" size="28" color="#748178" />
      <text>请先选择农场</text>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import PfRowChevron from "../../components/PfRowChevron.vue";
import { useFarmContext } from "../../services/farm-context";
import type { Species } from "../../services/species";

const farmId = ref(0);
const plotId = ref(0);
const selectedSpecies = ref<Species | null>(null);
const variety = ref("");
const toastRef = ref<{ error: (message: string) => void } | null>(null);
const { currentFarm } = useFarmContext();

function openSpeciesSelector(): void {
  if (!farmId.value) {
    toastRef.value?.error("农场信息无效");
    return;
  }
  const selectedParameter = selectedSpecies.value ? `&selectedId=${selectedSpecies.value.id}` : "";
  uni.navigateTo({
    url: `/pages/species/index?farmId=${farmId.value}${selectedParameter}`,
    events: {
      selected: (species: Species) => {
        if (selectedSpecies.value?.id !== species.id) variety.value = "";
        selectedSpecies.value = species;
      },
    },
  });
}

function goNext(): void {
  if (!selectedSpecies.value) {
    toastRef.value?.error("请选择种类");
    return;
  }
  const plotParameter = plotId.value ? `&plotId=${plotId.value}` : "";
  const speciesParameter = [
    `&speciesId=${selectedSpecies.value.id}`,
    `&speciesName=${encodeURIComponent(selectedSpecies.value.name)}`,
    `&industry=${selectedSpecies.value.industry}`,
    `&individualUnit=${selectedSpecies.value.individualUnit}`,
  ].join("");
  const varietyParameter = variety.value.trim() ? `&variety=${encodeURIComponent(variety.value.trim())}` : "";
  uni.navigateTo({
    url: `/pages/productions/form?farmId=${farmId.value}${plotParameter}${speciesParameter}${varietyParameter}`,
  });
}

onLoad((options) => {
  const requestedFarmId = Number(options?.farmId || 0);
  const requestedPlotId = Number(options?.plotId || 0);
  farmId.value = Number.isInteger(requestedFarmId) && requestedFarmId > 0 ? requestedFarmId : currentFarm.value?.id || 0;
  plotId.value = Number.isInteger(requestedPlotId) && requestedPlotId > 0 ? requestedPlotId : 0;
  uni.setNavigationBarTitle({ title: "开始种养" });
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.production-start-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding-bottom: $pf-space-page-bottom;
}

.production-start-page .pf-page-content {
  padding-top: $pf-space-4;
}

.start-form {
  padding-top: 0;
}

.field-group + .field-group {
  margin-top: $pf-space-4;
}

.field-label {
  display: block;
  margin-bottom: 12rpx;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.field-optional {
  margin-left: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  font-weight: $pf-font-weight-medium;
}

.field-required {
  margin-left: $pf-space-1;
  color: $pf-color-danger;
}

.select-shell,
.input-shell {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.select-shell {
  justify-content: space-between;
  padding: 0 $pf-space-2 0 $pf-space-3;
}

.select-shell--pressed {
  background: $pf-color-surface-muted;
}

.input-shell {
  padding: 0 $pf-space-3;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}

.species-select__name {
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.select-placeholder {
  color: $pf-color-text-muted;
  font-size: $pf-font-size-body;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: $pf-space-4 $pf-space-page-x 0;
  padding: 28rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-card;
  background: $pf-color-surface;
  color: $pf-color-text-secondary;
  font-size: $pf-font-size-body;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
