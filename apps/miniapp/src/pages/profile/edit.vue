<template>
  <view class="pf-page profile-page">
    <view class="profile-form">
      <text class="field-label">昵称</text>
      <view class="input-shell" :class="{ 'input-shell--focused': inputFocused }">
        <uv-input
          v-model="form.nickname"
          maxlength="50"
          clearable
          border="none"
          placeholder="请输入昵称"
          placeholder-style="color: #748178;"
          color="#17261F"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
        />
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
import { useUserContext } from "../../services/user-context";

const { setUser } = useUserContext();
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
    const updated = await updateCurrentUser(nickname || null);
    setUser(updated);
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
  padding: $pf-space-4 $pf-space-page-x $pf-space-page-bottom;
}

.field-label {
  display: block;
  margin-bottom: 12rpx;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
}

.input-shell {
  display: flex;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  padding: 0 $pf-space-3;
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
</style>
