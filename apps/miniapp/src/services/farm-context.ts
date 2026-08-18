import { computed, ref } from "vue";
import { getMyFarms, type Farm } from "./farm";

const CURRENT_FARM_KEY = "pocket_farm_current_farm";

export interface FarmSummary {
  id: number;
  farmCode?: string;
  name: string;
  region?: string | null;
  role?: "OWNER" | "ADMIN" | "MEMBER";
  plotCount?: number;
  activeProductionCount?: number;
}

function readStoredFarm(): FarmSummary | null {
  const value = uni.getStorageSync(CURRENT_FARM_KEY);
  if (!value) return null;

  try {
    const parsed = typeof value === "string" ? JSON.parse(value) : value;
    if (typeof parsed?.id !== "number" || typeof parsed?.name !== "string") {
      return null;
    }
    return parsed as FarmSummary;
  } catch {
    return null;
  }
}

const currentFarm = ref<FarmSummary | null>(readStoredFarm());

function persistFarm(farm: FarmSummary | null): void {
  if (farm) {
    uni.setStorageSync(CURRENT_FARM_KEY, JSON.stringify(farm));
  } else {
    uni.removeStorageSync(CURRENT_FARM_KEY);
  }
}

export function useFarmContext() {
  const currentFarmName = computed(() => currentFarm.value?.name || "暂无农场");
  const hasCurrentFarm = computed(() => currentFarm.value !== null);

  function selectFarm(farm: FarmSummary): void {
    currentFarm.value = farm;
    persistFarm(farm);
  }

  /**
   * 在成功获取当前用户可访问农场后调用。
   * 已保存的农场仍可访问则继续使用，否则回退到第一个有效农场；列表为空则清除上下文。
   */
  function syncAvailableFarms(farms: FarmSummary[]): FarmSummary | null {
    const matched = currentFarm.value
      ? farms.find((farm) => farm.id === currentFarm.value?.id)
      : undefined;
    const nextFarm = matched || farms[0] || null;
    currentFarm.value = nextFarm;
    persistFarm(nextFarm);
    return nextFarm;
  }

  function clearFarm(): void {
    currentFarm.value = null;
    persistFarm(null);
  }

  async function refreshFromApi(): Promise<FarmSummary | null> {
    const page = await getMyFarms();
    return syncAvailableFarms(page.items.map(toFarmSummary));
  }

  return {
    currentFarm,
    currentFarmName,
    hasCurrentFarm,
    selectFarm,
    syncAvailableFarms,
    refreshFromApi,
    clearFarm,
  };
}

export function toFarmSummary(farm: Farm): FarmSummary {
  return {
    id: farm.id,
    farmCode: farm.farmCode,
    name: farm.name,
    region: farm.region,
    role: farm.myRole || undefined,
  };
}
