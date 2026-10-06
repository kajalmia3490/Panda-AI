let ws;
let isConnected = false;
let currentAgentMessageDiv = null;

let isVoiceMuted = false;
let recognition = null;
let isRecognizing = false;
let isSpeaking = false;
let silenceTimer = null;
const SILENCE_TIMEOUT_MS = 3000; // 3 seconds silence threshold

const messagesContainer = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelSelect = document.getElementById('model-select');
const conversationHistoryList = document.getElementById('conversation-history-list');
const statusBadge = document.getElementById('status-badge');
const micBtn = document.getElementById('mic-btn');
const voiceStatusText = document.getElementById('voice-status-text');
const voiceMuteBtn = document.getElementById('voice-mute-btn');

function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/agent`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    isConnected = true;
    updateStatus('Online', true);
  };

  ws.onclose = () => {
    isConnected = false;
    updateStatus('Disconnected', false);
    setTimeout(initWebSocket, 3000);
  };

  ws.onerror = (err) => {
    console.error('WS Error:', err);
    updateStatus('Error', false);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleAgentEvent(data);
  };
}

function updateStatus(text, ok) {
  const dot = statusBadge.querySelector('.status-dot');
  const span = statusBadge.querySelector('span');
  if (span) span.textContent = text;
  if (dot) {
    dot.style.background = ok ? 'var(--accent-emerald)' : 'var(--accent-rose)';
    dot.style.boxShadow = ok ? '0 0 8px var(--accent-emerald)' : '0 0 8px var(--accent-rose)';
  }
}

function handleAgentEvent(event) {
  switch (event.type) {
    case 'connected':
      if (modelSelect && event.model) {
        modelSelect.value = event.model;
      }
      break;

    case 'start':
      prepareAgentResponseContainer();
      setAgentWorking(true);
      break;

    case 'tool_call':
      appendToolCall(event.tool, event.args);
      break;

    case 'tool_result':
      appendToolResult(event.tool, event.result);
      // If a write_file or command happened, refresh workspace files
      if (event.tool === 'write_file' || event.tool === 'run_command') {
        refreshFiles();
      }
      break;

    case 'thought_or_text':
      updateAgentResponseText(event.text);
      break;

    case 'done':
      if (event.final_text) {
        updateAgentResponseText(event.final_text);
        speakText(event.final_text);
        recordMessageToHistory('agent', event.final_text);
      }
      setAgentWorking(false);
      currentAgentMessageDiv = null;
      break;

    case 'error':
      appendErrorMessage(event.message);
      setAgentWorking(false);
      currentAgentMessageDiv = null;
      break;

    case 'info':
      appendSystemNotice(event.message);
      break;
  }
}

function prepareAgentResponseContainer() {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-wrapper agent';

  const header = document.createElement('div');
  header.className = 'msg-header';
  header.innerHTML = `<span>🐼 Panda</span> • <span>${new Date().toLocaleTimeString()}</span>`;

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';

  const streamArea = document.createElement('div');
  streamArea.className = 'agent-stream-area';
  bubble.appendChild(streamArea);

  wrapper.appendChild(header);
  wrapper.appendChild(bubble);

  messagesContainer.appendChild(wrapper);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  currentAgentMessageDiv = bubble;
}

function updateAgentResponseText(markdownText) {
  if (!currentAgentMessageDiv) prepareAgentResponseContainer();
  let textNode = currentAgentMessageDiv.querySelector('.markdown-body');
  if (!textNode) {
    textNode = document.createElement('div');
    textNode.className = 'markdown-body';
    currentAgentMessageDiv.appendChild(textNode);
  }
  // Parse markdown with marked library
  if (window.marked) {
    textNode.innerHTML = marked.parse(markdownText);
  } else {
    textNode.textContent = markdownText;
  }
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendToolCall(toolName, args) {
  if (!currentAgentMessageDiv) prepareAgentResponseContainer();
  const streamArea = currentAgentMessageDiv.querySelector('.agent-stream-area');

  const pill = document.createElement('div');
  pill.className = 'tool-pill';

  let icon = '⚡';
  if (toolName === 'list_files') icon = '📂';
  if (toolName === 'read_file') icon = '📖';
  if (toolName === 'write_file') icon = '✍️';
  if (toolName === 'run_command') icon = '💻';
  if (toolName === 'search_in_files') icon = '🔍';
  if (toolName === 'launch_application') icon = '🚀';
  if (toolName === 'close_process') icon = '🛑';
  if (toolName === 'open_url_in_browser') icon = '🌐';
  if (toolName === 'get_system_status') icon = '📊';
  if (toolName === 'control_volume') icon = '🔊';
  if (toolName === 'windows_power_control') icon = '🔌';
  if (toolName === 'install_windows_app') icon = '📦';
  if (toolName === 'move_and_click_mouse') icon = '🖱️';
  if (toolName === 'keyboard_type_and_press') icon = '⌨️';

  const argsSummary = Object.entries(args || {})
    .map(([k, v]) => {
      const valStr = typeof v === 'string' && v.length > 50 ? v.slice(0, 50) + '...' : JSON.stringify(v);
      return `<span style="color:var(--text-dim);">${k}:</span> ${valStr}`;
    })
    .join('  ');

  pill.innerHTML = `
    <div class="tool-icon">${icon}</div>
    <div class="tool-details">
      <div class="tool-name">Tool: ${toolName}</div>
      <div style="font-size:0.75rem; color:var(--text-muted);">${argsSummary || '(no arguments)'}</div>
    </div>
  `;

  streamArea.appendChild(pill);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendToolResult(toolName, result) {
  if (!currentAgentMessageDiv) return;
  const streamArea = currentAgentMessageDiv.querySelector('.agent-stream-area');

  const pill = document.createElement('div');
  pill.className = 'tool-pill result';

  const preview = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
  const truncated = preview.length > 300 ? preview.slice(0, 300) + `\n... (+${preview.length - 300} more chars)` : preview;

  pill.innerHTML = `
    <div class="tool-icon">✓</div>
    <div class="tool-details">
      <div class="tool-name" style="color:var(--accent-emerald);">Result: ${toolName}</div>
      <div class="tool-output">${escapeHtml(truncated)}</div>
    </div>
  `;

  streamArea.appendChild(pill);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendUserMessage(text, record = true) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-wrapper user';

  const header = document.createElement('div');
  header.className = 'msg-header';
  header.style.justifyContent = 'flex-end';
  header.innerHTML = `<span>You</span> • <span>${new Date().toLocaleTimeString()}</span>`;

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.textContent = text;

  wrapper.appendChild(header);
  wrapper.appendChild(bubble);

  messagesContainer.appendChild(wrapper);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  if (record) {
    recordMessageToHistory('user', text);
  }
}

function appendErrorMessage(msg) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-wrapper agent';
  wrapper.innerHTML = `
    <div class="msg-bubble" style="border-left: 3px solid var(--accent-rose); background: rgba(244, 63, 94, 0.1);">
      <div style="color:var(--accent-rose); font-weight:600; margin-bottom:4px;">Execution Error</div>
      <div style="font-size:0.85rem; color:var(--text-muted);">${escapeHtml(msg)}</div>
    </div>
  `;
  messagesContainer.appendChild(wrapper);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendSystemNotice(text) {
  const note = document.createElement('div');
  note.style.textAlign = 'center';
  note.style.fontSize = '0.75rem';
  note.style.color = 'var(--text-dim)';
  note.style.padding = '8px 0';
  note.textContent = text;
  messagesContainer.appendChild(note);
}

function sendMessage() {
  const text = userInput.value.trim();
  if (!text || !isConnected) return;

  appendUserMessage(text);
  userInput.value = '';

  ws.send(JSON.stringify({
    action: 'chat',
    prompt: text,
    model: modelSelect.value
  }));
}

function setAgentWorking(working) {
  sendBtn.disabled = working;
  userInput.disabled = working;
  if (working) {
    sendBtn.innerHTML = 'Thinking...';
  } else {
    sendBtn.innerHTML = 'Send <span>↵</span>';
    userInput.focus();
  }
}

let sessions = JSON.parse(localStorage.getItem('panda_sessions') || '[]');
let currentSessionId = localStorage.getItem('panda_active_session') || null;

function renderConversationHistory() {
  if (!conversationHistoryList) return;
  conversationHistoryList.innerHTML = '';

  if (sessions.length === 0) {
    conversationHistoryList.innerHTML = '<div style="padding:12px 8px; color:var(--text-dim); font-size:0.8rem; text-align:center;">কোনো পূর্ববর্তী রেকর্ড নেই</div>';
    return;
  }

  sessions.slice().reverse().forEach((session) => {
    const item = document.createElement('div');
    item.className = 'history-item' + (session.id === currentSessionId ? ' active' : '');
    
    item.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
        <div class="history-title" style="flex:1;">${escapeHtml(session.title || 'নতুন কথোপকথন')}</div>
        <button class="delete-history-btn" title="মুছে ফেলুন (Delete)" onclick="event.stopPropagation(); deleteSession('${session.id}')">🗑️</button>
      </div>
      <div class="history-meta">
        <span>${session.time || ''}</span>
        <span>${session.messages ? session.messages.length + ' টি বার্তা' : ''}</span>
      </div>
    `;

    item.onclick = () => loadSession(session.id);
    conversationHistoryList.appendChild(item);
  });
}

