<template>
  <view class="pf-page login-page">
    <view class="login-content">
      <view class="brand-block">
        <image
          class="brand-mark"
          src="/static/brand/pocket-farm-logo.png"
          mode="aspectFill"
          aria-label="掌农记"
        />
        <text class="brand-title">掌农记</text>
      </view>

      <view class="login-form">
        <view class="field-group">
          <text class="field-label">手机号</text>
          <view class="input-shell" :class="{ 'input-shell--focused': phoneFocused }">
            <view class="country-code">
              <text>+86</text>
            </view>
            <view class="input-control">
              <uv-input
                v-model="form.phoneNumber"
                type="number"
                maxlength="11"
                clearable
                border="none"
                placeholder="请输入手机号"
                placeholder-style="color: #748178;"
                color="#17261F"
                :adjust-position="true"
                :cursor-spacing="24"
                @focus="phoneFocused = true"
                @blur="phoneFocused = false"
              />
            </view>
          </view>
        </view>

        <view class="field-group code-field-group">
          <text class="field-label">验证码</text>
          <view class="input-shell" :class="{ 'input-shell--focused': codeFocused }">
            <view class="input-control">
              <uv-input
                v-model="form.verificationCode"
                type="number"
                maxlength="6"
                border="none"
                placeholder="请输入验证码"
                placeholder-style="color: #748178;"
                color="#17261F"
                :adjust-position="true"
                :cursor-spacing="24"
                @focus="codeFocused = true"
                @blur="codeFocused = false"
              />
            </view>
            <view class="code-divider" />
            <view
              class="code-action"
              :class="{ 'code-action--disabled': countdown > 0 }"
              :hover-class="countdown > 0 ? 'none' : 'code-action--pressed'"
              role="button"
              :aria-disabled="countdown > 0"
              @tap="handleGetCode"
            >
              <text>{{ countdown > 0 ? `${countdown}s 后重新获取` : "获取验证码" }}</text>
            </view>
          </view>
        </view>

        <uv-button
          type="primary"
          size="large"
          shape="square"
          :loading="submitting"
          loading-text="登录中"
          custom-style="height: 96rpx; margin-top: 40rpx; border-radius: 16rpx;"
          @click="handleLogin"
        >
          登录
        </uv-button>
      </view>
    </view>

    <view
      class="agreement pf-tappable"
      role="checkbox"
      :aria-checked="agreementAccepted"
      aria-label="同意用户协议和隐私政策"
      @tap="toggleAgreement"
    >
      <view class="agreement-check">
        <view class="agreement-check__icon" :class="{ 'agreement-check__icon--checked': agreementAccepted }">
          <uv-icon v-if="agreementAccepted" name="checkbox-mark" size="16" color="#FFFFFF" />
        </view>
      </view>
      <text>我已阅读并同意</text>
      <text class="agreement-link" @tap.stop="openAgreement('user')">《用户协议》</text>
      <text>和</text>
      <text class="agreement-link" @tap.stop="openAgreement('privacy')">《隐私政策》</text>
    </view>

    <uv-toast ref="toastRef" />
  </view>
</template>

<script setup lang="ts">
import { onUnmounted, reactive, ref, watch } from "vue";
import { useFarmContext } from "../../services/farm-context";
import { ApiRequestError } from "../../services/http";
import { login } from "../../services/user";
import { useUserContext } from "../../services/user-context";

const { setUser } = useUserContext();
const { initializeFarmSession } = useFarmContext();

const form = reactive({
  phoneNumber: "",
  verificationCode: "",
});
const submitting = ref(false);
const countdown = ref(0);
const verificationPhone = ref("");
const phoneFocused = ref(false);
const codeFocused = ref(false);
const agreementAccepted = ref(false);
const toastRef = ref<{
  show: (options: {
    message: string;
    type?: "error" | "success" | "warning" | "primary" | "default";
    overlay?: boolean;
    position?: "top" | "center" | "bottom";
  }) => void;
} | null>(null);
let countdownTimer: ReturnType<typeof setInterval> | null = null;

function showError(message: string): void {
  toastRef.value?.show({ message, type: "error", overlay: false, position: "top" });
}

function showMessage(message: string): void {
  toastRef.value?.show({ message, overlay: false, position: "top" });
}

function isValidPhoneNumber(phoneNumber: string): boolean {
  return /^1[3-9]\d{9}$/.test(phoneNumber);
}

function handleGetCode(): void {
  if (countdown.value > 0) {
    return;
  }

  const phoneNumber = form.phoneNumber.trim();
  if (!isValidPhoneNumber(phoneNumber)) {
    showError("请输入正确的手机号");
    return;
  }

  verificationPhone.value = phoneNumber;
  countdown.value = 60;
  countdownTimer = setInterval(() => {
    if (countdown.value <= 1) {
      countdown.value = 0;
      if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
      }
      return;
    }
    countdown.value -= 1;
  }, 1000);

  showMessage("演示模式，使用验证码 8888 登录");
}

