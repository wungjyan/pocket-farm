import { defineComponent, h, nextTick, onMounted, watch } from "vue";
import type { Theme } from "vitepress";
import DefaultTheme from "vitepress/theme";
import { useData } from "vitepress";
import { createMermaidRenderer } from "vitepress-mermaid-renderer";
import "vitepress-mermaid-renderer/css";

const MermaidLayout = defineComponent({
  name: "MermaidLayout",
  setup() {
    const { isDark } = useData();

    const renderMermaid = () => {
      void nextTick(() => {
        const renderer = createMermaidRenderer({
          theme: isDark.value ? "dark" : "default",
        });

        renderer.setToolbar({
          fullscreenMode: "dialog",
          downloadFormat: "svg",
          i18n: {
            tooltips: {
              zoomIn: "放大",
              zoomOut: "缩小",
              resetView: "重置视图",
              copyCode: "复制 Mermaid 源码",
              copyCodeCopied: "已复制",
              toggleFullscreen: "全屏查看",
              download: "下载图表",
              renderErrorText: "图表渲染失败",
              toggleErrorDetailsText: "查看错误详情",
              toggleErrorDetailsHideText: "收起错误详情",
            },
          },
        });
      });
    };

    onMounted(renderMermaid);
    watch(isDark, renderMermaid);

    return () => h(DefaultTheme.Layout);
  },
});

export default {
  extends: DefaultTheme,
  Layout: MermaidLayout,
} satisfies Theme;
