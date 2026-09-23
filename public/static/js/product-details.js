/**
 * Product Details & Comparison Modal Module
 * Pure Vanilla JavaScript
 */

const ProductDetails = {
  activeProduct: null,
  comparisonIds: new Set(),

  init() {
    // Event listeners for closing modals
    const closeDetailBtn = document.getElementById('closeDetailModalBtn');
    const detailModal = document.getElementById('productDetailModal');
    if (closeDetailBtn) {
      closeDetailBtn.addEventListener('click', () => this.closeDetailModal());
    }
    if (detailModal) {
      detailModal.addEventListener('click', (e) => {
        if (e.target === detailModal) this.closeDetailModal();
      });
    }

    const closeCompBtn = document.getElementById('closeComparisonModalBtn');
    const compModal = document.getElementById('comparisonModal');
    const clearCompBtn = document.getElementById('clearComparisonBtn');
    const dockCompareBtn = document.getElementById('dockCompareBtn');
    const dockClearBtn = document.getElementById('dockClearBtn');
    const compareBarTrigger = document.getElementById('compareBarTrigger');

    if (closeCompBtn) closeCompBtn.addEventListener('click', () => this.closeComparisonModal());
    if (compModal) {
      compModal.addEventListener('click', (e) => {
        if (e.target === compModal) this.closeComparisonModal();
      });
    }
    if (clearCompBtn) clearCompBtn.addEventListener('click', () => this.clearComparison());
    if (dockCompareBtn) dockCompareBtn.addEventListener('click', () => this.openComparisonModal());
    if (dockClearBtn) dockClearBtn.addEventListener('click', () => this.clearComparison());
    if (compareBarTrigger) compareBarTrigger.addEventListener('click', () => this.openComparisonModal());
  },

  async openProduct(productId) {
    try {
      const res = await fetch(`/api/products/${encodeURIComponent(productId)}`);
      if (!res.ok) throw new Error('Product not found');
      const data = await res.json();
      this.activeProduct = data.product;
      this.renderDetailModal(data.product, data.similar || []);
    } catch (err) {
      console.error('Error loading product details:', err);
    }
  },

  renderDetailModal(product, similarProducts) {
    const modal = document.getElementById('productDetailModal');
    const container = document.getElementById('productDetailContent');
    if (!modal || !container) return;

    const inCompare = this.comparisonIds.has(product.id);

    // Build specs rows
    let specsHtml = '';
    const specs = product.specs || {};
    for (const [k, v] of Object.entries(specs)) {
      const label = k.replace(/_/g, ' ').toUpperCase();
      specsHtml += `
        <tr>
          <td class="spec-key">${label}</td>
          <td class="spec-val">${v}</td>
        </tr>
      `;
    }

    // Build pros and cons
    const prosHtml = (product.pros || []).map(p => `<li>${p}</li>`).join('');
    const consHtml = (product.cons || []).map(c => `<li>${c}</li>`).join('');

    // Build similar thumbnails
    let similarHtml = '';
    if (similarProducts.length > 0) {
      similarHtml = `
        <div style="margin-top: 24px; border-top: 1px solid var(--border-subtle); padding-top: 16px;">
          <h5 style="font-size: 0.9rem; margin-bottom: 10px; color: var(--text-secondary); text-transform: uppercase;">Similar Alternatives</h5>
          <div style="display: flex; gap: 10px; overflow-x: auto;">
            ${similarProducts.map(s => `
              <div style="width: 140px; background: var(--bg-surface-elevated); padding: 8px; border-radius: 8px; cursor: pointer; flex-shrink: 0;" onclick="ProductDetails.openProduct('${s.id}')">
                <img src="${s.image_url}" style="width: 100%; height: 80px; object-fit: cover; border-radius: 4px; margin-bottom: 6px;" alt="${s.title}">
                <div style="font-size: 0.75rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${s.title}</div>
                <div style="font-size: 0.8rem; font-weight: 800; color: var(--accent-secondary); font-family: var(--font-mono);">₹${s.price.toLocaleString()}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="detail-grid">
        <div class="detail-gallery">
          <img class="detail-img" src="${product.image_url}" alt="${product.title}">
          <div class="detail-gallery-actions">
            <button class="btn-primary" onclick="ProductDetails.toggleCompare('${product.id}')">
              ${inCompare ? '✓ In Comparison' : '+ Add to Comparison'}
            </button>
            <button class="btn-secondary" onclick="ProductDetails.askAiAbout('${product.id}')">
              ✨ Ask AI About This
            </button>
            <a href="${product.product_url}" target="_blank" rel="noopener noreferrer" class="btn-text" style="text-align: center; margin-top: 4px;">
              View on Retail Store ↗
            </a>
          </div>
        </div>

        <div class="detail-info">
          <div class="detail-header-row">
            <span class="detail-brand-badge">${product.brand} • ${product.category.toUpperCase()}</span>
            <h1 class="detail-title">${product.title}</h1>
            <div class="card-rating-row" style="margin-top: 6px;">
              <span class="stars">★★★★☆</span>
              <span class="rating-num">${product.rating} / 5.0</span>
              <span style="font-size: 0.8rem; color: var(--text-muted); margin-left: 8px;">Model: ${product.model}</span>
            </div>
          </div>

          <div class="detail-price-row">
            <span class="detail-price">₹${product.price.toLocaleString()}</span>
            <span style="font-size: 0.85rem; color: var(--success); font-weight: 600;">Inclusive of all taxes</span>
          </div>

          <p class="detail-desc">${product.description}</p>

          <div class="spec-table-title">Full Specifications</div>
          <table class="specs-table">
            <tbody>
              ${specsHtml}
            </tbody>
          </table>

          <div class="pros-cons-grid">
            <div class="pros-box">
              <h5>👍 Key Pros</h5>
              <ul>${prosHtml || '<li>Great build quality</li>'}</ul>
            </div>
            <div class="cons-box">
              <h5>👎 Limitations</h5>
              <ul>${consHtml || '<li>Standard warranty</li>'}</ul>
            </div>
          </div>

          ${similarHtml}
        </div>
      </div>
    `;

    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  },

  closeDetailModal() {
    const modal = document.getElementById('productDetailModal');
    if (modal) modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
  },

  toggleCompare(productId) {
    if (this.comparisonIds.has(productId)) {
      this.comparisonIds.delete(productId);
    } else {
      if (this.comparisonIds.size >= 4) {
        alert('You can compare a maximum of 4 products at a time.');
        return;
      }
      this.comparisonIds.add(productId);
    }
    this.updateCompareUI();

    // Re-render detail modal button if open
    if (this.activeProduct && this.activeProduct.id === productId) {
      this.renderDetailModal(this.activeProduct, []);
    }
  },

  updateCompareUI() {
    const count = this.comparisonIds.size;
    const badge = document.getElementById('compareCountBadge');
    const dock = document.getElementById('comparisonDock');
    const dockCount = document.getElementById('dockCount');
    const dockThumbs = document.getElementById('dockThumbnails');

    if (badge) badge.textContent = count;

    if (count > 0) {
      if (dock) dock.classList.remove('hidden');
      if (dockCount) dockCount.textContent = `${count} / 4`;

      if (dockThumbs) {
        dockThumbs.innerHTML = '';
        this.comparisonIds.forEach(id => {
          const product = window.CatalogApp?.getProductById(id);
          if (product) {
            const img = document.createElement('img');
            img.src = product.image_url;
            img.className = 'dock-thumb';
            img.title = product.title;
            dockThumbs.appendChild(img);
          }
        });
      }
    } else {
      if (dock) dock.classList.add('hidden');
    }

    // Update checkboxes on cards
    document.querySelectorAll('.card-compare-checkbox input').forEach(input => {
      const pid = input.dataset.productId;
      input.checked = this.comparisonIds.has(pid);
    });
  },

  clearComparison() {
    this.comparisonIds.clear();
    this.updateCompareUI();
    this.closeComparisonModal();
  },

  async openComparisonModal() {
    if (this.comparisonIds.size === 0) {
      alert('Please select at least 1 or 2 products to compare.');
      return;
    }

    try {
      const res = await fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_ids: Array.from(this.comparisonIds) })
      });
      const data = await res.json();
      this.renderComparisonMatrix(data.products || []);
    } catch (err) {
      console.error('Error fetching comparison:', err);
    }
  },

  renderComparisonMatrix(products) {
    const modal = document.getElementById('comparisonModal');
    const container = document.getElementById('comparisonModalContent');
    if (!modal || !container) return;

    if (products.length === 0) {
      container.innerHTML = '<p>No products selected for comparison.</p>';
      modal.classList.remove('hidden');
      return;
    }

    // Collect all spec keys
    const specKeySet = new Set();
    products.forEach(p => {
      if (p.specs) {
        Object.keys(p.specs).forEach(k => specKeySet.add(k));
      }
    });
    const specKeys = Array.from(specKeySet);

    let html = `
      <div class="comparison-table-wrapper">
        <table class="comparison-matrix">
          <thead>
            <tr>
              <th style="width: 180px;">Feature</th>
              ${products.map(p => `
                <th>
                  <div class="comparison-product-header">
                    <img src="${p.image_url}" alt="${p.title}" class="comparison-header-img">
                    <span class="detail-brand-badge">${p.brand}</span>
                    <div class="comparison-header-title">${p.title}</div>
                    <div class="comparison-header-price">₹${p.price.toLocaleString()}</div>
                    <button class="btn-text" style="color: var(--danger); font-size: 0.75rem;" onclick="ProductDetails.toggleCompare('${p.id}'); ProductDetails.openComparisonModal();">Remove</button>
                  </div>
                </th>
              `).join('')}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Rating</strong></td>
              ${products.map(p => `<td>⭐ ${p.rating} / 5.0</td>`).join('')}
            </tr>
            <tr>
              <td><strong>Category</strong></td>
              ${products.map(p => `<td>${p.category.toUpperCase()}</td>`).join('')}
            </tr>
            ${specKeys.map(k => `
              <tr>
                <td><strong>${k.replace(/_/g, ' ').toUpperCase()}</strong></td>
                ${products.map(p => `<td>${(p.specs && p.specs[k]) || '—'}</td>`).join('')}
              </tr>
            `).join('')}
            <tr>
              <td><strong>Key Pros</strong></td>
              ${products.map(p => `<td><ul>${(p.pros || []).map(pr => `<li>${pr}</li>`).join('')}</ul></td>`).join('')}
            </tr>
            <tr>
              <td><strong>Limitations</strong></td>
              ${products.map(p => `<td><ul>${(p.cons || []).map(c => `<li>${c}</li>`).join('')}</ul></td>`).join('')}
            </tr>
            <tr>
              <td><strong>Action</strong></td>
              ${products.map(p => `
                <td>
                  <button class="btn-primary-sm" onclick="ProductDetails.closeComparisonModal(); ProductDetails.openProduct('${p.id}');">View Details</button>
                </td>
              `).join('')}
            </tr>
          </tbody>
        </table>
      </div>
    `;

    container.innerHTML = html;
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  },

  closeComparisonModal() {
    const modal = document.getElementById('comparisonModal');
    if (modal) modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
  },

  askAiAbout(productId) {
    this.closeDetailModal();
    const product = window.CatalogApp?.getProductById(productId);
    if (product && window.ChatAssistant) {
      window.ChatAssistant.openChat();
      window.ChatAssistant.sendMessage(`Tell me more about ${product.brand} ${product.model} and whether it is worth buying.`);
    }
  }
};

window.ProductDetails = ProductDetails;
document.addEventListener('DOMContentLoaded', () => ProductDetails.init());