function deleteSession(id) {
  if (confirm('এই কথোপকথন রেকর্ডটি মুছে ফেলতে চান?')) {
    sessions = sessions.filter(s => s.id !== id);
    localStorage.setItem('panda_sessions', JSON.stringify(sessions));
    if (currentSessionId === id) {
      createNewChatSession();
    } else {
      renderConversationHistory();
    }
  }
}

function clearAllConversations() {
  if (confirm('সবগুলো কথোপকথন রেকর্ড মুছে ফেলতে চান?')) {
    sessions = [];
    localStorage.removeItem('panda_sessions');
    createNewChatSession();
  }
}

function recordMessageToHistory(role, text) {
  if (!currentSessionId) {
    currentSessionId = 'sess_' + Date.now();
    localStorage.setItem('panda_active_session', currentSessionId);
    sessions.push({
      id: currentSessionId,
      title: text.substring(0, 35) + (text.length > 35 ? '...' : ''),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      messages: []
    });
  }

  const session = sessions.find(s => s.id === currentSessionId);
  if (session) {
    session.messages.push({ role, text, time: new Date().toLocaleTimeString() });
    if (session.messages.length === 1 && role === 'user') {
      session.title = text.substring(0, 35) + (text.length > 35 ? '...' : '');
    }
    localStorage.setItem('panda_sessions', JSON.stringify(sessions));
    renderConversationHistory();
  }
}

