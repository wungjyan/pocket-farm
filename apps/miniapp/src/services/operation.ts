import { request } from "./http";
import type { WorkMethod } from "./production";

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
