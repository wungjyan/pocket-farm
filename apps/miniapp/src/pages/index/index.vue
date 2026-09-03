<template>
  <view class="entry-page" />
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { clearAuthToken, hasAuthToken } from "../../services/auth";
import { useFarmContext } from "../../services/farm-context";
import { useUserContext } from "../../services/user-context";

function navigateToLogin(): void {
  uni.reLaunch({ url: "/pages/auth/login" });
}

async function resolveEntry(): Promise<void> {
  if (!hasAuthToken()) {
    navigateToLogin();
    return;
  }

  try {
    const user = await useUserContext().ensureCurrentUser();
    if (!user) {
      throw new Error("当前用户信息不可用");
    }
    await useFarmContext().initializeFarmSession();
    uni.reLaunch({ url: "/pages/home/index" });
  } catch {
    clearAuthToken();
    useFarmContext().endFarmSession();
    navigateToLogin();
  }
}

onLoad(() => {
  void resolveEntry();
});
</script>

<style lang="scss" scoped>
@import "../../styles/design-tokens.scss";

.entry-page {
  min-height: 100vh;
  background: $pf-color-page;
}
</style>
