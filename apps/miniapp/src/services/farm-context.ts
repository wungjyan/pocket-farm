import { computed, ref } from "vue";
import { getCurrentFarm, setCurrentFarm, type Farm } from "./farm";

const LEGACY_CURRENT_FARM_KEY = "pocket_farm_current_farm";

export interface FarmSummary {
  id: number;
  farmCode?: string;
  name: string;
  region?: string | null;
  aiEnabled?: boolean;
  role?: "OWNER" | "ADMIN" | "MEMBER";
  plotCount?: number;
  activeProductionCount?: number;
}

export type FarmSessionStatus = "SELECTED" | "NO_FARMS";

const currentFarm = ref<FarmSummary | null>(null);

function clearLegacyFarmCache(): void {
  uni.removeStorageSync(LEGACY_CURRENT_FARM_KEY);
  uni
    .getStorageInfoSync()
    .keys.filter((key) => key.startsWith("pocket_farm_last_farm_"))
    .forEach((key) => uni.removeStorageSync(key));
}

export function useFarmContext() {
  const currentFarmName = computed(() => currentFarm.value?.name || "暂无农场");
  const hasCurrentFarm = computed(() => currentFarm.value !== null);

  function selectFarm(farm: FarmSummary): void {
    currentFarm.value = farm;
  }

  async function selectFarmAndPersist(farm: FarmSummary): Promise<FarmSummary> {
    const selectedFarm = await setCurrentFarm(farm.id);
    const summary = toFarmSummary(selectedFarm);
    selectFarm(summary);
    return summary;
  }

  /**
   * 仅同步当前会话已有选择的农场快照；当前农场的自动解析由服务端负责。
   */
  function syncAvailableFarms(farms: FarmSummary[]): FarmSummary | null {
    const selectedFarm = currentFarm.value;
    if (!selectedFarm) return null;

    const matched = farms.find((farm) => farm.id === selectedFarm.id);
    if (matched) {
      currentFarm.value = matched;
      return matched;
    }

    currentFarm.value = null;
    return null;
  }

  /** 登录后或持久会话启动时调用，仅从服务端解析当前农场。 */
  async function initializeFarmSession(): Promise<FarmSessionStatus> {
    currentFarm.value = null;
    clearLegacyFarmCache();

    const farm = await getCurrentFarm();
    if (!farm) return "NO_FARMS";
    selectFarm(toFarmSummary(farm));
    return "SELECTED";
  }

  /** 结束当前账号会话；服务端持久化的农场偏好会保留。 */
  function endFarmSession(): void {
    currentFarm.value = null;
    clearLegacyFarmCache();
  }

  /** 当前农场已不可访问时清空活动上下文。 */
  function clearFarm(): void {
    currentFarm.value = null;
  }

  return {
    currentFarm,
    currentFarmName,
    hasCurrentFarm,
    selectFarm,
    selectFarmAndPersist,
    syncAvailableFarms,
    initializeFarmSession,
    endFarmSession,
    clearFarm,
  };
}

export function toFarmSummary(farm: Farm): FarmSummary {
  return {
    id: farm.id,
    farmCode: farm.farmCode,
    name: farm.name,
    region: farm.region,
    aiEnabled: farm.aiEnabled,
    role: farm.myRole || undefined,
  };
}
