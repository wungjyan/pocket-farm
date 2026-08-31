import { request } from "./http";
import type { IndividualUnit, Industry, Species } from "./species";

export type ProductionStatus = "ACTIVE" | "ENDED";
export type PlantingStandard = "NORMAL" | "GREEN" | "ORGANIC";
export type PlantingMethod = "TRANSPLANT" | "DIRECT_SEEDING";
export type WorkMethod = "MANUAL" | "MECHANICAL";

export interface Production {
  id: number;
  plotId: number;
  speciesId: number;
  speciesName: string;
  industry: Industry;
  individualUnit: IndividualUnit;
  variety: string | null;
  status: ProductionStatus;
  startedOn: string;
  endedOn: string | null;
  plantingStandard: PlantingStandard | null;
  plantingMethod: PlantingMethod | null;
  workMethod: WorkMethod | null;
  expectedHarvestOn: string | null;
  expectedYieldPerMu: number | string | null;
  initialQuantity: number | string | null;
  plantSpacingCm: number | string | null;
  entryAgeDays: number | null;
  remark: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ProductionPage {
  items: Production[];
  page: number;
  pageSize: number;
  total: number;
}

export interface FarmProduction {
  id: number;
  plotId: number;
  plotName: string;
  plotAreaValue: number | string | null;
  plotAreaUnit: "MU" | "SQUARE_METER" | "HECTARE" | null;
  speciesId: number;
  speciesName: string;
  industry: Industry;
  individualUnit: IndividualUnit;
  variety: string | null;
  status: ProductionStatus;
  startedOn: string;
  endedOn: string | null;
  initialQuantity: number | string | null;
}

export interface FarmProductionPage {
  items: FarmProduction[];
  page: number;
  pageSize: number;
  total: number;
}

export interface FarmProductionListParams {
  industry?: Industry;
  status?: ProductionStatus;
  speciesId?: number;
  page?: number;
  pageSize?: number;
}

export interface ProductionSpeciesOption {
  id: number;
  name: string;
}

export interface ProductionFilterOptions {
  species: ProductionSpeciesOption[];
}

export interface ProductionInput {
  speciesId: number;
  variety?: string | null;
  startedOn: string;
  plantingStandard?: PlantingStandard | null;
  plantingMethod?: PlantingMethod | null;
  workMethod?: WorkMethod | null;
  expectedHarvestOn?: string | null;
  expectedYieldPerMu?: number | null;
  initialQuantity?: number | null;
  plantSpacingCm?: number | null;
  entryAgeDays?: number | null;
  remark?: string | null;
}

export interface ProductionUpdateInput extends Partial<ProductionInput> {
  plotId?: number;
}

export interface EndProductionInput {
  endedOn?: string;
}

export function getPlotProductions(
  plotId: number,
  status?: ProductionStatus,
  page = 1,
  pageSize = 100,
): Promise<ProductionPage> {
  const parameters = [`page=${page}`, `pageSize=${pageSize}`];
  if (status) parameters.push(`status=${status}`);
  return request<ProductionPage>({ url: `/plots/${plotId}/productions?${parameters.join("&")}` });
}

export function getFarmProductions(
  farmId: number,
  params: FarmProductionListParams = {},
): Promise<FarmProductionPage> {
  const parameters = [`page=${params.page || 1}`, `pageSize=${params.pageSize || 20}`];
  if (params.industry) parameters.push(`industry=${params.industry}`);
  if (params.status) parameters.push(`status=${params.status}`);
  if (params.speciesId) parameters.push(`speciesId=${params.speciesId}`);
  return request<FarmProductionPage>({
    url: `/farms/${farmId}/productions?${parameters.join("&")}`,
  });
}

export function getProductionFilterOptions(
  farmId: number,
  industry?: Industry,
): Promise<ProductionFilterOptions> {
  const parameters: string[] = [];
  if (industry) parameters.push(`industry=${industry}`);
  const query = parameters.length ? `?${parameters.join("&")}` : "";
  return request<ProductionFilterOptions>({ url: `/farms/${farmId}/production-filter-options${query}` });
}

export function createProduction(plotId: number, input: ProductionInput): Promise<Production> {
  return request<Production>({
    url: `/plots/${plotId}/productions`,
    method: "POST",
    data: input,
  });
}

export function getProduction(productionId: number): Promise<Production> {
  return request<Production>({ url: `/productions/${productionId}` });
}

export function updateProduction(
  productionId: number,
  input: ProductionUpdateInput,
): Promise<Production> {
  return request<Production>({
    url: `/productions/${productionId}`,
    method: "PATCH",
    data: input,
  });
}

export function deleteProduction(productionId: number): Promise<void> {
  return request<void>({ url: `/productions/${productionId}`, method: "DELETE" });
}

export function endProduction(
  productionId: number,
  input: EndProductionInput = {},
): Promise<Production> {
  return request<Production>({
    url: `/productions/${productionId}/end`,
    method: "POST",
    data: input,
  });
}

export function toSpecies(production: Production): Species {
  return {
    id: production.speciesId,
    name: production.speciesName,
    industry: production.industry,
    individualUnit: production.individualUnit,
    createdAt: production.createdAt,
  };
}
