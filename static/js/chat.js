/**
 * AI Shopping Assistant Chat Module
 * Powered by Gemini 2.5 Flash & Backend Search Pipeline
 */

const ChatAssistant = {
  sessionId: null,
  isOpen: false,
  isWaiting: false,

  init() {
    this.sessionId = sessionStorage.getItem('electro_session_id');
    if (!this.sessionId) {
      this.sessionId = 'sess_' + Math.random().toString(36).substring(2, 11) + Date.now();
      sessionStorage.setItem('electro_session_id', this.sessionId);
    }

    const drawer = document.getElementById('aiChatDrawer');
    const floatingBtn = document.getElementById('floatingAiBtn');
    const headerBtn = document.getElementById('chatToggleHeaderBtn');
    const headerAskBtn = document.getElementById('headerAskAiBtn');
    const promoChatBtn = document.getElementById('promoChatBtn');
    const emptyAskAiBtn = document.getElementById('emptyAskAiBtn');
    const closeBtn = document.getElementById('closeChatBtn');
    const resetBtn = document.getElementById('resetChatBtn');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');

    if (floatingBtn) floatingBtn.addEventListener('click', () => this.toggleChat());
    if (headerBtn) headerBtn.addEventListener('click', () => this.toggleChat());
    if (headerAskBtn) {
      headerAskBtn.addEventListener('click', () => {
        const searchVal = document.getElementById('mainSearchInput')?.value.trim();
        this.openChat();
        if (searchVal) {
          this.sendMessage(searchVal);
        }
      });
    }
    if (promoChatBtn) promoChatBtn.addEventListener('click', () => this.openChat());
    if (emptyAskAiBtn) promoChatBtn && emptyAskAiBtn.addEventListener('click', () => this.openChat());
    if (closeBtn) closeBtn.addEventListener('click', () => this.closeChat());
    if (resetBtn) resetBtn.addEventListener('click', () => this.resetConversation());

    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const msg = chatInput.value.trim();
        if (msg && !this.isWaiting) {
          this.sendMessage(msg);
          chatInput.value = '';
        }
      });
    }

    // Quick prompt buttons
    document.querySelectorAll('.prompt-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const text = pill.dataset.prompt;
        if (text) {
          this.openChat();
          this.sendMessage(text);
        }
      });
    });
  },

  openChat() {
    const drawer = document.getElementById('aiChatDrawer');
    const floatingBtn = document.getElementById('floatingAiBtn');
    if (drawer) {
      drawer.classList.remove('hidden');
      this.isOpen = true;
    }
    if (floatingBtn) floatingBtn.style.display = 'none';

    // Focus input
    setTimeout(() => {
      document.getElementById('chatInput')?.focus();
      this.scrollToBottom();
    }, 100);
  },

  closeChat() {
    const drawer = document.getElementById('aiChatDrawer');
    const floatingBtn = document.getElementById('floatingAiBtn');
    if (drawer) {
      drawer.classList.add('hidden');
      this.isOpen = false;
    }
    if (floatingBtn) floatingBtn.style.display = 'flex';
  },

  toggleChat() {
    if (this.isOpen) {
      this.closeChat();
    } else {
      this.openChat();
    }
  },

  async resetConversation() {
    try {
      await fetch('/api/reset-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.sessionId })
      });
      const container = document.getElementById('chatMessagesContainer');
      if (container) {
        container.innerHTML = `
          <div class="message-bubble assistant">
            <div class="message-avatar">AI</div>
            <div class="message-body">
              <div class="message-text">
                Conversation reset. How can I help you find electronics today?
              </div>
            </div>
          </div>
        `;
      }
    } catch (err) {
      console.error('Failed to reset session:', err);
    }
  },

  async sendMessage(text) {
    if (!text || this.isWaiting) return;

    this.appendUserMessage(text);
    this.showTyping(true);
    this.isWaiting = true;

    try {
      const activeCat = window.CatalogApp?.currentCategory || '';
      const activeBrand = window.CatalogApp?.currentBrand || '';

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: this.sessionId,
          context: {
            category: activeCat,
            brand: activeBrand
          }
        })
      });

      const data = await res.json();
      this.showTyping(false);
      this.isWaiting = false;

      this.appendAssistantResponse(data);
    } catch (err) {
      console.error('Chat error:', err);
      this.showTyping(false);
      this.isWaiting = false;
      this.appendAssistantResponse({
        reply: "I'm having trouble connecting to the shopping database right now. Please try again in a moment.",
        products: []
      });
    }
  },

  appendUserMessage(text) {
    const container = document.getElementById('chatMessagesContainer');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'message-bubble user';
    div.innerHTML = `
      <div class="message-body">
        <div class="message-text">${this.escapeHtml(text)}</div>
      </div>
    `;
    container.appendChild(div);
    this.scrollToBottom();
  },

  appendAssistantResponse(data) {
    const container = document.getElementById('chatMessagesContainer');
    if (!container) return;

    const reply = data.reply || '';
    const products = data.products || [];
    const targetProduct = data.target_product;
    const similarProducts = data.similar_products || [];
    const actionButtons = data.action_buttons || [];

    // Format markdown bold/bullets in text
    let formattedText = this.formatMarkdown(reply);

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble assistant';

    let contentHtml = `
      <div class="message-avatar">AI</div>
      <div class="message-body">
        <div class="message-text">${formattedText}</div>
    `;

    // Display target product card if exact product was found
    if (targetProduct) {
      contentHtml += `
        <div class="chat-products-list">
          <div class="chat-product-item">
            <img src="${targetProduct.image_url}" class="chat-prod-img" alt="${targetProduct.title}">
            <div class="chat-prod-info">
              <div class="chat-prod-title">${targetProduct.title}</div>
              <div class="chat-prod-price">₹${targetProduct.price.toLocaleString()}</div>
              <div style="font-size: 0.72rem; color: var(--text-secondary);">⭐ ${targetProduct.rating} • ${targetProduct.brand}</div>
            </div>
            <button class="chat-prod-btn" onclick="ProductDetails.openProduct('${targetProduct.id}')">View Specs</button>
          </div>
        </div>
      `;
    } else if (products && products.length > 0 && products.length <= 4) {
      // Small product carousel inside chat
      contentHtml += `
        <div class="chat-products-list">
          ${products.map(p => `
            <div class="chat-product-item">
              <img src="${p.image_url}" class="chat-prod-img" alt="${p.title}">
              <div class="chat-prod-info">
                <div class="chat-prod-title">${p.title}</div>
                <div class="chat-prod-price">₹${p.price.toLocaleString()}</div>
                <div style="font-size: 0.72rem; color: var(--text-secondary);">⭐ ${p.rating} • ${p.brand}</div>
              </div>
              <button class="chat-prod-btn" onclick="ProductDetails.openProduct('${p.id}')">View</button>
            </div>
          `).join('')}
        </div>
      `;
    }

    // Action buttons (e.g. [Show Similar Products], [Search Again])
    if (actionButtons && actionButtons.length > 0) {
      contentHtml += `<div class="chat-action-buttons">`;
      actionButtons.forEach(btn => {
        const btnId = 'act_' + Math.random().toString(36).substr(2, 9);
        contentHtml += `<button id="${btnId}" class="chat-action-btn">${btn.label}</button>`;

        // Add listener after insertion
        setTimeout(() => {
          const el = document.getElementById(btnId);
          if (el) {
            el.addEventListener('click', () => this.handleActionClick(btn));
          }
        }, 50);
      });
      contentHtml += `</div>`;
    }

    contentHtml += `</div>`;
    bubble.innerHTML = contentHtml;
    container.appendChild(bubble);

    // If products were returned, also sync with main catalog grid
    if (products && products.length > 0) {
      window.CatalogApp?.displayProducts(products, `AI Search: "${data.tier || 'Assistant recommendations'}"`);
    }

    this.scrollToBottom();
  },

  handleActionClick(actionBtn) {
    if (actionBtn.action === 'show_similar') {
      const brand = actionBtn.brand || '';
      const cat = actionBtn.category || 'products';
      this.sendMessage(`Show similar ${brand} ${cat}`);
    } else if (actionBtn.action === 'search_again') {
      document.getElementById('chatInput')?.focus();
    } else if (actionBtn.action === 'browse_category') {
      window.CatalogApp?.setCategory(actionBtn.category || '');
    } else if (actionBtn.action === 'search_query') {
      this.sendMessage(actionBtn.query);
    } else if (actionBtn.action === 'compare') {
      if (actionBtn.product_id) {
        ProductDetails.toggleCompare(actionBtn.product_id);
        this.sendMessage(`Who does ${actionBtn.product_id} compare best against?`);
      }
    } else if (actionBtn.action === 'compare_top') {
      if (actionBtn.ids && actionBtn.ids.length >= 2) {
        ProductDetails.comparisonIds.clear();
        actionBtn.ids.forEach(id => ProductDetails.comparisonIds.add(id));
        ProductDetails.updateCompareUI();
        ProductDetails.openComparisonModal();
      }
    }
  },

  showTyping(show) {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
      if (show) {
        indicator.classList.remove('hidden');
      } else {
        indicator.classList.add('hidden');
      }
    }
    this.scrollToBottom();
  },

  scrollToBottom() {
    const container = document.getElementById('chatMessagesContainer');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  },

  escapeHtml(str) {
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  },

  formatMarkdown(text) {
    if (!text) return '';
    let t = this.escapeHtml(text);
    // Bold
    t = t.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Bullet points
    t = t.replace(/^\s*•\s*(.*)$/gm, '<li>$1</li>');
    t = t.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    return t;
  }
};

window.ChatAssistant = ChatAssistant;
document.addEventListener('DOMContentLoaded', () => ChatAssistant.init());
