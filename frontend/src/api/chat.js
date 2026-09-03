import axios from 'axios';

const BASE_URL = '/api/v1';

/**
 * Send a chat message to the ChatAssist AI agent.
 * @param {Object} payload - { message, conversation_id, event_type, payload }
 * @returns {Promise<Object>} ChatResponse containing reply, ui components, and state.
 */
export async function sendChatMessage({ message, conversation_id, event_type = 'user_message', payload = null }) {
  const response = await axios.post(`${BASE_URL}/chat`, {
    message,
    conversation_id,
    event_type,
    payload
  });
  return response.data;
}

/**
 * Fetch all chat conversations for the current user.
 * @returns {Promise<Array>} List of conversation sessions.
 */
export async function fetchConversations() {
  const response = await axios.get(`${BASE_URL}/chat/conversations`);
  return response.data;
}

/**
 * Create a new conversation session.
 * @param {string} title
 * @returns {Promise<Object>} Created conversation session.
 */
export async function createConversation(title = 'New Chat') {
  const response = await axios.post(`${BASE_URL}/chat/conversations`, null, {
    params: { title }
  });
  return response.data;
}

/**
 * Fetch message history for a specific conversation.
 * @param {number} conversationId
 * @returns {Promise<Array>} List of historical messages.
 */
export async function fetchConversationMessages(conversationId) {
  const response = await axios.get(`${BASE_URL}/chat/conversations/${conversationId}/messages`);
  return response.data;
}

/**
 * Delete a conversation.
 * @param {number} conversationId
 * @returns {Promise<Object>}
 */
export async function deleteConversation(conversationId) {
  const response = await axios.delete(`${BASE_URL}/chat/conversations/${conversationId}`);
  return response.data;
}
