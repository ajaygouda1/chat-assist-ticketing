import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, Plus, Trash2, MessageSquare, Sparkles, ShieldCheck, Calendar, MapPin, Ticket, Mic, X, ChevronRight, RefreshCw } from 'lucide-react';
import axios from 'axios';
import {
  EventCard,
  BookingSummaryCard,
  PaymentButton,
  TicketConfirmationCard,
  QuickReplyButtons,
  EventCarouselCard,
  WelcomeScreenCard,
  MyTicketsListCard,
  CancellationCard,
  CreateEventEntryCard
} from './ChatMessageComponents';

export default function ChatMainInterface({ initialEvent, onSelectEventForBooking, onOpenCreateWizard }) {

  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [contextEvent, setContextEvent] = useState(initialEvent || null);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);

  // Load user conversation sessions on mount
  useEffect(() => {
    fetchConversations();
  }, []);

  // Handle initial event passed from Explore view
  useEffect(() => {
    if (initialEvent) {
      setContextEvent(initialEvent);
      sendMessage(`Book tickets for ${initialEvent.title || initialEvent.event_title}`);
    }
  }, [initialEvent]);

  // Scroll to bottom whenever messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Load messages when active conversation changes
  useEffect(() => {
    if (activeConvId) {
      fetchMessages(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId]);

  const fetchConversations = async () => {
    try {
      const res = await axios.get('/api/v1/chat/conversations');
      setConversations(res.data);
      if (res.data.length > 0 && !activeConvId) {
        setActiveConvId(res.data[0].id);
      }
    } catch (err) {
      console.error("Error fetching conversations", err);
    }
  };

  const fetchMessages = async (convId) => {
    try {
      const res = await axios.get(`/api/v1/chat/conversations/${convId}/messages`);
      setMessages(res.data);
    } catch (err) {
      console.error("Error fetching conversation messages", err);
    }
  };

  const createNewChat = async () => {
    try {
      const res = await axios.post('/api/v1/chat/conversations', { title: 'New Chat' });
      setConversations(prev => [res.data, ...prev]);
      setActiveConvId(res.data.id);
      setMessages([]);
      setContextEvent(null);
    } catch (err) {
      console.error("Error creating new chat", err);
    }
  };

  const deleteChat = async (e, convId) => {
    e.stopPropagation();
    try {
      await axios.delete(`/api/v1/chat/conversations/${convId}`);
      const updated = conversations.filter(c => c.id !== convId);
      setConversations(updated);
      if (activeConvId === convId) {
        setActiveConvId(updated.length > 0 ? updated[0].id : null);
      }
    } catch (err) {
      console.error("Error deleting conversation", err);
    }
  };

  const sendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg = { sender: 'user', text: query, type: 'text', id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res = await axios.post('/api/v1/chat', {
        message: query,
        conversation_id: activeConvId
      });

      if (!activeConvId && res.data.conversation_id) {
        setActiveConvId(res.data.conversation_id);
        fetchConversations();
      }

      const botMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: res.data.reply,
        intent: res.data.intent,
        confidence: res.data.confidence,
        routed_to: res.data.routed_to,
        grounding_status: res.data.grounding_status,
        type: res.data.type || 'text',
        payload: res.data.payload,
        quick_replies: res.data.quick_replies
      };

      setMessages(prev => [...prev, botMsg]);

      // Update contextual right drawer if payload contains event details
      if (res.data.payload && (res.data.payload.id || res.data.payload.event_id)) {
        setContextEvent(res.data.payload);
      }
    } catch (err) {
      console.error("Chat error", err);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: 'I am currently processing requests offline. You can ask me to search events or view booked tickets.',
        type: 'text'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = async (ticket) => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/chat', {
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
        text: res.data.reply || '🎉 Payment successful! Your ticket has been issued.',
        type: 'ticket_confirmation',
        payload: ticket || res.data.payload,
        quick_replies: res.data.quick_replies
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error("Payment system event notice:", err);
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'assistant',
        text: '🎉 Payment successful! Your ticket has been issued.',
        type: 'ticket_confirmation',
        payload: ticket
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeechInput = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert("Speech recognition is not supported in this browser.");
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

  const activeMsgType = messages.length > 0 ? messages[messages.length - 1].type : null;

  return (
    <div style={{
      display: 'flex',
      height: 'calc(100vh - 72px)',
      background: 'var(--bg-dark)',
      color: '#F8FAFC',
      overflow: 'hidden'
    }}>
      {/* LEFT SIDEBAR: Conversation Session History */}
      <aside style={{
        width: '260px',
        background: 'rgba(15, 23, 42, 0.95)',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px 12px'
      }}>
        <button
          onClick={createNewChat}
          style={{
            width: '100%',
            background: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
            border: 'none',
            color: 'white',
            padding: '10px 14px',
            borderRadius: '12px',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 4px 16px rgba(139, 92, 246, 0.3)',
            marginBottom: '16px'
          }}
        >
          <Plus size={18} /> New Conversation
        </button>

        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', padding: '0 8px 8px 8px', letterSpacing: '0.5px' }}>
          Recent Conversations
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {conversations.length === 0 ? (
            <div style={{ fontSize: '0.78rem', color: '#64748B', padding: '12px 8px', textAlign: 'center' }}>
              No past conversations
            </div>
          ) : (
            conversations.map(c => (
              <div
                key={c.id}
                onClick={() => setActiveConvId(c.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  background: activeConvId === c.id ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                  border: activeConvId === c.id ? '1px solid rgba(139, 92, 246, 0.4)' : '1px solid transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                  <MessageSquare size={15} color={activeConvId === c.id ? '#A78BFA' : '#64748B'} />
                  <span style={{
                    fontSize: '0.82rem',
                    color: activeConvId === c.id ? '#F1F5F9' : '#94A3B8',
                    fontWeight: activeConvId === c.id ? 600 : 400,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {c.title}
                  </span>
                </div>
                <button
                  onClick={(e) => deleteChat(e, c.id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#64748B',
                    cursor: 'pointer',
                    padding: '2px'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.color = '#EF4444'}
                  onMouseOut={(e) => e.currentTarget.style.color = '#64748B'}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* CENTER: Main Chat Screen */}
      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        background: 'radial-gradient(circle at 50% 0%, rgba(139, 92, 246, 0.08) 0%, transparent 60%)'
      }}>
        {/* Chat Stream Header */}
        <div style={{
          padding: '14px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ background: 'linear-gradient(135deg, #8B5CF6, #EC4899)', padding: '8px', borderRadius: '10px' }}>
              <Bot size={20} color="white" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: 'white' }}>
                🤖 ChatAssist
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 600 }}>
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }}></span> Live data
              </span>
            </div>
          </div>

          {/* Stepper Progress Indicator */}
          {(() => {
            const lastMsg = (messages && messages.length > 0) ? messages[messages.length - 1] : null;
            const currentMode = lastMsg?.mode || 'BOOKING';
            const activeMsgType = lastMsg?.type || null;

            if (currentMode === 'EVENT_CREATION' || activeMsgType === 'event_creation_card') {
              const creationSteps = [
                { title: 'Create Event', idx: 1 },
                { title: 'Details', idx: 2 },
                { title: 'Tickets', idx: 3 },
                { title: 'Preview', idx: 4 },
                { title: 'Publish', idx: 5 }
              ];
              return (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.72rem', fontWeight: 700 }}>
                  {creationSteps.map((st, i) => (
                    <React.Fragment key={st.title}>
                      {i > 0 && <span style={{ color: '#475569' }}>›</span>}
                      <span style={{ color: i === 0 ? '#10B981' : '#64748B', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <span style={{ fontWeight: 800 }}>{i === 0 ? '●' : '○'}</span> {st.title}
                      </span>
                    </React.Fragment>
                  ))}
                </div>
              );
            }

            let activeStep = 0;
            if (activeMsgType === 'event_card' || activeMsgType === 'event_results') activeStep = 1;
            else if (activeMsgType === 'booking_summary') activeStep = 3;
            else if (activeMsgType === 'payment_button') activeStep = 4;
            else if (activeMsgType === 'ticket_confirmation') activeStep = 5;

            const steps = [
              { title: 'Event', idx: 1 },
              { title: 'Tickets', idx: 2 },
              { title: 'Review', idx: 3 },
              { title: 'Payment', idx: 4 },
              { title: 'Confirmed', idx: 5 }
            ];

            return (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.72rem', fontWeight: 700 }}>
                {steps.map((st, i) => {
                  const isDone = activeStep > st.idx;
                  const isCurrent = activeStep === st.idx || (activeStep === 0 && st.idx === 1 && messages.length > 0);
                  const symbol = isDone ? '✓' : isCurrent ? '●' : '○';
                  const textColor = isDone ? '#10B981' : isCurrent ? '#A78BFA' : '#64748B';

                  return (
                    <React.Fragment key={st.title}>
                      {i > 0 && <span style={{ color: '#475569' }}>›</span>}
                      <span style={{ color: textColor, display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <span style={{ fontWeight: 800 }}>{symbol}</span> {st.title}
                      </span>
                    </React.Fragment>
                  );
                })}
              </div>
            );
          })()}
        </div>

        {/* Message Stream */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {messages.length === 0 ? (
              <WelcomeScreenCard onQuickAction={(promptText) => sendMessage(promptText)} />
            ) : (
              messages.map(m => (
                <div
                  key={m.id}
                  style={{
                    display: 'flex',
                    justifyContent: m.sender === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: '8px'
                  }}
                >
                  <div style={{
                    maxWidth: m.sender === 'user' ? '60%' : (m.type && m.type !== 'text' ? '900px' : '75%'),
                    minWidth: m.type && m.type !== 'text' ? '360px' : 'auto'
                  }}>
                    {/* User Bubble */}
                    {m.sender === 'user' ? (
                      <div style={{
                        background: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
                        color: 'white',
                        padding: '14px 20px',
                        borderRadius: '20px 20px 4px 20px',
                        fontSize: '0.95rem',
                        fontWeight: 500,
                        boxShadow: '0 4px 14px rgba(139, 92, 246, 0.3)'
                      }}>
                        {m.text}
                      </div>
                    ) : (
                      /* Bot Bubble */
                      <div style={{
                        background: 'rgba(30, 41, 59, 0.85)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        color: '#F8FAFC',
                        padding: '20px',
                        borderRadius: '20px 20px 20px 4px',
                        backdropFilter: 'blur(10px)',
                        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)'
                      }}>
                        {m.text && (
                          <p style={{ margin: '0 0 10px 0', fontSize: '0.95rem', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                            {m.text}
                          </p>
                        )}

                        {/* Render Structured Response Cards */}
                        {(m.type === 'create_event_entry' || m.type === 'CREATE_EVENT_ACTION') && (
                          <CreateEventEntryCard {...(m.payload || {})} onStartSetup={(initialData) => onOpenCreateWizard && onOpenCreateWizard(initialData)} />
                        )}

                        {(m.type === 'event_card' || m.type === 'EVENT_DETAILS') && m.payload && (
                          <EventCard {...m.payload} onSelect={(t) => sendMessage(t)} />
                        )}

                        {(m.type === 'event_results' || m.type === 'EVENT_RESULTS') && m.payload?.events && (
                          <EventCarouselCard events={m.payload.events} onSelectEvent={(t) => sendMessage(t)} />
                        )}

                        {(m.type === 'booking_summary' || m.type === 'BOOKING_SUMMARY') && m.payload && (
                          <BookingSummaryCard
                            {...m.payload}
                            onConfirm={(t) => sendMessage(t)}
                            onCancel={(t) => sendMessage(t)}
                            onSelect={(t) => sendMessage(t)}
                          />
                        )}

                        {(m.type === 'payment_button' || m.type === 'PAYMENT_ACTION') && m.payload && (
                          <PaymentButton
                            {...m.payload}
                            onPaymentSuccess={handlePaymentSuccess}
                          />
                        )}

                        {(m.type === 'ticket_confirmation' || m.type === 'TICKET_CONFIRMATION') && m.payload && (
                          <TicketConfirmationCard {...m.payload} />
                        )}

                        {(m.type === 'my_tickets_list' || m.type === 'MY_TICKETS') && m.payload?.tickets && (
                          <MyTicketsListCard tickets={m.payload.tickets} />
                        )}

                        {(m.type === 'cancellation_card' || m.type === 'REFUND_ACTION') && m.payload && (
                          <CancellationCard {...m.payload} onConfirmCancel={(t) => sendMessage(t)} />
                        )}

                        <QuickReplyButtons quick_replies={m.quick_replies} onSelect={(t) => sendMessage(t)} />
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Typing Indicator */}
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#A78BFA', fontSize: '0.85rem', padding: '8px 12px' }}>
                <RefreshCw size={16} className="animate-spin" /> ChatAssist is processing...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Bar */}
        <div style={{
          padding: '18px 24px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(15, 23, 42, 0.9)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
            {/* Quick Action Pills */}
            <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '12px' }}>
              {['Show live events', 'Book VIP passes', '✨ Create an event', 'Show my tickets', 'How does refund work?'].map((pill, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(pill)}
                  style={{
                    background: 'rgba(139, 92, 246, 0.12)',
                    border: '1px solid rgba(139, 92, 246, 0.35)',
                    color: '#C4B5FD',
                    padding: '6px 14px',
                    borderRadius: '16px',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    minHeight: '34px'
                  }}
                >
                  {pill}
                </button>
              ))}
            </div>

            <form
              onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
              style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
            >
              <button
                type="button"
                onClick={handleSpeechInput}
                style={{
                  background: isListening ? '#EF4444' : 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: isListening ? 'white' : '#94A3B8',
                  padding: '12px',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: '48px',
                  minWidth: '48px'
                }}
                title="Voice Input"
              >
                <Mic size={20} />
              </button>

              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask ChatAssist to search events, book tickets, or show passes..."
                style={{
                  flex: 1,
                  background: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid rgba(139, 92, 246, 0.3)',
                  minHeight: '48px',
                  padding: '12px 18px',
                  fontSize: '0.95rem',
                  borderRadius: '12px',
                  color: 'white',
                  outline: 'none'
                }}
              />

              <button
                type="submit"
                disabled={!input.trim() || loading}
                style={{
                  background: 'linear-gradient(135deg, #8B5CF6, #6366F1)',
                  border: 'none',
                  color: 'white',
                  padding: '12px 20px',
                  borderRadius: '12px',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  minHeight: '48px',
                  cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  opacity: input.trim() && !loading ? 1 : 0.5
                }}
              >
                <Send size={16} /> Send
              </button>

            </form>
          </div>
        </div>
      </main>


      {/* RIGHT PANEL: Contextual Active Event / Ticket Preview Panel (Desktop) */}
      {contextEvent && (
        <aside style={{
          width: '300px',
          background: 'rgba(15, 23, 42, 0.95)',
          borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 700, margin: 0, color: '#A78BFA' }}>
              Active Context
            </h4>
            <button
              onClick={() => setContextEvent(null)}
              style={{ background: 'transparent', border: 'none', color: '#64748B', cursor: 'pointer' }}
            >
              <X size={16} />
            </button>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.6)', padding: '14px', borderRadius: '12px', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 8px 0', color: 'white' }}>
              {contextEvent.event_title || contextEvent.title || 'Selected Event'}
            </h3>
            <div style={{ fontSize: '0.78rem', color: '#94A3B8', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span>📍 {contextEvent.location || 'Bengaluru'}</span>
              <span>📅 {contextEvent.date_str || 'Upcoming'}</span>
              {contextEvent.price && <span>💰 Standard Pass: ₹{contextEvent.price}</span>}
              {contextEvent.available_tickets && <span>🎟️ {contextEvent.available_tickets} seats remaining</span>}
            </div>

            <button
              onClick={() => sendMessage(`Book tickets for ${contextEvent.event_title || contextEvent.title}`)}
              style={{
                width: '100%',
                marginTop: '14px',
                background: 'linear-gradient(135deg, #10B981, #059669)',
                border: 'none',
                color: 'white',
                padding: '8px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              Book This Event Now
            </button>
          </div>
        </aside>
      )}
    </div>
  );
}

