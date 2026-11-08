
import { useState } from "react";
import type { Message, Conversation } from "../types/chat";
import { chatApi } from "../services/chatApi";

const ACTIVE_CONVERSATION_KEY = "tutorme_active_conversation_id";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  function appendToLastAssistantMessage(content: string) {
    setMessages((previous) => {
      const updated = [...previous];
      const lastIndex = updated.length - 1;

      if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
        updated[lastIndex] = {
          ...updated[lastIndex],
          content: updated[lastIndex].content + content,
        };
      }

      return updated;
    });
  }

  async function loadConversations() {
    const data = await chatApi.getConversations();
    setConversations(data);
    return data;
  }

  async function openConversation(id: number) {
    if (loading) return false;

    setLoading(true);

    try {
      const data = await chatApi.getMessages(id);

      setMessages(data);
      setConversationId(id);
      localStorage.setItem(ACTIVE_CONVERSATION_KEY, String(id));

      return true;
    } catch (error) {
      console.error("Conversation loading error:", error);
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function deleteConversation(id: number) {
    await chatApi.deleteConversation(id);

    setConversations((previous) =>
      previous.filter((conversation) => conversation.id !== id)
    );

    if (conversationId === id) {
      setConversationId(null);
      setMessages([]);
      localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
    }
  }

  async function sendMessage(text: string) {
    const trimmedText = text.trim();

    if (!trimmedText || loading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", content: trimmedText },
      { role: "assistant", content: "" },
    ]);

    setLoading(true);

    try {
      let activeConversationId = conversationId;

      if (activeConversationId === null) {
        const conversation = await chatApi.createConversation({
          title: trimmedText.slice(0, 60),
        });

        activeConversationId = conversation.id;
        setConversationId(activeConversationId);

        setConversations((previous) => [
          conversation,
          ...previous,
        ]);
      }

      localStorage.setItem(
        ACTIVE_CONVERSATION_KEY,
        String(activeConversationId)
      );

      const response = await chatApi.streamMessage({
        message: trimmedText,
        conversation_id: activeConversationId,
      });

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        appendToLastAssistantMessage(
          decoder.decode(value, { stream: true })
        );
      }

      appendToLastAssistantMessage(decoder.decode());
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Something went wrong.";

      appendToLastAssistantMessage(`Sorry, ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }

  function startNewChat() {
    setMessages([]);
    setConversationId(null);
    localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
  }

  return {
    messages,
    setMessages,
    conversations,
    setConversations,
    conversationId,
    setConversationId,
    loading,
    setLoading,
    loadConversations,
    openConversation,
    deleteConversation,
    sendMessage,
    startNewChat,
  };
}
