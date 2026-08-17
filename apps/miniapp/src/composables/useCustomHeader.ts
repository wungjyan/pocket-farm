import { computed, onMounted, ref } from "vue";

/**
 * 为微信小程序自定义导航栏预留状态栏和胶囊按钮空间。
 * H5 等没有胶囊按钮的平台使用安全的默认间距。
 */
export function useCustomHeader() {
  const statusBarHeight = ref(0);
  const contentHeight = ref(44);
  const rightPadding = ref(32);

  onMounted(() => {
    const systemInfo = uni.getSystemInfoSync();
    statusBarHeight.value = systemInfo.statusBarHeight || 0;

    if (typeof uni.getMenuButtonBoundingClientRect !== "function") {
      return;
    }

    const menuButton = uni.getMenuButtonBoundingClientRect();
    const windowWidth = systemInfo.windowWidth || 375;
    const menuOffsetTop = Math.max(menuButton.top - statusBarHeight.value, 0);

    contentHeight.value = Math.max(44, menuButton.height + menuOffsetTop * 2);
    rightPadding.value = Math.max(32, windowWidth - menuButton.left + 12);
  });

  const headerStyle = computed(() => ({
    paddingTop: `${statusBarHeight.value}px`,
  }));

  const headerInnerStyle = computed(() => ({
    height: `${contentHeight.value}px`,
    paddingRight: `${rightPadding.value}px`,
  }));

  return { headerStyle, headerInnerStyle };
}
