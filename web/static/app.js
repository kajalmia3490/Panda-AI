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
const voiceSelect = document.getElementById('voice-select');
const sidebar = document.getElementById('sidebar');
const fileInput = document.getElementById('file-input');
const attachBtn = document.getElementById('attach-btn');
const attachmentPreviewContainer = document.getElementById('attachment-preview-container');

let pendingAttachments = []; // Array of { name, type, size, data (base64) }

function toggleSidebar() {
  if (!sidebar) return;
  const isCollapsed = sidebar.classList.toggle('collapsed');
  localStorage.setItem('panda_sidebar_collapsed', isCollapsed ? 'true' : 'false');
}

function initSidebarState() {
  if (!sidebar) return;
  const savedState = localStorage.getItem('panda_sidebar_collapsed');
  // Collapse on mobile by default or if user previously collapsed it
  if (savedState === 'true' || (savedState === null && window.innerWidth <= 768)) {
    sidebar.classList.add('collapsed');
  } else {
    sidebar.classList.remove('collapsed');
  }
}

let availableVoices = [];

function populateVoiceList() {
  if (!('speechSynthesis' in window) || !voiceSelect) return;
  availableVoices = window.speechSynthesis.getVoices();
  if (!availableVoices || availableVoices.length === 0) return;

  const currentSelection = voiceSelect.value || localStorage.getItem('panda_preferred_voice') || 'auto';
  voiceSelect.innerHTML = '<option value="auto">Auto (Bangla bn-BD Priority)</option>';

  // Sort: Bangla & Hindi first, then other languages
  const sortedVoices = [...availableVoices].sort((a, b) => {
    const aIsBn = a.lang.toLowerCase().includes('bn');
    const bIsBn = b.lang.toLowerCase().includes('bn');
    if (aIsBn && !bIsBn) return -1;
    if (!aIsBn && bIsBn) return 1;
    return a.name.localeCompare(b.name);
  });

  sortedVoices.forEach((voice) => {
    const opt = document.createElement('option');
    opt.value = voice.name;
    const isBn = voice.lang.toLowerCase().includes('bn') ? ' 🇧🇩 [Bangla]' : '';
    const isHi = voice.lang.toLowerCase().includes('hi') ? ' 🇮🇳 [Hindi]' : '';
    opt.textContent = `${voice.name} (${voice.lang})${isBn}${isHi}`;
    if (voice.name === currentSelection) {
      opt.selected = true;
    }
    voiceSelect.appendChild(opt);
  });
}

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
  if (toolName === 'capture_screenshot') icon = '📸';
  if (toolName === 'list_open_windows') icon = '🪟';
  if (toolName === 'get_clipboard_content') icon = '📋';
  if (toolName === 'set_clipboard_content') icon = '📋';

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

  let extraVisualHtml = '';
  // If agent captured a screenshot, render live visual image card directly in chat
  if (toolName === 'capture_screenshot') {
    const timestamp = Date.now();
    extraVisualHtml = `
      <div style="margin-top:8px;">
        <a href="/api/screenshot?t=${timestamp}" target="_blank" title="Click to view full screen">
          <img src="/api/screenshot?t=${timestamp}" style="max-width:100%; max-height:260px; border-radius:8px; border:1px solid var(--border-color); box-shadow:0 4px 12px rgba(0,0,0,0.3); object-fit:contain; background:#000;" alt="Screen Activity Visual">
        </a>
        <div style="font-size:0.7rem; color:var(--text-dim); margin-top:3px;">📸 Live Desktop Activity Preview (Click to view full)</div>
      </div>
    `;
  }

  pill.innerHTML = `
    <div class="tool-icon">✓</div>
    <div class="tool-details">
      <div class="tool-name" style="color:var(--accent-emerald);">Result: ${toolName}</div>
      <div class="tool-output">${escapeHtml(truncated)}</div>
      ${extraVisualHtml}
    </div>
  `;

  streamArea.appendChild(pill);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function renderAttachmentPreviews() {
  if (!attachmentPreviewContainer) return;
  attachmentPreviewContainer.innerHTML = '';
  if (pendingAttachments.length === 0) {
    attachmentPreviewContainer.style.display = 'none';
    return;
  }
  attachmentPreviewContainer.style.display = 'flex';

  pendingAttachments.forEach((att, index) => {
    const item = document.createElement('div');
    item.className = 'attachment-preview-item';

    const isImg = att.type.startsWith('image/');
    let previewEl = '';
    if (isImg && att.data) {
      previewEl = `<img src="${att.data}" class="attachment-preview-thumb" alt="${escapeHtml(att.name)}">`;
    } else {
      const ext = att.name.split('.').pop() || 'file';
      previewEl = `<div class="attachment-preview-icon">📄</div>`;
    }

    item.innerHTML = `
      ${previewEl}
      <div class="attachment-preview-name" title="${escapeHtml(att.name)}">${escapeHtml(att.name)}</div>
      <button type="button" class="attachment-remove-btn" onclick="removeAttachment(${index})" title="Remove attachment">✕</button>
    `;
    attachmentPreviewContainer.appendChild(item);
  });
}

