import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, Trash2, Mic, ArrowUp, Sparkles, MessageSquare, ChevronLeft } from 'lucide-react';
import {
  sendChatMessage,
  fetchConversations as apiFetchConversations,
  createConversation as apiCreateConversation,
  fetchConversationMessages as apiFetchConversationMessages,
  deleteConversation as apiDeleteConversation
} from '../../api/chat';
import {
  EventCard,
  EventCarouselCard,
  BookingSummaryCard,
  PaymentButton,
  TicketConfirmationCard,
  MyTicketsListCard,
  ComparisonCard,
  CancellationCard,
  EmptyStateHero
} from './ChatMessageComponents';

export default function ChatMainInterface({
  initialEvent,
  initialPrompt,
  onClearInitialPrompt,
  isSidebarOpen = true,
  onToggleSidebar,
  onOpenCreateEvent
}) {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Fetch conversations on mount
  useEffect(() => {
    fetchConversations();
  }, []);

  // Handle incoming initial prompt from Explore page
  useEffect(() => {
    if (initialPrompt) {
      sendMessage(initialPrompt);
      if (onClearInitialPrompt) onClearInitialPrompt();
    }
  }, [initialPrompt]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, toolStatus]);

  // Load messages on active conversation change
  useEffect(() => {
    if (activeConvId) {
      fetchMessages(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId]);

  const fetchConversations = async () => {
    try {
      const data = await apiFetchConversations();
      setConversations(data);
      if (data.length > 0 && !activeConvId) {
        setActiveConvId(data[0].id);
      }
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  };

  const fetchMessages = async (convId) => {
    try {
      const data = await apiFetchConversationMessages(convId);
      setMessages(data);
    } catch (err) {
      console.error('Error fetching conversation messages:', err);
    }
  };

  const createNewChat = async () => {
    try {
      const data = await apiCreateConversation('New Chat');
      setConversations(prev => [data, ...prev]);
      setActiveConvId(data.id);
      setMessages([]);
    } catch (err) {
      console.error('Error creating new chat:', err);
    }
  };

  const deleteChat = async (e, convId) => {
    e.stopPropagation();
    try {
      await apiDeleteConversation(convId);
      const updated = conversations.filter(c => c.id !== convId);
      setConversations(updated);
      if (activeConvId === convId) {
        setActiveConvId(updated.length > 0 ? updated[0].id : null);
      }
    } catch (err) {
      console.error('Error deleting chat:', err);
    }
  };

  const sendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg = { sender: 'user', text: query, type: 'text', id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    setLoading(true);

    // Dynamic subtle tool status feedback
    const qLower = query.toLowerCase();
    if (qLower.includes('book') || qLower.includes('vip') || qLower.includes('ticket')) {
      setToolStatus('Holding your tickets…');
    } else if (qLower.includes('pay') || qLower.includes('proceed') || qLower.includes('confirm')) {
      setToolStatus('Preparing payment order…');
    } else if (qLower.includes('compare')) {
      setToolStatus('Comparing event details…');
    } else if (qLower.includes('event') || qLower.includes('find') || qLower.includes('show')) {
      setToolStatus('Searching events…');
    } else {
      setToolStatus('Thinking…');
    }

    try {
      const res = await sendChatMessage({
        message: query,
        conversation_id: activeConvId
      });

      if (!activeConvId && res.conversation_id) {
        setActiveConvId(res.conversation_id);
        fetchConversations();
      }

      const botMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: res.reply || res.message,
        type: res.type || 'text',
        payload: res.payload,
        ui: res.ui,
        state: res.state
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: "I couldn't complete that request right now. Let me know if you'd like to try again or explore upcoming events.",
        type: 'text'
      }]);
    } finally {
      setLoading(false);
      setToolStatus(null);
    }
  };

  const handlePaymentSuccess = async (ticket) => {
    setLoading(true);
    setToolStatus('Verifying payment…');
    try {
      const res = await sendChatMessage({
        event_type: 'system_event',
        payload: {
          event: 'PAYMENT_VERIFIED',
          ticket: ticket
        },
        conversation_id: activeConvId
      });

      const botMsg = {
        id: Date.now(),
        sender: 'assistant',
        text: res.reply || res.message || 'Payment confirmed ✓ Your tickets are ready.',
        type: 'ticket_confirmation',
        payload: ticket || res.payload
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error('Payment notice error:', err);
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        text: 'Payment confirmed ✓ Your tickets are ready.',
        type: 'ticket_confirmation',
        payload: ticket
      }]);
    } finally {
      setLoading(false);
      setToolStatus(null);
    }
  };

  const handleSpeechInput = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    setIsListening(true);
    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setIsListening(false);
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleTextareaInput = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const renderMessageCard = (msg) => {
    // 1. Check structured UI array from backend
    if (msg.ui && Array.isArray(msg.ui) && msg.ui.length > 0) {
      return msg.ui.map((component, idx) => {
        const { type, data } = component;
        if (type === 'event_carousel' || type === 'event_results') {
          return <EventCarouselCard key={idx} events={data.events || []} onSelect={sendMessage} />;
        }
        if (type === 'booking_summary') {
          return <BookingSummaryCard key={idx} {...data} onConfirm={sendMessage} onSelect={sendMessage} />;
        }
        if (type === 'payment_button') {
          return <PaymentButton key={idx} {...data} onPaymentSuccess={handlePaymentSuccess} />;
        }
        if (type === 'ticket_confirmation') {
          return <TicketConfirmationCard key={idx} {...data} />;
        }
        if (type === 'my_tickets_list') {
          return <MyTicketsListCard key={idx} tickets={data.tickets || []} onSelect={sendMessage} />;
        }
        if (type === 'comparison_card') {
          return <ComparisonCard key={idx} {...data} onSelect={sendMessage} />;
        }
        if (type === 'cancellation_card') {
          return <CancellationCard key={idx} {...data} onConfirmCancel={sendMessage} />;
        }
        return null;
      });
    }

    // 2. Backward compatibility fallback
    if (msg.type === 'event_results' && msg.payload?.events) {
      return <EventCarouselCard events={msg.payload.events} onSelect={sendMessage} />;
    }
    if (msg.type === 'booking_summary' && msg.payload) {
      return <BookingSummaryCard {...msg.payload} onConfirm={sendMessage} onSelect={sendMessage} />;
    }
    if (msg.type === 'payment_button' && msg.payload) {
      return <PaymentButton {...msg.payload} onPaymentSuccess={handlePaymentSuccess} />;
    }
    if (msg.type === 'ticket_confirmation' && msg.payload) {
      return <TicketConfirmationCard {...msg.payload} />;
    }
    if (msg.type === 'my_tickets_list' && msg.payload?.tickets) {
      return <MyTicketsListCard tickets={msg.payload.tickets} onSelect={sendMessage} />;
    }
    if (msg.type === 'comparison_card' && msg.payload) {
      return <ComparisonCard {...msg.payload} onSelect={sendMessage} />;
    }
    if (msg.type === 'cancellation_card' && msg.payload) {
      return <CancellationCard {...msg.payload} onConfirmCancel={sendMessage} />;
    }

    return null;
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 60px)', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {/* 1. Slim Collapsible Sidebar */}
      {isSidebarOpen && (
        <aside
          style={{
            width: '260px',
            background: 'var(--bg-surface)',
            borderRight: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            padding: '16px 12px',
            flexShrink: 0,
            transition: 'width 200ms ease',
          }}
        >
          {/* New Chat Button */}
          <div>
            <button
              onClick={createNewChat}
              style={{
                width: '100%',
                background: 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-btn)',
                color: 'var(--text-primary)',
                padding: '9px 14px',
                fontWeight: 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '16px',
              }}
              onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.04)'}
              onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={16} /> New chat
              </span>
            </button>

            {/* Conversation History List */}
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0 8px 6px' }}>
              Recent Chats
            </div>

            <div style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 220px)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {conversations.map((conv) => {
                const isActive = conv.id === activeConvId;
                return (
                  <div
                    key={conv.id}
                    onClick={() => setActiveConvId(conv.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-btn)',
                      background: isActive ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                      color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                      cursor: 'pointer',
                      fontSize: '0.82rem',
                    }}
                    onMouseOver={(e) => !isActive && (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')}
                    onMouseOut={(e) => !isActive && (e.currentTarget.style.background = 'transparent')}
                  >
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '170px' }}>
                      {conv.title || 'Chat'}
                    </span>
                    <button
                      onClick={(e) => deleteChat(e, conv.id)}
                      title="Delete chat"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '2px',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                      onMouseOver={(e) => e.currentTarget.style.color = 'var(--danger)'}
                      onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bottom Sidebar Footnote */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px', paddingLeft: '4px', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            ✦ ChatAssist v2.0
          </div>
        </aside>
      )}

      {/* 2. Main Conversation Stream Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', position: 'relative', overflow: 'hidden' }}>
        {/* Message Stream */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 20px 140px' }}>
          <div style={{ maxWidth: '768px', margin: '0 auto', width: '100%' }}>
            {/* Empty State Hero */}
            {messages.length === 0 && (
              <EmptyStateHero onQuickAction={sendMessage} />
            )}

            {/* Message History */}
            {messages.map((msg, index) => {
              const isUser = msg.sender === 'user';
              return (
                <div
                  key={msg.id || index}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start',
                    marginBottom: '20px',
                    animation: 'fadeIn 180ms ease-out forwards',
                  }}
                >
                  {/* Sender Header */}
                  {!isUser && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                      <span style={{ color: 'var(--accent)' }}>✦</span>
                      <span>ChatAssist</span>
                    </div>
                  )}

                  {/* Text Content */}
                  <div
                    style={{
                      background: isUser ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                      color: 'var(--text-primary)',
                      padding: isUser ? '10px 16px' : '2px 0',
                      borderRadius: isUser ? '18px 18px 4px 18px' : '0',
                      maxWidth: '85%',
                      fontSize: '0.94rem',
                      lineHeight: 1.6,
                      wordBreak: 'break-word',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {msg.text}
                  </div>

                  {/* Single Purpose UI Card */}
                  {!isUser && renderMessageCard(msg)}
                </div>
              );
            })}

            {/* Subtle Thinking & Tool Activity Indicator */}
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '0.84rem', marginTop: '10px' }}>
                <span style={{ color: 'var(--accent)', animation: 'pulseSubtle 1.2s infinite' }}>✦</span>
                <span style={{ fontStyle: 'italic' }}>{toolStatus || 'Thinking…'}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 3. Universal Centered Floating Bottom Composer */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: 'linear-gradient(to top, var(--bg-primary) 70%, transparent)',
            padding: '20px 20px 24px',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              maxWidth: '768px',
              width: '100%',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-composer)',
              padding: '6px 10px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
              transition: 'border-color 150ms ease',
            }}
            onFocus={() => {}}
          >
            {/* Attachment Button */}
            <button
              title="Add attachment"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              onMouseOver={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
              onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
            >
              <Plus size={18} />
            </button>

            {/* Natural Textarea Composer */}
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask ChatAssist anything about events, tickets, or bookings..."
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.94rem',
                resize: 'none',
                padding: '8px 4px',
                maxHeight: '120px',
                lineHeight: 1.4,
              }}
            />

            {/* Voice Input Mic */}
            <button
              onClick={handleSpeechInput}
              title={isListening ? 'Listening...' : 'Use voice input'}
              style={{
                background: isListening ? 'var(--danger-soft)' : 'transparent',
                border: 'none',
                color: isListening ? 'var(--danger)' : 'var(--text-muted)',
                cursor: 'pointer',
                padding: '8px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              onMouseOver={(e) => !isListening && (e.currentTarget.style.color = 'var(--text-primary)')}
              onMouseOut={(e) => !isListening && (e.currentTarget.style.color = 'var(--text-muted)')}
            >
              <Mic size={18} />
            </button>

            {/* Circular Send Button */}
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                background: input.trim() && !loading ? 'var(--text-primary)' : 'rgba(255,255,255,0.08)',
                color: input.trim() && !loading ? '#111111' : 'var(--text-muted)',
                border: 'none',
                cursor: input.trim() && !loading ? 'pointer' : 'default',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 150ms ease',
              }}
            >
              <ArrowUp size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
