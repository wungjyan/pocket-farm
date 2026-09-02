import { request } from "./http";

export type AIReferenceKind = "PLOT" | "PRODUCTION" | "OPERATION" | "HARVEST" | "SPECIES";

export interface AIReference {
  kind: AIReferenceKind;
  id: number;
  label: string;
  route: string;
}

export interface AITurnInput {
  conversationId: number;
  message: string;
}

export interface AITurnResult {
  answer: string;
  references: AIReference[];
  needsSelection: boolean;
  candidates: AIReference[];
}

export interface AIConversation {
  id: number;
  farmId: number;
  farmName: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface AIConversationPage {
  items: AIConversation[];
  page: number;
  pageSize: number;
  total: number;
}

export interface AIMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  references: AIReference[];
  candidates: AIReference[];
  createdAt: string;
}

export interface AIMessagePage {
  items: AIMessage[];
  page: number;
  pageSize: number;
  total: number;
}

export function createAIConversation(farmId: number): Promise<AIConversation> {
  return request<AIConversation>({
    url: "/ai/conversations",
    method: "POST",
    data: { farmId },
  });
}

export function getAIConversations(page = 1, pageSize = 20): Promise<AIConversationPage> {
  return request<AIConversationPage>({
    url: `/ai/conversations?page=${page}&pageSize=${pageSize}`,
  });
}

export function getAIMessages(
  conversationId: number,
  page = 1,
  pageSize = 100,
): Promise<AIMessagePage> {
  return request<AIMessagePage>({
    url: `/ai/conversations/${conversationId}/messages?page=${page}&pageSize=${pageSize}`,
  });
}

export function deleteAIConversation(conversationId: number): Promise<void> {
  return request<void>({
    url: `/ai/conversations/${conversationId}`,
    method: "DELETE",
  });
}

export function createAITurn(input: AITurnInput): Promise<AITurnResult> {
  return request<AITurnResult>({
    url: "/ai/turn",
    method: "POST",
    data: input,
  });
}
