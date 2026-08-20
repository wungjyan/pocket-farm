import { onUnmounted, watch, type Ref } from "vue";

/**
 * 使用微信原生页面返回确认保护未保存表单。
 * 非微信平台没有对应能力时静默降级，不接管页面导航。
 */
export function useUnsavedChangesGuard(
  dirty: Ref<boolean>,
  message = "当前内容尚未保存，确定离开吗？",
): void {
  let enabled = false;

  const enable = (): void => {
    if (enabled || typeof uni.enableAlertBeforeUnload !== "function") return;
    uni.enableAlertBeforeUnload({ message });
    enabled = true;
  };

  const disable = (): void => {
    if (!enabled || typeof uni.disableAlertBeforeUnload !== "function") return;
    uni.disableAlertBeforeUnload();
    enabled = false;
  };

  watch(dirty, (value) => (value ? enable() : disable()), { immediate: true });
  onUnmounted(disable);
}
