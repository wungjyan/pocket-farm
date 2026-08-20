import { request } from "./http";
import type { HarvestRecord } from "./harvest";
import type { FarmOperation } from "./operation";
import type { Production } from "./production";

export type PlotType =
  | "FIELD"
  | "PADDY"
  | "GREENHOUSE"
  | "ORCHARD"
  | "FOREST"
  | "POND"
  | "BARN"
  | "OTHER";

export type AreaUnit = "MU" | "SQUARE_METER" | "HECTARE";

export interface Plot {
  id: number;
  farmId: number;
  name: string;
  type: PlotType | null;
  areaValue: number | string | null;
  areaUnit: AreaUnit | null;
  areaM2: number | string | null;
  boundary: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface PlotPage {
  items: Plot[];
  page: number;
  pageSize: number;
  total: number;
}

export interface PlotDetail {
  plot: Plot;
  activeProductions: Production[];
  endedProductions: Production[];
  operations: FarmOperation[];
  operationTotal: number;
  harvests: HarvestRecord[];
  harvestTotal: number;
}

export interface PlotInput {
  name: string;
  type?: PlotType | null;
  areaValue?: number | null;
  areaUnit?: AreaUnit | null;
  boundary?: Record<string, unknown> | null;
}

export function getFarmPlots(farmId: number, page = 1, pageSize = 100): Promise<PlotPage> {
  return request<PlotPage>({
    url: `/farms/${farmId}/plots?page=${page}&pageSize=${pageSize}`,
  });
}

export function createPlot(farmId: number, input: PlotInput): Promise<Plot> {
  return request<Plot>({
    url: `/farms/${farmId}/plots`,
    method: "POST",
    data: input,
  });
}

export function getPlot(plotId: number): Promise<Plot> {
  return request<Plot>({ url: `/plots/${plotId}` });
}

export function getPlotDetail(plotId: number): Promise<PlotDetail> {
  return request<PlotDetail>({ url: `/plots/${plotId}/detail` });
}

export function updatePlot(plotId: number, input: PlotInput): Promise<Plot> {
  return request<Plot>({
    url: `/plots/${plotId}`,
    method: "PATCH",
    data: input,
  });
}
