<template>
  <view class="page farm-page">
    <view class="custom-header" :style="headerStyle">
      <view class="custom-header__inner" :style="headerInnerStyle">
        <view class="header-context" @tap="showComingSoon">
          <uv-icon name="map" size="18" color="#2F7D4A" />
          <text>选择农场</text>
          <uv-icon name="arrow-down" size="14" color="#667068" />
        </view>
        <text class="header-title">农场</text>
      </view>
    </view>

    <view class="page-content">
      <view class="intro-block">
        <text class="eyebrow">生产现场</text>
        <text class="page-title">把地块和工作放在一起</text>
        <text class="page-description">从一个农场开始，逐步记录每次种养、农事和收获。</text>
      </view>

      <view class="overview-card">
        <view class="overview-card__topline">
          <view class="overview-card__icon">
            <uv-icon name="map-fill" size="28" color="#2F7D4A" />
          </view>
          <view class="overview-card__status">尚未创建</view>
        </view>
        <text class="overview-card__title">还没有农场</text>
        <text class="overview-card__description">创建农场后，可以在这里管理地块和查看生产现场。</text>
        <view class="overview-card__action" @tap="showComingSoon">
          <text>创建第一个农场</text>
          <uv-icon name="arrow-right" size="17" color="#2F7D4A" />
        </view>
      </view>

      <view class="section-heading">
        <text class="section-title">开始使用</text>
        <text class="section-note">三步建立记录</text>
      </view>

      <view class="steps-card">
        <view class="step-item">
          <view class="step-index">1</view>
          <view class="step-copy">
            <text class="step-title">创建农场</text>
            <text class="step-description">先给你的生产空间取个名字</text>
          </view>
          <uv-icon name="plus-circle" size="22" color="#A6C9B0" />
        </view>
        <view class="step-line" />
        <view class="step-item">
          <view class="step-index">2</view>
          <view class="step-copy">
            <text class="step-title">添加地块</text>
            <text class="step-description">记录田地、大棚、鱼塘或栏舍</text>
          </view>
          <uv-icon name="grid" size="22" color="#A6C9B0" />
        </view>
        <view class="step-line" />
        <view class="step-item">
          <view class="step-index">3</view>
          <view class="step-copy">
            <text class="step-title">开始记录</text>
            <text class="step-description">留下每一次真实的生产过程</text>
          </view>
          <uv-icon name="edit-pen" size="22" color="#A6C9B0" />
        </view>
      </view>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useCustomHeader } from "../../composables/useCustomHeader";

const { headerStyle, headerInnerStyle } = useCustomHeader();
const toastRef = ref<{ show: (options: { type?: string; message: string }) => void } | null>(null);

function showComingSoon(): void {
  toastRef.value?.show({ type: "default", message: "相关功能将在后续阶段开放" });
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  box-sizing: border-box;
  background: #f7f8f3;
}

.custom-header {
  background: #f7f8f3;
}

.custom-header__inner {
  position: relative;
  display: flex;
  box-sizing: border-box;
  align-items: center;
  padding-left: 32rpx;
}

.header-title {
  position: absolute;
  top: 50%;
  left: 50%;
  color: #202821;
  font-size: 32rpx;
  font-weight: 600;
  line-height: 1;
  transform: translate(-50%, -50%);
}

.header-context {
  display: flex;
  align-items: center;
  color: #2f7d4a;
  font-size: 25rpx;
  white-space: nowrap;
}

.header-context > .uv-icon:first-child {
  margin-right: 8rpx;
}

.header-context text + .uv-icon {
  margin-left: 8rpx;
}

.page-content {
  padding: 24rpx 32rpx 64rpx;
}

.intro-block {
  padding: 12rpx 4rpx 32rpx;
}

.eyebrow {
  display: block;
  color: #2f7d4a;
  font-size: 24rpx;
  font-weight: 600;
}

.page-title {
  display: block;
  margin-top: 12rpx;
  color: #202821;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.25;
}

.page-description {
  display: block;
  margin-top: 14rpx;
  color: #667068;
  font-size: 25rpx;
  line-height: 1.55;
}

.overview-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 26rpx rgba(32, 40, 33, 0.04);
}

.overview-card__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.overview-card__icon {
  display: flex;
  width: 64rpx;
  height: 64rpx;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  background: #eaf4ec;
}

.overview-card__status {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #f3f5f1;
  color: #929a93;
  font-size: 22rpx;
}

.overview-card__title,
.overview-card__description {
  display: block;
}

.overview-card__title {
  margin-top: 28rpx;
  color: #202821;
  font-size: 32rpx;
  font-weight: 600;
}

.overview-card__description {
  max-width: 580rpx;
  margin-top: 10rpx;
  color: #667068;
  font-size: 24rpx;
  line-height: 1.55;
}

.overview-card__action {
  display: flex;
  align-items: center;
  margin-top: 26rpx;
  color: #2f7d4a;
  font-size: 26rpx;
  font-weight: 600;
}

.overview-card__action .uv-icon {
  margin-left: 8rpx;
}

.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 44rpx 4rpx 16rpx;
}

.section-title {
  color: #202821;
  font-size: 30rpx;
  font-weight: 600;
}

.section-note {
  color: #929a93;
  font-size: 23rpx;
}

.steps-card {
  padding: 4rpx 24rpx;
  border: 1rpx solid #e2e6e0;
  border-radius: 22rpx;
  background: #ffffff;
}

.step-item {
  display: flex;
  min-height: 106rpx;
  align-items: center;
}

.step-index {
  display: flex;
  width: 44rpx;
  height: 44rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #eaf4ec;
  color: #2f7d4a;
  font-size: 23rpx;
  font-weight: 700;
}

.step-copy {
  min-width: 0;
  flex: 1;
  margin: 0 20rpx;
}

.step-title,
.step-description {
  display: block;
}

.step-title {
  color: #202821;
  font-size: 27rpx;
  font-weight: 600;
}

.step-description {
  margin-top: 6rpx;
  color: #929a93;
  font-size: 22rpx;
  line-height: 1.4;
}

.step-line {
  height: 1rpx;
  margin-left: 64rpx;
  background: #ecefeb;
}
</style>
