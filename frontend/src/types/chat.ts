
export type MessageRole = "user" | "assistant";

// A message displayed in the chat.
export interface Message {
  role: MessageRole;
  content: string;
}

// A saved conversation shown in the sidebar.
export interface Conversation {
  id: number;
  title: string;
}

// Current application viewing mode.
export type TutorMode = "chat" | "whiteboard";

// Request sent when creating a conversation.
export interface CreateConversationRequest {
  title: string;
}

// Response returned after creating a conversation.
export interface CreateConversationResponse {
  id: number;
  title: string;
}

// Request sent to POST /ask/stream.
export interface ChatStreamRequest {
  message: string;
  conversation_id: number | null;
}