function loadSession(id) {
  const session = sessions.find(s => s.id === id);
  if (!session) return;

  currentSessionId = id;
  localStorage.setItem('panda_active_session', id);
  messagesContainer.innerHTML = '';

  (session.messages || []).forEach(msg => {
    if (msg.role === 'user') {
      appendUserMessage(msg.text, false);
    } else {
      prepareAgentResponseContainer();
      updateAgentResponseText(msg.text);
      currentAgentMessageDiv = null;
    }
  });

  renderConversationHistory();
}

function createNewChatSession() {
  currentSessionId = null;
  localStorage.removeItem('panda_active_session');
  messagesContainer.innerHTML = '';
  if (ws && isConnected) {
    ws.send(JSON.stringify({ action: 'reset' }));
  }
  renderConversationHistory();
}

function quickAction(promptText) {
  userInput.value = promptText;
  sendMessage();
}

function resetChat() {
  if (confirm('কথোপকথন মেমরি রিসেট করবেন?')) {
    createNewChatSession();
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Voice Synthesis (Text-to-Speech)
function speakText(text) {
  if (isVoiceMuted || !('speechSynthesis' in window)) return;

  // Stop listening while speaking to prevent Panda from hearing its own voice
  if (recognition && isRecognizing) {
    try { recognition.stop(); } catch (e) {}
  }

  // Strip markdown symbols and code blocks for clean, natural speech
  let cleanText = text
    .replace(/```[\s\S]*?```/g, 'কোড তৈরি সম্পন্ন হয়েছে')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/[*_#~>\[\]]/g, '')
    .trim();

  // If text is very long, summarize for spoken audio
  if (cleanText.length > 250) {
    cleanText = cleanText.substring(0, 250) + '... বিস্তারিত স্ক্রিনে দেখানো হলো।';
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  // Pick appropriate voice (prefer Hindi or English)
  const voices = window.speechSynthesis.getVoices();
  const isHindiText = /[\u0900-\u097F]/.test(cleanText);
  let chosenVoice = null;
  if (isHindiText) {
    chosenVoice = voices.find(v => v.lang.includes('hi') || v.lang.includes('HI'));
  }
  if (!chosenVoice) {
    chosenVoice = voices.find(v => v.lang.includes('en') || v.lang.includes('US') || v.lang.includes('IN'));
  }
  if (chosenVoice) {
    utterance.voice = chosenVoice;
  }

  isSpeaking = true;
  utterance.onend = () => {
    isSpeaking = false;
    // Resume listening after agent speech completes if mic was previously active
    setTimeout(() => {
      if (!isSpeaking && recognition && !isRecognizing) {
        try { recognition.start(); } catch (e) {}
      }
    }, 500);
  };

  utterance.onerror = () => {
    isSpeaking = false;
  };

  window.speechSynthesis.speak(utterance);
}

function toggleVoiceMute() {
  isVoiceMuted = !isVoiceMuted;
  if (isVoiceMuted) {
    window.speechSynthesis.cancel();
    voiceMuteBtn.textContent = '🔈 Voice Reply: OFF';
    voiceMuteBtn.style.color = 'var(--text-dim)';
  } else {
    voiceMuteBtn.textContent = '🔊 Voice Reply: ON';
    voiceMuteBtn.style.color = '#818cf8';
  }
}

// Voice Recognition (Speech-to-Text) with Wake Word Support
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceStatusText.textContent = '⚠️ Speech Recognition not supported in this browser (Use Chrome or Edge)';
    if (micBtn) micBtn.style.display = 'none';
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'bn-BD'; // Primary Bengali, but captures English phrases like 'Hey Lootha'

  recognition.onstart = () => {
    isRecognizing = true;
    micBtn.classList.add('listening');
    voiceStatusText.textContent = '🎙️ শুনছি... বলুন "Hey Panda" বা আপনার নির্দেশ!';
  };

  recognition.onend = () => {
    isRecognizing = false;
    micBtn.classList.remove('listening');
    voiceStatusText.textContent = '🎤 মাইক্রোফোন বাটনে ক্লিক করে কথা বলুন';
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    isRecognizing = false;
    micBtn.classList.remove('listening');
    voiceStatusText.textContent = `🎤 ত্রুটি: ${event.error} (আবার চেষ্টা করুন)`;
  };

  recognition.onresult = (event) => {
    // If agent is currently speaking, ignore incoming mic audio completely
    if (isSpeaking) return;

    let interimTranscript = '';
    let finalTranscript = '';
    for (let i = 0; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript + ' ';
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    const currentSpeech = (finalTranscript + interimTranscript).trim();
    if (currentSpeech) {
      voiceStatusText.textContent = `🗣️ Listening: "${currentSpeech}" (Wait 3s of silence to execute)`;
      userInput.value = currentSpeech;

      // Reset and start 3-second silence timer
      clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {
        // 3 seconds elapsed without new speech -> stop listening and execute action
        const captured = userInput.value.trim();
        if (captured) {
          voiceStatusText.textContent = `⏳ 3s completed! Executing command: "${captured}"`;
          if (recognition && isRecognizing) {
            try { recognition.stop(); } catch (e) {}
          }
          handleSpokenCommand(captured);
        }
      }, SILENCE_TIMEOUT_MS);
    }
  };
}

function toggleSpeechRecognition() {
  if (!recognition) {
    initSpeechRecognition();
  }
  if (!recognition) return;

  if (isRecognizing) {
    clearTimeout(silenceTimer);
    recognition.stop();
  } else {
    try {
      clearTimeout(silenceTimer);
      recognition.start();
    } catch (e) {
      console.error(e);
    }
  }
}

function handleSpokenCommand(transcript) {
  clearTimeout(silenceTimer);
  const lower = transcript.toLowerCase().trim();

  // Wake-word only detection: e.g. "hey panda", "panda", "hello panda"
  const isWakeWordOnly = 
    lower === 'hey panda' || 
    lower === 'panda' || 
    lower === 'hello panda' || 
    lower === 'hey' ||
    lower === 'हे पांडा' ||
    lower === 'पांडा';

  if (isWakeWordOnly) {
    // Instant wake-word response in English / Hindi
    const isHindiUser = /[\u0900-\u097F]/.test(transcript);
    const wakeReply = isHindiUser
      ? 'जी बॉस! बताइए, मैं आपके लिए क्या कर सकता हूँ?'
      : 'Yes Boss! How can I assist you right now?';

    appendUserMessage(transcript);
    
    // Add agent response
    prepareAgentResponseContainer();
    updateAgentResponseText(wakeReply);
    speakText(wakeReply);
    currentAgentMessageDiv = null;
    return;
  }

  // If command includes wake word like "Hey Panda install chrome" or direct command
  userInput.value = transcript;
  sendMessage();
}

// Event Listeners
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);

modelSelect.addEventListener('change', () => {
  fetch('/api/model', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: modelSelect.value })
  });
});

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
  initWebSocket();
  renderConversationHistory();
  initSpeechRecognition();
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      // Voices loaded
    };
  }
});