function removeAttachment(index) {
  pendingAttachments.splice(index, 1);
  renderAttachmentPreviews();
}

function handleFilesSelected(files) {
  if (!files || files.length === 0) return;
  Array.from(files).forEach((file) => {
    // Max 10MB per file for WebSocket transfer
    if (file.size > 10 * 1024 * 1024) {
      alert(`ফাইল '${file.name}' সাইজ অনেক বড় (সর্বোচ্চ ১০MB)`);
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      pendingAttachments.push({
        name: file.name,
        type: file.type || 'application/octet-stream',
        size: file.size,
        data: e.target.result // Data URL (data:image/png;base64,...)
      });
      renderAttachmentPreviews();
    };
    reader.readAsDataURL(file);
  });
}

function appendUserMessage(text, attachments = [], record = true) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-wrapper user';

  const header = document.createElement('div');
  header.className = 'msg-header';
  header.style.justifyContent = 'flex-end';
  header.innerHTML = `<span>You</span> • <span>${new Date().toLocaleTimeString()}</span>`;

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';

  // Render attached images/files in user bubble
  if (attachments && attachments.length > 0) {
    const attContainer = document.createElement('div');
    attContainer.style.display = 'flex';
    attContainer.style.flexWrap = 'wrap';
    attContainer.style.gap = '8px';
    attContainer.style.marginBottom = text ? '8px' : '0';

    attachments.forEach((att) => {
      if (att.type && att.type.startsWith('image/')) {
        const img = document.createElement('img');
        img.src = att.data;
        img.style.maxWidth = '200px';
        img.style.maxHeight = '140px';
        img.style.borderRadius = '8px';
        img.style.objectFit = 'cover';
        img.style.border = '1px solid rgba(255,255,255,0.15)';
        attContainer.appendChild(img);
      } else {
        const fileChip = document.createElement('div');
        fileChip.style.display = 'inline-flex';
        fileChip.style.alignItems = 'center';
        fileChip.style.gap = '6px';
        fileChip.style.background = 'rgba(0,0,0,0.25)';
        fileChip.style.padding = '4px 8px';
        fileChip.style.borderRadius = '6px';
        fileChip.style.fontSize = '0.8rem';
        fileChip.innerHTML = `📎 <span>${escapeHtml(att.name)}</span>`;
        attContainer.appendChild(fileChip);
      }
    });
    bubble.appendChild(attContainer);
  }

  if (text) {
    const textNode = document.createElement('div');
    textNode.textContent = text;
    bubble.appendChild(textNode);
  }

  wrapper.appendChild(header);
  wrapper.appendChild(bubble);

  messagesContainer.appendChild(wrapper);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  if (record) {
    recordMessageToHistory('user', text || '[Attachment]');
  }
}

