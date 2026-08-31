import { request } from "./http";
import type { ProductionStatus, WorkMethod } from "./production";

export type OperationTypeStatus = "ACTIVE" | "DISABLED";

export interface OperationType {
  id: number;
  code: string;
  name: string;
  status: OperationTypeStatus;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

export interface OperationTypePage {
  items: OperationType[];
  page: number;
  pageSize: number;
  total: number;
}

export interface FarmOperation {
  id: number;
  plotId: number;
  productionId: number | null;
  operationType: OperationType;
  workMethod: WorkMethod;
  operatedAt: string;
  operatorId: number;
  createdBy: number;
  remark: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface OperationPage {
  items: FarmOperation[];
  page: number;
  pageSize: number;
  total: number;
}

export interface FarmOperationSummary {
  id: number;
  plotId: number;
  plotName: string;
  plotAreaValue: number | string | null;
  plotAreaUnit: "MU" | "SQUARE_METER" | "HECTARE" | null;
  productionId: number | null;
  operationTypeId: number;
  operationTypeName: string;
  operatedAt: string;
  speciesName: string | null;
  productionStatus: ProductionStatus | null;
}

export interface FarmOperationSummaryPage {
  items: FarmOperationSummary[];
  page: number;
  pageSize: number;
  total: number;
}

export interface OperationTypeOption {
  id: number;
  name: string;
}

export interface OperationFilterOptions {
  types: OperationTypeOption[];
}

export interface FarmOperationListParams {
  operationTypeId?: number;
  page?: number;
  pageSize?: number;
}

export interface OperationInput {
  productionId: number | null;
  operationTypeId: number;
  workMethod: WorkMethod;
  operatedAt: string;
  operatorId: number;
  remark?: string | null;
}

export type OperationUpdateInput = Partial<OperationInput>;

export function getPlotOperations(
  plotId: number,
  page = 1,
  pageSize = 100,
): Promise<OperationPage> {
  return request<OperationPage>({
    url: `/plots/${plotId}/operations?page=${page}&pageSize=${pageSize}`,
  });
}

export function getOperation(operationId: number): Promise<FarmOperation> {
  return request<FarmOperation>({ url: `/operations/${operationId}` });
}

export function getFarmOperations(
  farmId: number,
  params: FarmOperationListParams = {},
): Promise<FarmOperationSummaryPage> {
  const parameters = [`page=${params.page || 1}`, `pageSize=${params.pageSize || 20}`];
  if (params.operationTypeId) parameters.push(`operationTypeId=${params.operationTypeId}`);
  return request<FarmOperationSummaryPage>({
    url: `/farms/${farmId}/operations?${parameters.join("&")}`,
  });
}

export function getOperationFilterOptions(farmId: number): Promise<OperationFilterOptions> {
  return request<OperationFilterOptions>({ url: `/farms/${farmId}/operation-filter-options` });
}

export function getOperationTypes(page = 1, pageSize = 100): Promise<OperationTypePage> {
  return request<OperationTypePage>({ url: `/operation-types?page=${page}&pageSize=${pageSize}` });
}

export function createOperation(plotId: number, input: OperationInput): Promise<FarmOperation> {
  return request<FarmOperation>({
    url: `/plots/${plotId}/operations`,
    method: "POST",
    data: input,
  });
}

export function updateOperation(
  operationId: number,
  input: OperationUpdateInput,
): Promise<FarmOperation> {
  return request<FarmOperation>({
    url: `/operations/${operationId}`,
    method: "PATCH",
    data: input,
  });
}

export function deleteOperation(operationId: number): Promise<void> {
  return request<void>({ url: `/operations/${operationId}`, method: "DELETE" });
}
