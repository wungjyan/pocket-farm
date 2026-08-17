<template>
  <view class="page profile-page">
    <view class="page-heading">
      <text class="eyebrow">账号信息</text>
      <text class="page-title">个人资料</text>
      <text class="page-description">修改应用内展示的昵称，让记录更容易被辨认。</text>
    </view>

    <view class="identity-preview">
      <uv-avatar :text="avatarText" size="64" bg-color="#2F7D4A" color="#FFFFFF" />
      <view class="identity-copy">
        <text class="identity-label">当前昵称</text>
        <text class="identity-value">{{ form.nickname.trim() || "未设置昵称" }}</text>
      </view>
    </view>

    <view class="form-section">
      <text class="field-label">昵称</text>
      <view class="input-shell">
        <uv-input
          v-model="form.nickname"
          maxlength="50"
          clearable
          border="none"
          placeholder="请输入昵称"
          placeholder-style="color: #929A93;"
          color="#202821"
        />
      </view>
      <text class="field-help">昵称会显示在首页和后续的生产记录中</text>
    </view>

    <uv-button
      type="primary"
      size="large"
      shape="square"
      :loading="saving"
      loading-text="保存中"
      custom-style="height: 96rpx; margin-top: 40rpx; border-radius: 16rpx;"
      @click="handleSave"
    >
      保存修改
    </uv-button>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { clearAuthToken } from "../../services/auth";
import { ApiRequestError } from "../../services/http";
import { getCurrentUser, updateCurrentUser } from "../../services/user";

const form = reactive({ nickname: "" });
const saving = ref(false);
const toastRef = ref<{ error: (message: string) => void; success: (message: string) => void } | null>(null);
const avatarText = computed(() => form.nickname.trim().slice(0, 1) || "我");

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
.page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 28rpx 32rpx 64rpx;
  background: #f7f8f3;
}

.page-heading {
  padding: 12rpx 4rpx 30rpx;
}

.eyebrow {
  display: block;
  color: #2f7d4a;
  font-size: 24rpx;
  font-weight: 600;
}

.page-title {
  display: block;
  margin-top: 10rpx;
  color: #202821;
  font-size: 40rpx;
  font-weight: 700;
}

.page-description {
  display: block;
  margin-top: 12rpx;
  color: #667068;
  font-size: 25rpx;
  line-height: 1.55;
}

.identity-preview {
  display: flex;
  align-items: center;
  padding: 24rpx;
  border-radius: 22rpx;
  background: #eaf4ec;
}

.identity-copy {
  margin-left: 18rpx;
}

.identity-label,
.identity-value {
  display: block;
}

.identity-label {
  color: #2f7d4a;
  font-size: 23rpx;
  font-weight: 600;
}

.identity-value {
  margin-top: 8rpx;
  color: #202821;
  font-size: 28rpx;
  font-weight: 600;
}

.form-section {
  margin-top: 32rpx;
  padding: 28rpx 24rpx 24rpx;
  border: 1rpx solid #e2e6e0;
  border-radius: 22rpx;
  background: #ffffff;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: #202821;
  font-size: 27rpx;
  font-weight: 600;
}

.input-shell {
  display: flex;
  min-height: 88rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 20rpx;
  border: 1rpx solid #e2e6e0;
  border-radius: 14rpx;
  background: #f7f8f3;
}

.input-shell :deep(.uv-input) {
  width: 100%;
}

.field-help {
  display: block;
  margin-top: 14rpx;
  color: #929a93;
  font-size: 22rpx;
  line-height: 1.45;
}
</style>
