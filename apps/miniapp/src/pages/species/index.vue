<template>
  <view class="pf-page species-page">
    <view class="pf-page-content">
      <view class="search-shell">
        <uv-icon name="search" size="18" color="#929A93" />
        <uv-input
          v-model="keyword"
          border="none"
          clearable
          placeholder="搜索种类"
          placeholder-style="color: #929A93;"
          color="#202821"
          @confirm="loadSpecies"
        />
        <text class="search-action" @click="loadSpecies">搜索</text>
      </view>

      <view class="industry-tabs">
        <view
          v-for="item in industries"
          :key="item.value || 'all'"
          class="industry-tab"
          :class="{ 'industry-tab--active': selectedIndustry === item.value }"
          @click="selectIndustry(item.value)"
        >
          <text>{{ item.label }}</text>
        </view>
      </view>

      <view v-if="loading" class="state-card pf-card">
        <uv-loading-icon mode="circle" color="#2F7D4A" />
        <text>正在加载种类</text>
      </view>
      <view v-else-if="loadError" class="state-card pf-card">
        <uv-icon name="warning" size="28" color="#C96A45" />
        <text>{{ loadError }}</text>
        <uv-button
          type="primary"
          size="small"
          shape="square"
          custom-style="margin-top: 22rpx; border-radius: 12rpx;"
          @click="loadSpecies"
        >
          重试
        </uv-button>
      </view>
      <template v-else>
        <view v-if="species.length" class="list-toolbar">
          <text class="list-toolbar__count">共 {{ species.length }} 个种类</text>
        </view>
        <view v-if="species.length" class="species-list">
          <view
            v-for="item in species"
            :key="item.id"
            class="species-card pf-card pf-tappable"
            :class="{ 'species-card--selected': item.id === selectedSpeciesId }"
            @tap="chooseSpecies(item)"
          >
            <view class="species-copy">
              <text class="species-name">{{ item.name }}</text>
            </view>
            <view
              class="species-selection"
              :class="{ 'species-selection--selected': item.id === selectedSpeciesId }"
            >
              <uv-icon v-if="item.id === selectedSpeciesId" name="checkmark" size="15" color="#286B46" />
            </view>
          </view>
        </view>
        <view v-else class="state-card pf-card">
          <uv-icon name="empty-search" size="30" color="#929A93" />
          <text>没有找到相关种类</text>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getSpecies, type Industry, type Species } from "../../services/species";

interface OpenerEventChannel {
  emit: (eventName: string, data: Species) => void;
}

const industries: Array<{ label: string; value: Industry | null }> = [
  { label: "全部", value: null },
  { label: "农业", value: "AGRICULTURE" },
  { label: "林业", value: "FORESTRY" },
  { label: "牧业", value: "LIVESTOCK" },
  { label: "渔业", value: "FISHERY" },
];
const keyword = ref("");
const selectedIndustry = ref<Industry | null>(null);
const species = ref<Species[]>([]);
const loading = ref(false);
const loadError = ref("");
const selectedSpeciesId = ref(0);
let openerEventChannel: OpenerEventChannel | null = null;

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadSpecies(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    const page = await getSpecies({ industry: selectedIndustry.value, keyword: keyword.value });
    species.value = page.items;
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
      return;
    }
    loadError.value = error instanceof ApiRequestError ? error.message : "种类加载失败，请稍后再试";
  } finally {
    loading.value = false;
  }
}

function selectIndustry(industry: Industry | null): void {
  selectedIndustry.value = industry;
  loadSpecies();
}

function chooseSpecies(item: Species): void {
  openerEventChannel?.emit("selected", item);
  uni.navigateBack();
}

onLoad((options) => {
  const currentSelection = Number(options?.selectedId || 0);
  selectedSpeciesId.value = Number.isInteger(currentSelection) && currentSelection > 0 ? currentSelection : 0;
  const page = getCurrentInstance()?.proxy as unknown as {
    getOpenerEventChannel?: () => OpenerEventChannel;
  } | null;
  openerEventChannel = page?.getOpenerEventChannel?.() || null;
  loadSpecies();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.search-shell {
  display: flex;
  min-height: 80rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 20rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.search-shell :deep(.uv-input) {
  flex: 1;
  margin-left: 12rpx;
}

.search-action {
  margin-left: 12rpx;
  color: $pf-color-primary;
  font-size: 24rpx;
}

.industry-tabs {
  display: flex;
  margin: 24rpx 0;
  gap: 12rpx;
}

.industry-tab {
  flex: 1;
  padding: 14rpx 0;
  border-radius: 999rpx;
  background: $pf-color-surface-muted;
  color: $pf-color-text-secondary;
  font-size: 22rpx;
  text-align: center;
}

.industry-tab--active {
  background: $pf-color-primary-soft;
  color: $pf-color-primary;
  font-weight: 600;
}

.list-toolbar {
  display: flex;
  min-height: 48rpx;
  align-items: center;
  justify-content: flex-end;
  padding: 0 4rpx 12rpx;
}

.list-toolbar__count {
  color: $pf-color-text-muted;
  font-size: 22rpx;
}

.species-list {
  display: flex;
  flex-direction: column;
  gap: $pf-space-2;
}

.species-card {
  display: flex;
  min-height: 112rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 22rpx;
}

.species-card--selected {
  background: $pf-color-primary-soft;
}

.species-copy {
  min-width: 0;
  flex: 1;
}

.species-name {
  overflow: hidden;
  color: $pf-color-text;
  font-size: 28rpx;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.species-selection {
  display: flex;
  width: 36rpx;
  height: 36rpx;
  box-sizing: border-box;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-left: 16rpx;
  border: 2rpx solid $pf-color-border;
  border-radius: 50%;
  background: $pf-color-surface;
}

.species-selection--selected {
  border-color: $pf-color-primary;
}

.state-card {
  display: flex;
  min-height: 220rpx;
  box-sizing: border-box;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28rpx;
  color: $pf-color-text-secondary;
  font-size: 24rpx;
}

.state-card text {
  margin-top: 16rpx;
}
</style>
