<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { hasAuthToken } from "./services/auth";

onLaunch(() => {
  if (hasAuthToken()) {
    uni.reLaunch({ url: "/pages/home/index" });
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
