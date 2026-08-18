<template>
  <view class="pf-page profile-page">
    <view class="page-intro">
      <text class="page-description">修改应用内展示的昵称，后续记录会使用这个名称。</text>
    </view>

    <view class="form-card pf-card">
      <text class="field-label">昵称</text>
      <view class="input-shell" :class="{ 'input-shell--focused': inputFocused }">
        <uv-input
          v-model="form.nickname"
          maxlength="50"
          clearable
          border="none"
          placeholder="请输入昵称"
          placeholder-style="color: #929A93;"
          color="#202821"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
        />
      </view>
      <text class="field-help">昵称会显示在首页和生产记录中</text>

      <uv-button
        type="primary"
        size="large"
        shape="square"
        :loading="saving"
        loading-text="保存中"
        custom-style="height: 88rpx; margin-top: 36rpx; border-radius: 16rpx;"
        @click="handleSave"
      >
        保存修改
      </uv-button>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, updateCurrentUser } from "../../services/user";

const form = reactive({ nickname: "" });
const saving = ref(false);
const inputFocused = ref(false);
const toastRef = ref<{ error: (message: string) => void; success: (message: string) => void } | null>(null);

function handleUnauthorized(): void {
  clearAuthToken();
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function loadUser(): Promise<void> {
  try {
    const user = await getCurrentUser();
    form.nickname = user.nickname || "";
  } catch (error) {
    if (error instanceof ApiRequestError && error.statusCode === 401) {
      handleUnauthorized();
    }
  }
}

async function handleSave(): Promise<void> {
  const nickname = form.nickname.trim();
  if (nickname.length > 50) {
    toastRef.value?.error("昵称不能超过 50 个字符");
    return;
  }

  saving.value = true;
  try {
    await updateCurrentUser(nickname || null);
    toastRef.value?.success("保存成功");
    setTimeout(() => uni.navigateBack(), 500);
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

onShow(loadUser);
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.profile-page {
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

.form-card {
  padding: 28rpx 24rpx;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: $pf-color-text;
  font-size: 27rpx;
  font-weight: 600;
}

.input-shell {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 20rpx;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
}

.input-shell--focused {
  border-color: $pf-color-primary;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}

.field-help {
  display: block;
  margin-top: 14rpx;
  color: $pf-color-text-muted;
  font-size: 22rpx;
  line-height: 1.45;
}
</style>
