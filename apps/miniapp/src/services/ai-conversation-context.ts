import { ref } from "vue";
import type { AIConversation } from "./ai";

const activeConversation = ref<AIConversation | null>(null);

export function useAIConversationContext() {
  function selectAIConversation(conversation: AIConversation): void {
    activeConversation.value = conversation;
  }

  function clearAIConversation(): void {
    activeConversation.value = null;
  }

  return { activeConversation, selectAIConversation, clearAIConversation };
}
