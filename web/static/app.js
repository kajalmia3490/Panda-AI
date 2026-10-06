let ws;
let isConnected = false;
let currentAgentMessageDiv = null;

let isVoiceMuted = false;
let recognition = null;
let isRecognizing = false;
let isSpeaking = false;
let silenceTimer = null;
const SILENCE_TIMEOUT_MS = 5000; // 5 seconds silence threshold

const messagesContainer = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const modelSelect = document.getElementById('model-select');
const fileTree = document.getElementById('file-tree');
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
  header.innerHTML = `<span>🐼 Panda (প্যান্ডা)</span> • <span>${new Date().toLocaleTimeString()}</span>`;

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

function appendUserMessage(text) {
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

async function refreshFiles() {
  try {
    const res = await fetch('/api/files');
    const data = await res.json();
    fileTree.innerHTML = '';
    
    const lines = data.output.split('\n');
    lines.forEach(line => {
      if (!line.trim()) return;
      const div = document.createElement('div');
      div.className = 'file-item';
      
      if (line.startsWith('[DIR]')) {
        div.classList.add('dir');
        div.innerHTML = `📁 ${line.replace('[DIR]', '').trim()}`;
      } else if (line.startsWith('[FILE]')) {
        div.innerHTML = `📄 ${line.replace('[FILE]', '').trim()}`;
        div.onclick = () => {
          const fileName = line.replace('[FILE]', '').split('(')[0].trim();
          quickAction(`Inspect and explain the file ${fileName}`);
        };
      } else {
        div.textContent = line;
      }
      fileTree.appendChild(div);
    });
  } catch (err) {
    fileTree.innerHTML = '<div style="color:var(--accent-rose); padding:8px;">Failed to load files</div>';
  }
}

function quickAction(promptText) {
  userInput.value = promptText;
  sendMessage();
}

function resetChat() {
  if (confirm('Clear chat session and reset agent memory?')) {
    ws.send(JSON.stringify({ action: 'reset' }));
    messagesContainer.innerHTML = '';
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

  // Pick appropriate voice (prefer Bengali or natural female/male voice)
  const voices = window.speechSynthesis.getVoices();
  const bnVoice = voices.find(v => v.lang.includes('bn') || v.lang.includes('BD') || v.lang.includes('IN'));
  if (bnVoice) {
    utterance.voice = bnVoice;
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
    voiceStatusText.textContent = '⚠️ আপনার ব্রাউজারে স্পিচ রিকগনিশন সাপোর্ট নেই (Chrome বা Edge ব্যবহার করুন)';
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
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    const currentSpeech = (finalTranscript || interimTranscript).trim();
    if (currentSpeech) {
      voiceStatusText.textContent = `🗣️ শুনছি: "${currentSpeech}" (৫ সেকেন্ড পর স্বয়ংক্রিয়ভাবে কাজ শুরু হবে)`;
      userInput.value = currentSpeech;

      // Reset and start 5-second silence timer
      clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {
        // 5 seconds elapsed without new speech -> stop listening and execute action
        const captured = userInput.value.trim();
        if (captured) {
          voiceStatusText.textContent = `⏳ সময় শেষ! অ্যাকশন নেওয়া হচ্ছে: "${captured}"`;
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

  // Wake-word only detection: e.g. "hey panda", "panda", "হেই প্যান্ডা"
  const isWakeWordOnly = 
    lower === 'hey panda' || 
    lower === 'panda' || 
    lower === 'hello panda' || 
    lower === 'hey' || 
    transcript.trim() === 'হেই প্যান্ডা' || 
    transcript.trim() === 'প্যান্ডা';

  if (isWakeWordOnly) {
    // Instant wake-word response in voice and chat
    const wakeReply = 'জী বস! বলুন, আমি আপনার জন্য কী করতে পারি?';
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
  refreshFiles();
  initSpeechRecognition();
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
      // Voices loaded
    };
  }
});
