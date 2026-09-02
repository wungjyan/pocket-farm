<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { hasAuthToken } from "./services/auth";
import { useFarmContext } from "./services/farm-context";
import { useUserContext } from "./services/user-context";

onLaunch(() => {
  if (hasAuthToken()) {
    void (async () => {
      try {
        const user = await useUserContext().ensureCurrentUser();
        if (!user) return;
        await useFarmContext().initializeFarmSession();
        uni.reLaunch({ url: "/pages/home/index" });
      } catch {
        uni.reLaunch({ url: "/pages/home/index" });
      }
    })();
  }
});
onShow(() => {
});
onHide(() => {
});
</script>

<style lang="scss">
@import "@/uni_modules/uv-ui-tools/index.scss";
@import "@/styles/pocket-farm.scss";

page {
  background: $pf-color-page;
  color: $uni-text-color;
}
</style>
