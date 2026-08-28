import { request } from "./http";
import type { FarmOperation } from "./operation";
import type { HarvestRecord } from "./harvest";
import type { Plot } from "./plot";
import type { FarmMember } from "./farm";

export interface DashboardOperationItem {
  operation: FarmOperation;
  plotId: number;
  plotName: string;
}

export interface DashboardHarvestItem {
  harvest: HarvestRecord;
  plotId: number;
  plotName: string;
  industry: string | null;
}

export interface FarmDashboardResponse {
  recentOperations: DashboardOperationItem[];
  recentHarvests: DashboardHarvestItem[];
  members: FarmMember[];
  plots: Plot[];
}

export function getFarmDashboard(farmId: number): Promise<FarmDashboardResponse> {
  return request<FarmDashboardResponse>({
    url: `/farms/${farmId}/dashboard`,
  });
}
