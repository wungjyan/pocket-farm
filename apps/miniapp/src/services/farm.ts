import { request } from "./http";

export type FarmRole = "OWNER" | "ADMIN" | "MEMBER";

export interface Farm {
  id: number;
  farmCode: string;
  name: string;
  region: string | null;
  createdBy: number;
  createdAt: string;
  updatedAt: string;
  myRole?: FarmRole | null;
}

export interface FarmPage {
  items: Farm[];
  page: number;
  pageSize: number;
  total: number;
}

interface CurrentFarmPayload {
  currentFarm: Farm | null;
}

export interface FarmMember {
  id: number;
  userId: number;
  nickname: string | null;
  role: FarmRole;
  joinedAt: string;
}

export interface FarmMemberPage {
  items: FarmMember[];
  page: number;
  pageSize: number;
  total: number;
}

export interface CreateFarmInput {
  name: string;
  region?: string | null;
}

export interface UpdateFarmInput {
  name?: string;
  region?: string | null;
}

export function getMyFarms(page = 1, pageSize = 100): Promise<FarmPage> {
  return request<FarmPage>({
    url: `/farms?page=${page}&pageSize=${pageSize}`,
  });
}

export async function getCurrentFarm(): Promise<Farm | null> {
  const payload = await request<CurrentFarmPayload>({ url: "/farms/current" });
  return payload.currentFarm;
}

export function setCurrentFarm(farmId: number): Promise<Farm> {
  return request<Farm>({
    url: "/farms/current",
    method: "PUT",
    data: { farmId },
  });
}

export function createFarm(input: CreateFarmInput): Promise<Farm> {
  return request<Farm>({
    url: "/farms",
    method: "POST",
    data: input,
  });
}

export function getFarm(farmId: number): Promise<Farm> {
  return request<Farm>({ url: `/farms/${farmId}` });
}

export function updateFarm(farmId: number, input: UpdateFarmInput): Promise<Farm> {
  return request<Farm>({
    url: `/farms/${farmId}`,
    method: "PATCH",
    data: input,
  });
}

export function getFarmMembers(
  farmId: number,
  page = 1,
  pageSize = 100,
): Promise<FarmMemberPage> {
  return request<FarmMemberPage>({
    url: `/farms/${farmId}/members?page=${page}&pageSize=${pageSize}`,
  });
}

export function addFarmMember(
  farmId: number,
  phoneNumber: string,
  role: FarmRole = "MEMBER",
): Promise<FarmMember> {
  return request<FarmMember>({
    url: `/farms/${farmId}/members`,
    method: "POST",
    data: { phoneNumber, role },
  });
}

export function updateFarmMember(
  farmId: number,
  memberId: number,
  role: FarmRole,
): Promise<FarmMember> {
  return request<FarmMember>({
    url: `/farms/${farmId}/members/${memberId}`,
    method: "PATCH",
    data: { role },
  });
}

export function removeFarmMember(farmId: number, memberId: number): Promise<void> {
  return request<void>({
    url: `/farms/${farmId}/members/${memberId}`,
    method: "DELETE",
  });
}

export function leaveFarm(farmId: number): Promise<void> {
  return request<void>({
    url: `/farms/${farmId}/members/me`,
    method: "DELETE",
  });
}
