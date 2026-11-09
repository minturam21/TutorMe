import { useState, useEffect, useRef, type FormEvent } from "react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

import "katex/dist/katex.min.css";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

import "./App.css";

import Whiteboard from "./components/Whiteboard";
import StructuredLessonWhiteboard from "./components/whiteboard/StructuredLessonWhiteboard";

import { chatApi } from "./services/chatApi";
import { lessonApi } from "./services/lessonApi";

import { useChat } from "./hooks/useChat";

import type { TutorMode } from "./types/chat";
import type { Lesson } from "./types/lesson";
import TegakiTest from "./components/whiteboard/TegakiTest";

const ACTIVE_CONVERSATION_KEY = "tutorme_active_conversation_id";

/**
 * Prepare AI responses for ReactMarkdown.
 *
 * - Hides legacy visual JSON payloads.
 * - Converts escaped math delimiters.
 * - Converts simple math-like inline code into KaTeX expressions.
 * - Leaves ordinary programming code unchanged.
 */
function prepareChatMarkdown(content: string): string {
  let result = content.replace(
    /(^#{1,6}\s*Visual\s*[–—-][^\n]*\n)(```(?:json)?[ \t]*\r?\n[\s\S]*?```)/gim,
    "> This visual belongs in Whiteboard mode.\n",
  );

  // Convert escaped display math into standard Markdown math.
  result = result.replace(
    /\\\[([\s\S]*?)\\\]/g,
    (_match, math: string) => `$$\n${math.trim()}\n$$`,
  );

  // Convert escaped inline math into standard Markdown math.
  result = result.replace(
    /\\\(([\s\S]*?)\\\)/g,
    (_match, math: string) => `$${math.trim()}$`,
  );

  // Repair simple mathematical expressions incorrectly wrapped in backticks.
  result = result.replace(/`([^`\n]+)`/g, (match, expression: string) => {
    const trimmed = expression.trim();

    const containsMathOperator = /[=<>+\-*/^_]/.test(trimmed);

    const containsProgrammingSyntax =
      /[(){};]|=>|==|!=|&&|\|\||\b(?:const|let|var|return|function|class|import|export|print)\b/i.test(
        trimmed,
      );

    if (!containsMathOperator || containsProgrammingSyntax) {
      return match;
    }

    let math = trimmed;

    math = math.replace(/\bFnet\b/g, "F_{net}");
    math = math.replace(/\bdvdt\b/g, "\\frac{dv}{dt}");
    math = math.replace(/\bdpdt\b/g, "\\frac{dp}{dt}");

    return `$${math}$`;
  });

  return result;
}

function App() {
  const {
    conversationId,
    setConversationId,
    conversations,
    setConversations,
    messages,
    setMessages,
    loading,
    setLoading,
    openConversation: useChatOpenConversation,
    loadConversations: useChatLoadConversations,
    deleteConversation: useChatDeleteConversation,
    sendMessage: useChatSendMessage,
  } = useChat();

  const [question, setQuestion] = useState("");
  const [darkMode, setDarkMode] = useState(false);
  const [tutorMode, setTutorMode] = useState<TutorMode>("chat");
  const [lesson, setLesson] = useState<Lesson | null>(null);

  const conversationRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);
  const questionInputRef = useRef<HTMLTextAreaElement>(null);

  // Follow new content only while the reader is already near the bottom.
  // During streaming, use instant scrolling rather than repeated smooth animations.
  useEffect(() => {
    const container = conversationRef.current;

    if (!container || !shouldAutoScrollRef.current) return;

    container.scrollTo({
      top: container.scrollHeight,
      behavior: loading ? "auto" : "smooth",
    });
  }, [messages, loading]);

  function handleConversationScroll() {
    const container = conversationRef.current;

    if (!container) return;

    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    shouldAutoScrollRef.current = distanceFromBottom < 120;
  }

  // Open a saved conversation and load its messages.
  async function openConversation(id: number) {
    if (loading) return;

    shouldAutoScrollRef.current = true;

    const success = await useChatOpenConversation(id);

    if (success) {
      setLesson(null);
      setTutorMode("chat");
      setQuestion("");
    } else {
      alert("Could not open this conversation.");
    }
  }

  // Load saved conversations and restore the last active conversation.
  useEffect(() => {
    let cancelled = false;

    async function restoreConversations() {
      try {
        const data = await useChatLoadConversations();

        if (cancelled) return;

        const savedId = localStorage.getItem(ACTIVE_CONVERSATION_KEY);

        if (!savedId) return;

        const id = Number(savedId);

        const conversationExists = data.some(
          (conversation) => conversation.id === id,
        );

        if (Number.isSafeInteger(id) && conversationExists) {
          shouldAutoScrollRef.current = true;

          if (!cancelled) {
            await useChatOpenConversation(id);
          }
        } else {
          localStorage.removeItem(ACTIVE_CONVERSATION_KEY);
        }
      } catch (error) {
        if (!cancelled) {
          console.error("Conversation loading error:", error);
        }
      }
    }

    void restoreConversations();

    return () => {
      cancelled = true;
    };
  }, []);

  // Delete a saved conversation.
  async function deleteConversation(id: number) {
    try {
      await useChatDeleteConversation(id);

      if (conversationId === id) {
        setLesson(null);
      }
    } catch (error) {
      console.error("Conversation deletion error:", error);

      alert(
        error instanceof Error
          ? error.message
          : "Could not delete conversation.",
      );
    }
  }

  // Send a normal chat message.
  // The useChat hook handles streaming, conversation creation, and persistence.
  async function sendMessage() {
    const text = question.trim();

    if (!text || loading) return;

    shouldAutoScrollRef.current = true;
    setQuestion("");

    await useChatSendMessage(text);
  }

  // Generate a structured whiteboard lesson.
  async function generateWhiteboardLesson() {
    const text = question.trim();

    if (!text || loading) return;

    setLoading(true);
    setQuestion("");

    try {
      let activeConversationId = conversationId;

      // Create a conversation if this is a new chat.
      if (activeConversationId === null) {
        const conversation = await chatApi.createConversation({
          title: text.slice(0, 60),
        });

        activeConversationId = conversation.id;

        setConversationId(activeConversationId);

        setConversations((previous) => [conversation, ...previous]);
      }

      // Remember the active conversation.
      localStorage.setItem(
        ACTIVE_CONVERSATION_KEY,
        String(activeConversationId),
      );

      // Generate and save the structured lesson.
      const response = await lessonApi.generate({
        question: text,
        difficulty: "beginner",
        conversation_id: activeConversationId,
      });

      if (!response.success || !response.lesson) {
        throw new Error(
          response.message || "TutorMe could not generate the lesson.",
        );
      }

      setLesson(response.lesson);
    } catch (error) {
      console.error("Whiteboard lesson error:", error);

      alert(
        error instanceof Error
          ? error.message
          : "Something went wrong while generating the lesson.",
      );
    } finally {
      setLoading(false);
    }
  }

  // Start a fresh chat without deleting saved conversations.
  function startNewLesson() {
    if (loading) return;

    localStorage.removeItem(ACTIVE_CONVERSATION_KEY);

    shouldAutoScrollRef.current = true;

    setMessages([]);
    setQuestion("");
    setConversationId(null);
    setLesson(null);
    setTutorMode("chat");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (tutorMode === "whiteboard") {
      void generateWhiteboardLesson();
    } else {
      void sendMessage();
    }
  }

  // Temporary Tegaki handwriting test.
  if (window.location.pathname === "/hybrid-renderer-test") {
    return <TegakiTest />;
  }
  const isWhiteboardMode = tutorMode === "whiteboard";

  return (
    <div className={`app ${darkMode ? "dark" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar-top">
          <img src="/tutorme-logo.png" alt="TutorMe" className="brand-logo" />

          <button
            type="button"
            className="new-chat-button"
            onClick={startNewLesson}
            disabled={loading}
          >
            <span aria-hidden="true">＋</span>
            <span className="new-chat-label">New chat</span>
          </button>

          <p className="section-label">LEARNING</p>

          <div className="nav-item active">
            ◈ <span>AI Tutor</span>
          </div>

          <div className="nav-item">
            ▤ <span>My subjects</span>
          </div>

          <div className="nav-item">
            ▧ <span>Study notes</span>
          </div>

          <div className="nav-item">
            ▥ <span>My progress</span>
          </div>

          <p className="section-label recent-heading">YOUR CHATS</p>

          <div className="recent-chat-list">
            {conversations.map((conversation) => (
              <div
                className={`recent-chat-item ${
                  conversation.id === conversationId ? "active" : ""
                }`}
                key={conversation.id}
              >
                <button
                  type="button"
                  className="recent-chat"
                  onClick={() => void openConversation(conversation.id)}
                  disabled={loading}
                  title={conversation.title}
                >
                  {conversation.title}
                </button>

                <button
                  type="button"
                  className="delete-chat"
                  onClick={() => void deleteConversation(conversation.id)}
                  title="Delete conversation"
                  aria-label={`Delete ${conversation.title}`}
                  disabled={loading}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="sidebar-bottom">
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setDarkMode((previous) => !previous)}
          >
            <span aria-hidden="true">{darkMode ? "☀" : "☾"}</span>
            <span>{darkMode ? "Light mode" : "Dark mode"}</span>
          </button>

          <p>Personal AI learning assistant</p>
        </div>
      </aside>

      <main className="main">
        <header className="top-header">
          <div className="header-left">
            <span className="workspace-title">TutorMe</span>
            <span className="header-divider">/</span>

            <span className="workspace-subtitle">
              {isWhiteboardMode ? "Whiteboard" : "AI Tutor"}
            </span>
          </div>

          <div className="mode-switch" aria-label="Tutor mode">
            <button
              type="button"
              className={
                tutorMode === "chat" ? "mode-button active" : "mode-button"
              }
              onClick={() => setTutorMode("chat")}
            >
              Chat
            </button>

            <button
              type="button"
              className={
                tutorMode === "whiteboard"
                  ? "mode-button active"
                  : "mode-button"
              }
              onClick={() => setTutorMode("whiteboard")}
            >
              Whiteboard
            </button>
          </div>

          <span className="status">
            <span className="status-dot" />
            {loading ? "Thinking" : "Ready"}
          </span>
        </header>

        <div
          ref={conversationRef}
          onScroll={handleConversationScroll}
          className={`conversation ${
            messages.length === 0 ? "empty" : ""
          } ${isWhiteboardMode ? "whiteboard-view" : "chat-view"}`}
        >
          {isWhiteboardMode ? (
            loading ? (
              <div className="lesson-loading">
                <div className="loading-spinner" />

                <h2>Preparing your lesson...</h2>

                <p>
                  TutorMe is planning your lesson and preparing its visual
                  steps.
                </p>

                <span>Please wait a moment.</span>
              </div>
            ) : lesson ? (
              <StructuredLessonWhiteboard lesson={lesson} />
            ) : (
              <Whiteboard onSelectTopic={(topic) => setQuestion(topic)} />
            )
          ) : messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome">
                <div className="welcome-icon">✦</div>

                <h1>What would you like to learn today?</h1>

                <p>
                  Ask me anything. I can explain concepts, solve problems, and
                  help you understand difficult topics.
                </p>

                <div className="suggestions">
                  <button
                    type="button"
                    onClick={() =>
                      setQuestion("Explain Newton's laws of motion")
                    }
                  >
                    <span className="suggestion-icon">⚛</span>

                    <span>
                      <strong>Physics</strong>
                      <small>Explore a physics concept</small>
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setQuestion("Teach me Python programming")}
                  >
                    <span className="suggestion-icon">⌘</span>

                    <span>
                      <strong>Programming</strong>
                      <small>Learn Python step by step</small>
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      setQuestion("Explain a difficult mathematics topic")
                    }
                  >
                    <span className="suggestion-icon">∑</span>

                    <span>
                      <strong>Mathematics</strong>
                      <small>Understand a difficult problem</small>
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setQuestion("Help me understand chemistry")}
                  >
                    <span className="suggestion-icon">⚗</span>

                    <span>
                      <strong>Chemistry</strong>
                      <small>Learn reactions and concepts</small>
                    </span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => {
                const isLastMessage = index === messages.length - 1;

                const isStreaming =
                  loading && isLastMessage && message.role === "assistant";

                return (
                  <article
                    className={`message ${message.role}`}
                    key={`${conversationId ?? "new"}-${index}`}
                  >
                    {message.role === "user" ? (
                      <div className="user-message-content">
                        {message.content}
                      </div>
                    ) : (
                      <>
                        <div className="assistant-avatar" aria-hidden="true">
                          ✦
                        </div>

                        <div className="assistant-message-body">
                          <div className="assistant-name">TutorMe</div>

                          <div className="message-content">
                            {message.content ? (
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[rehypeKatex]}
                                components={{
                                  code({ className, children, ...props }) {
                                    const match = /language-(\w+)/.exec(
                                      className || "",
                                    );

                                    const language = match?.[1]?.toLowerCase();

                                    // Do not send math blocks to the code highlighter.
                                    if (
                                      language === "math" ||
                                      language === "latex"
                                    ) {
                                      return (
                                        <code className={className} {...props}>
                                          {children}
                                        </code>
                                      );
                                    }

                                    // Syntax-highlight actual fenced code blocks.
                                    if (language) {
                                      return (
                                        <SyntaxHighlighter
                                          style={oneDark}
                                          language={language}
                                          PreTag="div"
                                        >
                                          {String(children).replace(/\n$/, "")}
                                        </SyntaxHighlighter>
                                      );
                                    }

                                    // Preserve ordinary inline code.
                                    return (
                                      <code className={className} {...props}>
                                        {children}
                                      </code>
                                    );
                                  },
                                }}
                              >
                                {prepareChatMarkdown(message.content)}
                              </ReactMarkdown>
                            ) : null}

                            {isStreaming && message.content.length > 0 && (
                              <span
                                className="streaming-cursor"
                                aria-hidden="true"
                              />
                            )}

                            {isStreaming && message.content.length === 0 && (
                              <span className="thinking-indicator">
                                <i />
                                <i />
                                <i />
                              </span>
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </article>
                );
              })}

              <div className="conversation-end" />
            </div>
          )}
        </div>

        <form className="input-area" onSubmit={handleSubmit}>
          <div className="input-container">
            <textarea
              ref={questionInputRef}
              className="question-input"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={
                isWhiteboardMode
                  ? "What would you like me to teach on the whiteboard?"
                  : "Message TutorMe"
              }
              rows={1}
              disabled={loading}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();

                  if (!loading && question.trim()) {
                    event.currentTarget.form?.requestSubmit();
                  }
                }
              }}
            />

            <button
              type="submit"
              className="send-button"
              disabled={loading || !question.trim()}
              aria-label={
                isWhiteboardMode ? "Generate whiteboard lesson" : "Send message"
              }
              title={isWhiteboardMode ? "Generate lesson" : "Send message"}
            >
              {loading ? (
                <span className="send-loading">···</span>
              ) : (
                <span aria-hidden="true">↑</span>
              )}
            </button>
          </div>

          <p className="input-hint">
            {isWhiteboardMode
              ? "Whiteboard mode creates a visual, step-by-step lesson."
              : "TutorMe can make mistakes. Check important information."}
          </p>
        </form>
      </main>
    </div>
  );
}

export default App;
