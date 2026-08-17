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

page {
  background: $uni-bg-color-grey;
  color: $uni-text-color;
}
</style>