function toggleAgreement(): void {
  agreementAccepted.value = !agreementAccepted.value;
}

function openAgreement(type: "user" | "privacy"): void {
  uni.navigateTo({
    url: type === "user" ? "/pages/legal/user-agreement" : "/pages/legal/privacy-policy",
  });
}

async function handleLogin(): Promise<void> {
  const phoneNumber = form.phoneNumber.trim();
  const verificationCode = form.verificationCode.trim();

  if (!isValidPhoneNumber(phoneNumber)) {
    showError("请输入正确的手机号");
    return;
  }

  if (verificationPhone.value !== phoneNumber) {
    showError("请先获取验证码");
    return;
  }

  if (!verificationCode) {
    showError("请输入验证码");
    return;
  }

  if (!agreementAccepted.value) {
    showError("请先阅读并同意用户协议和隐私政策");
    return;
  }

  submitting.value = true;
  try {
    const result = await login(phoneNumber, verificationCode);
    setUser(result.user);
    await initializeFarmSession();
    uni.reLaunch({ url: "/pages/home/index" });
  } catch (error) {
    const message = error instanceof ApiRequestError ? error.message : "登录失败，请稍后再试";
    showError(message);
  } finally {
    submitting.value = false;
  }
}

watch(
  () => form.phoneNumber,
  (phoneNumber) => {
    if (phoneNumber.trim() !== verificationPhone.value) {
      verificationPhone.value = "";
    }
  },
);

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.login-page {
  display: flex;
  flex-direction: column;
  padding: $pf-space-6 $pf-space-page-x calc($pf-space-3 + env(safe-area-inset-bottom));
}

.login-content {
  width: 100%;
  flex: 1;
}

.brand-block {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.brand-mark {
  width: 104rpx;
  height: 104rpx;
  border-radius: $pf-radius-card-compact;
}

.brand-title {
  margin-top: $pf-space-2;
  color: $pf-color-text;
  font-size: 40rpx;
  font-weight: $pf-font-weight-bold;
  letter-spacing: 2rpx;
}

.login-form {
  margin-top: 96rpx;
}

.field-group {
  width: 100%;
}

.code-field-group {
  margin-top: $pf-space-4;
}

.field-label {
  display: block;
  margin-bottom: $pf-space-2;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-semibold;
  line-height: 1.4;
  white-space: nowrap;
}

.input-shell {
  display: flex;
  width: 100%;
  min-height: 96rpx;
  box-sizing: border-box;
  align-items: center;
  border: 1rpx solid $pf-color-border;
  border-radius: $pf-radius-control;
  background: $pf-color-surface;
  transition: border-color $pf-duration-fast ease;
}

.input-shell--focused {
  border-color: $pf-color-primary;
}

.country-code {
  display: flex;
  width: 106rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  border-right: 1rpx solid $pf-color-divider;
  color: $pf-color-text;
  font-size: $pf-font-size-title;
  font-weight: $pf-font-weight-medium;
  line-height: 1;
  white-space: nowrap;
}

.input-control {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  padding: 0 $pf-space-3;
}

.input-control :deep(.uv-input) {
  width: 100%;
}

.code-divider {
  width: 1rpx;
  height: 40rpx;
  background: $pf-color-divider;
}

.code-action {
  display: flex;
  min-width: 192rpx;
  min-height: 94rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  padding: 0 $pf-space-2;
  color: $pf-color-primary;
  font-size: $pf-font-size-body;
  font-weight: $pf-font-weight-semibold;
  line-height: 1.4;
  text-align: center;
  white-space: nowrap;
}

.code-action--disabled {
  color: $pf-color-text-muted;
}

.code-action--pressed {
  background: $pf-color-primary-soft;
}

.agreement {
  display: flex;
  min-height: 80rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: $pf-space-4;
  padding: $pf-space-1 0;
  color: $pf-color-text-muted;
  font-size: $pf-font-size-label;
  line-height: 1.6;
  text-align: center;
}

.agreement-check {
  display: flex;
  width: 48rpx;
  height: 48rpx;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  margin-right: 2rpx;
}

.agreement-check__icon {
  display: flex;
  width: 28rpx;
  height: 28rpx;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  border: 2rpx solid $pf-color-text-muted;
  border-radius: 6rpx;
  background: $pf-color-surface;
}

.agreement-check__icon--checked {
  border-color: $pf-color-primary;
  background: $pf-color-primary;
}

.agreement-link {
  color: $pf-color-primary;
  font-weight: $pf-font-weight-medium;
}
</style>
