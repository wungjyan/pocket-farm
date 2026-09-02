<template>
  <view class="pf-page about-page">
    <view class="about-content">
      <view class="about-brand">
        <view class="about-brand__mark">
          <uv-icon name="home-fill" size="30" color="#FFFFFF" />
        </view>
        <text class="about-brand__name">掌农记</text>
        <text class="about-brand__version">版本 1.0.0</text>
      </view>

      <view class="about-list">
        <view class="about-row pf-tappable" @tap="openAgreement('user')">
          <text class="about-row__label">用户协议</text>
          <PfRowChevron />
        </view>
        <view class="about-divider" />
        <view class="about-row pf-tappable" @tap="openAgreement('privacy')">
          <text class="about-row__label">隐私政策</text>
          <PfRowChevron />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import PfRowChevron from "../../components/PfRowChevron.vue";

function openAgreement(type: "user" | "privacy"): void {
  uni.navigateTo({
    url: type === "user" ? "/pages/legal/user-agreement" : "/pages/legal/privacy-policy",
  });
}
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.about-page {
  min-height: 100vh;
}

.about-content {
  padding: $pf-space-8 $pf-space-page-x $pf-space-page-bottom;
}

.about-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.about-brand__mark {
  display: flex;
  width: 96rpx;
  height: 96rpx;
  align-items: center;
  justify-content: center;
  border-radius: $pf-radius-list;
  background: $pf-color-primary;
}

.about-brand__name {
  margin-top: $pf-space-3;
  color: $pf-color-text;
  font-size: 34rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.about-brand__version {
  margin-top: $pf-space-1;
  color: $pf-color-text-muted;
  font-size: 23rpx;
}

.about-list {
  overflow: hidden;
  margin-top: 96rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.about-row {
  display: flex;
  min-height: 104rpx;
  align-items: center;
  padding: 0 $pf-space-3;
}

.about-row__label {
  flex: 1;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 550;
}

.about-divider {
  height: 1rpx;
  margin-left: $pf-space-3;
  background: $pf-color-divider;
}
</style>
