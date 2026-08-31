<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { hasAuthToken } from "./services/auth";
import { useUserContext } from "./services/user-context";

onLaunch(() => {
  if (hasAuthToken()) {
    // 老会话本地无用户缓存时兜底拉一次，之后由登录/改昵称写入点维护。
    // 失败静默忽略，不影响启动流程。
    useUserContext().ensureCurrentUser().catch(() => {});
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
