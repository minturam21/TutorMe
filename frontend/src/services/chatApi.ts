
import { apiClient } from "./apiClient";

import type {
  ChatStreamRequest,
  Conversation,
  CreateConversationRequest,
  CreateConversationResponse,
  Message,
} from "../types/chat";

export const chatApi = {
  // Create a new conversation.
  createConversation(
    request: CreateConversationRequest
  ): Promise<CreateConversationResponse> {
    return apiClient.post<CreateConversationResponse>(
      "/conversations",
      request
    );
  },

  // Get all saved conversations.
  getConversations(): Promise<Conversation[]> {
    return apiClient.get<Conversation[]>("/conversations");
  },

  // Get messages from a conversation.
  getMessages(conversationId: number): Promise<Message[]> {
    return apiClient.get<Message[]>(
      `/conversations/${conversationId}/messages`
    );
  },

  // Delete a conversation.
  deleteConversation(conversationId: number): Promise<void> {
    return apiClient.delete(`/conversations/${conversationId}`);
  },

  // Send a message using the existing streaming endpoint.
  streamMessage(request: ChatStreamRequest): Promise<Response> {
    return apiClient.postStream("/ask/stream", request);
  },
};
