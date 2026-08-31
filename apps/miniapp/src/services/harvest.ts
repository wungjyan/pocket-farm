import { request } from "./http";
import type { Plot } from "./plot";
import type { Production, ProductionStatus, WorkMethod } from "./production";
import type { Industry } from "./species";

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

export interface FarmHarvestSummary {
  id: number;
  productionId: number;
  productionStatus: ProductionStatus;
  plotId: number;
  plotName: string;
  plotAreaValue: number | string | null;
  plotAreaUnit: "MU" | "SQUARE_METER" | "HECTARE" | null;
  speciesId: number;
  speciesName: string;
  industry: Industry;
  quantity: number | string;
  unit: QuantityUnit;
  harvestedAt: string;
  productName: string | null;
  operatorId: number;
  operatorName: string | null;
  createdBy: number;
  creatorName: string | null;
}

export interface FarmHarvestPage {
  items: FarmHarvestSummary[];
  page: number;
  pageSize: number;
  total: number;
}

export interface FarmHarvestListParams {
  industry?: Industry;
  speciesId?: number;
  page?: number;
  pageSize?: number;
}

export interface HarvestSpeciesOption {
  id: number;
  name: string;
}

export interface HarvestFilterOptions {
  species: HarvestSpeciesOption[];
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

export function getFarmHarvests(
  farmId: number,
  params: FarmHarvestListParams = {},
): Promise<FarmHarvestPage> {
  const parameters = [`page=${params.page || 1}`, `pageSize=${params.pageSize || 20}`];
  if (params.industry) parameters.push(`industry=${params.industry}`);
  if (params.speciesId) parameters.push(`speciesId=${params.speciesId}`);
  return request<FarmHarvestPage>({
    url: `/farms/${farmId}/harvests?${parameters.join("&")}`,
  });
}

export function getHarvestFilterOptions(
  farmId: number,
  industry: Industry,
): Promise<HarvestFilterOptions> {
  return request<HarvestFilterOptions>({
    url: `/farms/${farmId}/harvest-filter-options?industry=${industry}`,
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
