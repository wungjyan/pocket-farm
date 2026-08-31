import { request } from "./http";
import type { Plot } from "./plot";
import type { Production, WorkMethod } from "./production";

export type QuantityUnit = "KG" | "HEAD" | "FEATHER" | "PIECE" | "PLANT" | "TAIL";

export interface HarvestRecord {
  id: number;
  productionId: number;
  quantity: number | string;
  unit: QuantityUnit;
  workMethod: WorkMethod;
  harvestedAt: string;
  operatorId: number;
  createdBy: number;
  productName: string | null;
  grade: string | null;
  remark: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface HarvestProductionSelection {
  production: Production;
  plot: Plot;
}

export interface HarvestPage {
  items: HarvestRecord[];
  page: number;
  pageSize: number;
  total: number;
}

export interface HarvestInput {
  quantity: number;
  workMethod: WorkMethod;
  harvestedAt: string;
  operatorId: number;
  productName?: string | null;
  grade?: string | null;
  remark?: string | null;
}

export type HarvestUpdateInput = Partial<HarvestInput>;

export function getProductionHarvests(
  productionId: number,
  page = 1,
  pageSize = 100,
): Promise<HarvestPage> {
  return request<HarvestPage>({
    url: `/productions/${productionId}/harvests?page=${page}&pageSize=${pageSize}`,
  });
}

export function getPlotHarvests(
  plotId: number,
  page = 1,
  pageSize = 100,
): Promise<HarvestPage> {
  return request<HarvestPage>({
    url: `/plots/${plotId}/harvests?page=${page}&pageSize=${pageSize}`,
  });
}

export function getHarvest(harvestId: number): Promise<HarvestRecord> {
  return request<HarvestRecord>({ url: `/harvests/${harvestId}` });
}

export function createHarvest(
  productionId: number,
  input: HarvestInput,
): Promise<HarvestRecord> {
  return request<HarvestRecord>({
    url: `/productions/${productionId}/harvests`,
    method: "POST",
    data: input,
  });
}

export function updateHarvest(
  harvestId: number,
  input: HarvestUpdateInput,
): Promise<HarvestRecord> {
  return request<HarvestRecord>({
    url: `/harvests/${harvestId}`,
    method: "PATCH",
    data: input,
  });
}

export function deleteHarvest(harvestId: number): Promise<void> {
  return request<void>({ url: `/harvests/${harvestId}`, method: "DELETE" });
}