function sendMessage() {
  const text = userInput.value.trim();
  const hasAttachments = pendingAttachments.length > 0;
  if ((!text && !hasAttachments) || !isConnected) return;

  const currentAttachments = [...pendingAttachments];
  pendingAttachments = [];
  renderAttachmentPreviews();

  appendUserMessage(text, currentAttachments);
  userInput.value = '';

  setAgentWorking(true);

  ws.send(JSON.stringify({
    action: 'chat',
    prompt: text,
    attachments: currentAttachments,
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

  // Strip markdown symbols, asterisks, hashtags and code blocks
  let cleanText = text
    .replace(/```[\s\S]*?```/g, 'কোড তৈরি সম্পন্ন হয়েছে।')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/[*_#~>\[\]\(\)]/g, '')
    // Strip all emojis and symbol characters completely so TTS never pronounces emoji names
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1FA70}-\u{1FAFF}\u{1F004}\u{1F0CF}\u{1F170}-\u{1F251}]/gu, '')
    .trim();

  // If text is very long, summarize for spoken audio
  if (cleanText.length > 250) {
    cleanText = cleanText.substring(0, 250) + '... বিস্তারিত স্ক্রিনে দেখানো হলো।';
  }

  try {
    // Resume audio context/speech synthesis if paused by browser autoplay policy
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    window.speechSynthesis.cancel();
  } catch (e) {}

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  // Pick appropriate voice
  let voices = window.speechSynthesis.getVoices();
  const isBanglaText = /[\u0980-\u09FF]/.test(cleanText);
  const isHindiText = /[\u0900-\u097F]/.test(cleanText);
  let chosenVoice = null;

  // 1. Check if user selected a specific voice from dropdown
  const preferredVoiceName = voiceSelect ? voiceSelect.value : 'auto';
  if (preferredVoiceName && preferredVoiceName !== 'auto') {
    chosenVoice = voices.find(v => v.name === preferredVoiceName);
    if (chosenVoice) {
      utterance.lang = chosenVoice.lang;
    }
  }

  // 2. If auto or not found, detect by language
  if (!chosenVoice) {
    if (isBanglaText) {
      utterance.lang = 'bn-BD';
      chosenVoice = voices.find(v => v.lang === 'bn-BD' || v.lang.toLowerCase().includes('bn-bd')) ||
                    voices.find(v => v.lang.toLowerCase().includes('bn-in') || v.lang.toLowerCase().includes('bn')) ||
                    voices.find(v => v.lang.toLowerCase().includes('in'));
    } else if (isHindiText) {
      utterance.lang = 'hi-IN';
      chosenVoice = voices.find(v => v.lang.includes('hi') || v.lang.includes('HI'));
    } else {
      utterance.lang = 'en-US';
    }
  }

  // If still not matched, fallback to system default voice
  if (!chosenVoice) {
    chosenVoice = voices.find(v => v.lang.includes('en') || v.lang.includes('US') || v.lang.includes('GB')) || voices[0];
  }
  if (chosenVoice) {
    utterance.voice = chosenVoice;
  }

  isSpeaking = true;
  // Explicitly abort/stop recognition while Panda speaks to guarantee no loop/echo
  if (recognition) {
    try { recognition.abort(); } catch (e) {}
  }

  utterance.onstart = () => {
    isSpeaking = true;
    if (recognition) {
      try { recognition.abort(); } catch (e) {}
    }
  };

  utterance.onend = () => {
    // Keep a 400ms buffer after speech finishes so room echo does not trigger the mic
    setTimeout(() => {
      isSpeaking = false;
      if (recognition && !isRecognizing) {
        try { recognition.start(); } catch (e) {}
      }
    }, 400);
  };

  utterance.onerror = (err) => {
    console.warn('SpeechSynthesis error:', err);
    setTimeout(() => {
      isSpeaking = false;
      if (recognition && !isRecognizing) {
        try { recognition.start(); } catch (e) {}
      }
    }, 300);
  };

  // Workaround for Chrome/Edge garbage-collection bug on long utterances
  window._currentUtterance = utterance;

  // Small timeout after cancel() prevents speech synthesis queue drop bug in Chromium
  setTimeout(() => {
    window.speechSynthesis.speak(utterance);
  }, 50);
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
  recognition.lang = 'bn-BD'; // Primary Bengali, captures English & Hindi phrases seamlessly

  recognition.onstart = () => {
    isRecognizing = true;
    micBtn.classList.add('listening');
    voiceStatusText.textContent = '🎙️ সর্বদা শুনছি... বলুন "Hey Panda" বা যেকোনো নির্দেশ!';
  };

  recognition.onend = () => {
    isRecognizing = false;
    // Always-on voice recognition: auto-restart immediately unless agent is speaking
    if (!isSpeaking) {
      setTimeout(() => {
        if (!isRecognizing && !isSpeaking) {
          try {
            recognition.start();
          } catch (e) {}
        }
      }, 300);
    } else {
      micBtn.classList.remove('listening');
      voiceStatusText.textContent = '🔊 Panda কথা বলছে... (মাইক্রোফোন সাময়িক মিউট)';
    }
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition status:', event.error);
    isRecognizing = false;
    micBtn.classList.remove('listening');
    // For no-speech or network glitches, auto-restart silently to keep voice always-on
    if (event.error === 'no-speech' || event.error === 'audio-capture' || event.error === 'network') {
      setTimeout(() => {
        if (!isRecognizing && !isSpeaking) {
          try { recognition.start(); } catch (e) {}
        }
      }, 1000);
    } else {
      voiceStatusText.textContent = `🎤 অবস্থা: ${event.error} (স্বয়ংক্রিয়ভাবে পুনরায় চালু হচ্ছে...)`;
      setTimeout(() => {
        if (!isRecognizing && !isSpeaking) {
          try { recognition.start(); } catch (e) {}
        }
      }, 1500);
    }
  };

  recognition.onresult = (event) => {
    // If agent is currently speaking, completely ignore and discard all microphone audio
    if (isSpeaking) {
      clearTimeout(silenceTimer);
      return;
    }

    let interimTranscript = '';
    let finalTranscript = '';
    for (let i = 0; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript + ' ';
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    // Double check that agent didn't start speaking in this exact instant
    if (isSpeaking) {
      clearTimeout(silenceTimer);
      return;
    }

    const currentSpeech = (finalTranscript + interimTranscript).trim();
    if (currentSpeech) {
      voiceStatusText.textContent = `🗣️ শুনছি: "${currentSpeech}"`;
      userInput.value = currentSpeech;

      // Reset and start silence threshold timer to execute command
      clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {
        if (isSpeaking) return; // Prevent executing if AI spoke in between
        const captured = userInput.value.trim();
        if (captured) {
          voiceStatusText.textContent = `⏳ নির্দেশ কার্যকর করা হচ্ছে: "${captured}"`;
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

  // Wake-word only detection: e.g. "hey panda", "হেই প্যান্ডা", "হে পাंडा"
  const isWakeWordOnly = 
    lower === 'hey panda' || 
    lower === 'panda' || 
    lower === 'hello panda' || 
    lower === 'hey' ||
    lower === 'হেই প্যান্ডা' ||
    lower === 'প্যান্ডা' ||
    lower === 'হ্যালো প্যান্ডা' ||
    lower === 'হে পাণ্ডা' ||
    lower === 'हे पांडा' ||
    lower === 'पांडा' ||
    lower === 'नमस्ते पांडा';

  if (isWakeWordOnly) {
    const isBangla = /[\u0980-\u09FF]/.test(transcript) || lower.includes('panda') || lower.includes('hey');
    const isHindi = /[\u0900-\u097F]/.test(transcript);
    
    let wakeReply = 'Yes Boss! How can I assist you right now?';
    if (isBangla) {
      wakeReply = 'জী বস! বলুন, আমি আপনার জন্য কী করতে পারি?';
    } else if (isHindi) {
      wakeReply = 'जी बॉस! बताइए, मैं आपके लिए क्या कर सकता हूँ?';
    }

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
  initSidebarState();
  initWebSocket();
  renderConversationHistory();
  initSpeechRecognition();

  // Start continuous listening immediately
  setTimeout(() => {
    if (recognition && !isRecognizing && !isSpeaking) {
      try { recognition.start(); } catch (e) {}
    }
  }, 400);

  // Populate voice selector & Pre-load voices immediately
  if ('speechSynthesis' in window) {
    populateVoiceList();
    window.speechSynthesis.onvoiceschanged = () => {
      populateVoiceList();
    };
  }

  if (voiceSelect) {
    voiceSelect.addEventListener('change', () => {
      localStorage.setItem('panda_preferred_voice', voiceSelect.value);
    });
  }

  // Attach button click
  if (attachBtn && fileInput) {
    attachBtn.addEventListener('click', () => {
      fileInput.click();
    });
    fileInput.addEventListener('change', (e) => {
      handleFilesSelected(e.target.files);
      fileInput.value = ''; // Reset for re-selection
    });
  }

  // Drag and drop files directly onto input area or window
  window.addEventListener('dragover', (e) => {
    e.preventDefault();
  });
  window.addEventListener('drop', (e) => {
    e.preventDefault();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelected(e.dataTransfer.files);
    }
  });

  // Paste screenshots or images directly from clipboard (Ctrl + V)
  window.addEventListener('paste', (e) => {
    if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      handleFilesSelected(e.clipboardData.files);
    }
  });

  // Unlock browser audio autoplay policy on first user interaction
  const unlockAudio = () => {
    if ('speechSynthesis' in window && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    document.removeEventListener('click', unlockAudio);
  };
  document.addEventListener('click', unlockAudio);
});
