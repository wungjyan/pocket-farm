import { request } from "./http";

export type Industry = "AGRICULTURE" | "FORESTRY" | "LIVESTOCK" | "FISHERY";
export type IndividualUnit = "HEAD" | "FEATHER" | "PIECE" | "PLANT" | "TAIL";

export interface Species {
  id: number;
  name: string;
  industry: Industry;
  individualUnit: IndividualUnit;
  createdAt: string;
}

export interface SpeciesPage {
  items: Species[];
  page: number;
  pageSize: number;
  total: number;
}

export interface SpeciesQuery {
  industry?: Industry | null;
  keyword?: string;
  page?: number;
  pageSize?: number;
}

export function getSpecies(query: SpeciesQuery = {}): Promise<SpeciesPage> {
  const parameters = [`page=${query.page || 1}`, `pageSize=${query.pageSize || 100}`];
  if (query.industry) parameters.push(`industry=${query.industry}`);
  if (query.keyword?.trim()) parameters.push(`keyword=${encodeURIComponent(query.keyword.trim())}`);
  return request<SpeciesPage>({ url: `/species?${parameters.join("&")}` });
}
