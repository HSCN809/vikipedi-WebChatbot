/**
 * Vikipedi Chatbot - Ana JavaScript Dosyası
 * Chat yönetimi ve UI etkileşimleri
 */

// ===== DOM Elements =====
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const chatListEl = document.getElementById("chat-list");
const sidebar = document.getElementById("sidebar");
const menuToggle = document.getElementById("menu-toggle");
const appContainer = document.querySelector('.app-container');

// ===== State =====
let isStreaming = false;
let currentBotMessage = null;
let chats = [];
let activeChat = null;

// ===== Storage Key =====
const STORAGE_KEY = 'wikipedia_chats';

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    initEventListeners();
    loadChats();
    init3DEffect();
});

/**
 * Event listener'ları başlatır
 */
function initEventListeners() {
    sendBtn.addEventListener("click", sendMessage);
    
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && !isStreaming) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    newChatBtn.addEventListener("click", () => {
        createNewChat();
        userInput.focus();
    });
    
    menuToggle.addEventListener("click", () => {
        sidebar.classList.toggle('open');
    });
    
    // Sidebar dışına tıklandığında kapat (mobil)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            sidebar.classList.contains('open') && 
            !sidebar.contains(e.target) && 
            !menuToggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
}

/**
 * 3D tilt efektini başlatır
 */
function init3DEffect() {
    document.addEventListener('mousemove', (e) => {
        if (window.innerWidth <= 768) return; // Mobilde devre dışı
        
        const x = (e.clientX / window.innerWidth - 0.5) * 2;
        const y = (e.clientY / window.innerHeight - 0.5) * 2;
        appContainer.style.transform = `rotateY(${x * 2}deg) rotateX(${-y * 2}deg)`;
    });
}

/**
 * Floating particle efekti oluşturur
 */
function createParticles() {
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + 'vw';
        particle.style.animationDelay = Math.random() * 15 + 's';
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        document.body.appendChild(particle);
    }
}

// ===== Chat Management =====

/**
 * Benzersiz ID üretir
 * @returns {string} Benzersiz ID
 */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Yeni sohbet oluşturur
 * @returns {Object} Oluşturulan sohbet
 */
function createNewChat() {
    const chat = {
        id: generateId(),
        title: `Sohbet ${chats.length + 1}`,
        messages: [],
        createdAt: Date.now()
    };
    
    chats.unshift(chat);
    activeChat = chat.id;
    saveChats();
    renderChatList();
    renderChatBox();
    
    return chat;
}

/**
 * Sohbeti siler
 * @param {string} chatId - Silinecek sohbet ID'si
 */
async function deleteChat(chatId) {
    // Backend'den sil
    try {
        await fetch('/delete_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: chatId })
        });
    } catch (err) {
        console.error('Backend silme hatası:', err);
    }
    
    // Frontend'den sil
    chats = chats.filter(c => c.id !== chatId);
    
    if (activeChat === chatId) {
        activeChat = chats.length > 0 ? chats[0].id : null;
    }
    
    saveChats();
    renderChatList();
    renderChatBox();
}

/**
 * Sohbete geçiş yapar
 * @param {string} chatId - Geçilecek sohbet ID'si
 */
function switchChat(chatId) {
    activeChat = chatId;
    saveChats();
    renderChatList();
    renderChatBox();
    
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('open');
    }
}

/**
 * Aktif sohbeti döndürür
 * @returns {Object|undefined} Aktif sohbet
 */
function getCurrentChat() {
    return chats.find(c => c.id === activeChat);
}

/**
 * Sohbet başlığını günceller
 * @param {Object} chat - Güncellenecek sohbet
 */
function updateChatTitle(chat) {
    if (chat.messages.length > 0 && chat.title.startsWith('Sohbet ')) {
        const firstUserMsg = chat.messages.find(m => m.sender === 'user');
        if (firstUserMsg) {
            const maxLength = 30;
            chat.title = firstUserMsg.content.substring(0, maxLength) + 
                        (firstUserMsg.content.length > maxLength ? '...' : '');
            saveChats();
            renderChatList();
        }
    }
}

// ===== Rendering =====

/**
 * Sohbet listesini render eder
 */
function renderChatList() {
    chatListEl.innerHTML = '';
    
    if (chats.length === 0) {
        chatListEl.innerHTML = `
            <div style="text-align:center;color:rgba(255,255,255,0.5);padding:20px;font-size:13px;">
                Henüz sohbet yok
            </div>
        `;
        return;
    }
    
    chats.forEach(chat => {
        const div = document.createElement('div');
        div.className = `chat-item ${chat.id === activeChat ? 'active' : ''}`;
        div.innerHTML = `
            <div class="chat-item-title">${escapeHtml(chat.title)}</div>
            <div class="chat-item-actions">
                <button class="chat-item-btn delete" onclick="event.stopPropagation(); deleteChat('${chat.id}')" aria-label="Sohbeti sil">
                    <i class="fas fa-trash" aria-hidden="true"></i>
                </button>
            </div>
        `;
        div.addEventListener('click', () => switchChat(chat.id));
        chatListEl.appendChild(div);
    });
}

/**
 * Chat kutusunu render eder
 */
