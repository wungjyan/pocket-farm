import { request } from "./http";
import type { QuantityUnit } from "./harvest";
import type { Industry } from "./species";

export const FARM_ACTIVITIES_CHANGED_EVENT = "pocket-farm:activities-changed";

export function notifyFarmActivitiesChanged(farmId: number): void {
  uni.$emit(FARM_ACTIVITIES_CHANGED_EVENT, farmId);
}

export type FarmActivityType =
  | "PRODUCTION_STARTED"
  | "PRODUCTION_ENDED"
  | "OPERATION_CREATED"
  | "HARVEST_CREATED";

export interface FarmActivity {
  type: FarmActivityType;
  occurredAt: string;
  productionId: number | null;
  operationId: number | null;
  harvestId: number | null;
  plotId: number;
  plotName: string;
  plotAreaValue: number | string | null;
  plotAreaUnit: "MU" | "SQUARE_METER" | "HECTARE" | null;
  speciesName: string | null;
  industry: Industry | null;
  operationTypeName: string | null;
  quantity: number | string | null;
  unit: QuantityUnit | null;
  operatorName: string | null;
}

export interface FarmActivityListResponse {
  items: FarmActivity[];
}

export function getFarmActivities(
  farmId: number,
  limit = 5,
): Promise<FarmActivityListResponse> {
  return request<FarmActivityListResponse>({
    url: `/farms/${farmId}/activities?limit=${limit}`,
  });
}
