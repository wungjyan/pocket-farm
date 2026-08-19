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

export function toSpecies(production: Production): Species {
  return {
    id: production.speciesId,
    name: production.speciesName,
    industry: production.industry,
    individualUnit: production.individualUnit,
    createdAt: production.createdAt,
  };
}