function renderChatBox() {
    chatBox.innerHTML = '';
    const chat = getCurrentChat();
    
    if (!chat) {
        chatBox.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comments" aria-hidden="true"></i>
                <h3>Hoş Geldiniz!</h3>
                <p>Yeni bir sohbet başlatmak için "Yeni Sohbet" butonuna tıklayın</p>
            </div>
        `;
        return;
    }
    
    chat.messages.forEach(msg => {
        appendMessage(msg.content, msg.sender, false);
    });
}

/**
 * Mesaj ekler
 * @param {string} content - Mesaj içeriği
 * @param {string} sender - Gönderen (user/bot)
 * @param {boolean} save - Kaydet
 * @returns {HTMLElement} Oluşturulan element
 */
function appendMessage(content, sender, save = true) {
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    
    if (sender === 'bot') {
        div.innerHTML = marked.parse(content);
    } else {
        div.innerText = content;
    }
    
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    if (save) {
        const chat = getCurrentChat();
        if (chat) {
            chat.messages.push({ 
                sender, 
                content, 
                timestamp: Date.now() 
            });
            updateChatTitle(chat);
            saveChats();
        }
    }
    
    return div;
}

/**
 * Yazma göstergesini oluşturur
 * @returns {HTMLElement} Typing indicator elementi
 */
function createTypingIndicator() {
    const div = document.createElement("div");
    div.className = "message bot typing-indicator";
    div.innerHTML = `
        <i class="fas fa-robot" aria-hidden="true"></i>
        <span>Düşünüyor</span>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    return div;
}

// ===== Message Sending =====

/**
 * Mesaj gönderir
 */
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isStreaming) return;
    
    let chat = getCurrentChat();
    if (!chat) {
        chat = createNewChat();
    }
    
    // UI güncellemeleri
    appendMessage(message, "user");
    userInput.value = "";
    isStreaming = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i>';
    
    // Typing indicator
    currentBotMessage = createTypingIndicator();
    chatBox.appendChild(currentBotMessage);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'Accept': 'text/event-stream' 
            },
            body: JSON.stringify({ 
                message: message,
                chat_id: chat.id
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        await handleStreamResponse(response, chat);
        
    } catch (error) {
        handleError(error);
    }
    
    // Cleanup
    isStreaming = false;
    sendBtn.disabled = false;
    sendBtn.innerHTML = '<i class="fas fa-paper-plane" aria-hidden="true"></i>';
    currentBotMessage = null;
}

/**
 * Stream response'u işler
 * @param {Response} response - Fetch response
 * @param {Object} chat - Aktif sohbet
 */
async function handleStreamResponse(response, chat) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let botContent = '';
    
    currentBotMessage.className = "message bot";
    currentBotMessage.innerHTML = "";
    
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.type === 'content') {
                        botContent += data.content;
                        currentBotMessage.innerHTML = marked.parse(botContent);
                        chatBox.scrollTop = chatBox.scrollHeight;
                    } else if (data.type === 'error') {
                        currentBotMessage.innerHTML = `
                            <i class="fas fa-exclamation-triangle" aria-hidden="true"></i> 
                            Hata: ${escapeHtml(data.error)}
                        `;
                        console.error('Stream Error:', data);
                        break;
                    } else if (data.type === 'end') {
                        break;
                    }
                } catch (e) {
                    console.error('JSON parse error:', e, line);
                }
            }
        }
    }
    
    // Mesajı kaydet
    if (botContent) {
        chat.messages.push({ 
            sender: 'bot', 
            content: botContent, 
            timestamp: Date.now() 
        });
        updateChatTitle(chat);
        saveChats();
    }
}

/**
 * Hata durumunu işler
 * @param {Error} error - Hata objesi
 */
function handleError(error) {
    if (currentBotMessage) {
        currentBotMessage.innerHTML = `
            <i class="fas fa-wifi" aria-hidden="true"></i> 
            Bağlantı hatası: ${escapeHtml(error.message)}
        `;
    }
    console.error('Fetch Error:', error);
}

// ===== Storage =====

/**
 * Sohbetleri localStorage'a kaydeder
 */
function saveChats() {
    try {
        const data = { chats, activeChat };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
        console.error('Sohbetler kaydedilemedi:', e);
    }
}

/**
 * Sohbetleri localStorage'dan yükler
 */
function loadChats() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            const data = JSON.parse(saved);
            chats = data.chats || [];
            activeChat = data.activeChat || null;
        }
    } catch (e) {
        console.error('Sohbetler yüklenemedi:', e);
        chats = [];
        activeChat = null;
    }
    
    if (chats.length === 0) {
        createNewChat();
    }
    
    renderChatList();
    renderChatBox();
}

// ===== Utilities =====

/**
 * HTML karakterlerini escape eder
 * @param {string} text - Escape edilecek metin
 * @returns {string} Escape edilmiş metin
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Sohbet geçmişini temizler
 */
async function clearCurrentChat() {
    const chat = getCurrentChat();
    if (!chat) return;
    
    try {
        await fetch('/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: chat.id })
        });
        
        chat.messages = [];
        saveChats();
        renderChatBox();
    } catch (err) {
        console.error('Sohbet temizleme hatası:', err);
    }
}

// Global fonksiyonlar (onclick için)
window.deleteChat = deleteChat;
window.clearCurrentChat = clearCurrentChat;
