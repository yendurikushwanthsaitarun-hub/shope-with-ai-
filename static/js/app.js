/**
 * Main Store Catalog & Filtering Module
 * Pure Vanilla JavaScript
 */

// Global Toast Notification Helper
window.showToast = function(message, type = 'info', duration = 3200) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast-message toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
};

const CatalogApp = {
  allProducts: [],
  filteredProducts: [],
  currentDepartment: '',
  currentCategory: '',
  currentBrand: '',
  maxPrice: 250000,
  sortBy: 'popular',
  searchDebounceTimer: null,
  activeUseCase: '',

  async init() {
    this.setupEventListeners();
    await this.fetchProducts();
    await this.fetchBrands();
  },

  setupEventListeners() {
    // Brand home logo
    const brandHome = document.getElementById('brandHomeBtn');
    if (brandHome) {
      brandHome.addEventListener('click', () => {
        this.resetFilters();
      });
    }

    // Department tabs
    document.querySelectorAll('.dept-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.dept-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentDepartment = tab.dataset.department || '';
        this.filterCategoryPillsByDept();
        this.fetchBrands(this.currentCategory);
        this.applyFilters();
      });
    });

    // Main search input
    const searchInput = document.getElementById('mainSearchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';

        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => {
          this.applyFilters();
        }, 250);
      });

      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const q = searchInput.value.trim();
          if (q) {
            // Trigger AI assistant if user pressed enter or filter directly
            this.applyFilters();
          }
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (searchInput) {
          searchInput.value = '';
          clearBtn.style.display = 'none';
          this.applyFilters();
        }
      });
    }

    // Category pills
    const catButtons = document.querySelectorAll('.cat-pill');
    catButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        catButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentCategory = btn.dataset.category || '';
        this.fetchBrands(this.currentCategory);
        this.applyFilters();
      });
    });

    // Price range slider
    const priceSlider = document.getElementById('priceRangeInput');
    const priceDisplay = document.getElementById('priceDisplay');
    if (priceSlider) {
      priceSlider.addEventListener('input', (e) => {
        this.maxPrice = Number(e.target.value);
        if (priceDisplay) {
          priceDisplay.textContent = `₹${this.maxPrice.toLocaleString()}`;
        }
        this.applyFilters();
      });
    }

    // Sort selector
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.sortBy = e.target.value;
        this.sortAndRender();
      });
    }

    // Reset filters button
    const resetBtn = document.getElementById('resetFiltersBtn');
    const emptyClearBtn = document.getElementById('emptyClearBtn');
    if (resetBtn) resetBtn.addEventListener('click', () => this.resetFilters());
    if (emptyClearBtn) emptyClearBtn.addEventListener('click', () => this.resetFilters());

    // Brand search in sidebar
    const brandSearch = document.getElementById('brandSearchInput');
    if (brandSearch) {
      brandSearch.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        document.querySelectorAll('.brand-item').forEach(item => {
          const brandText = item.textContent.toLowerCase();
          item.style.display = brandText.includes(query) ? 'flex' : 'none';
        });
      });
    }

    // Use-case tag chips
    document.querySelectorAll('.tag-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const uc = chip.dataset.usecase;
        if (this.activeUseCase === uc) {
          this.activeUseCase = '';
          chip.classList.remove('active');
        } else {
          document.querySelectorAll('.tag-chip').forEach(c => c.classList.remove('active'));
          chip.classList.add('active');
          this.activeUseCase = uc;
        }
        this.applyFilters();
      });
    });

    // Mobile filter toggle
    const mobileFilterBtn = document.getElementById('mobileFilterToggle');
    const sidebar = document.getElementById('filterSidebar');
    if (mobileFilterBtn && sidebar) {
      mobileFilterBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
  },

  async fetchProducts() {
    try {
      const res = await fetch('/api/products');
      const data = await res.json();
      this.allProducts = data.products || [];
      this.filteredProducts = [...this.allProducts];
      this.applyFilters();
    } catch (err) {
      console.error('Failed to load products:', err);
    }
  },

  async fetchBrands(category = '') {
    try {
      let url = '/api/brands?';
      if (category) url += `category=${encodeURIComponent(category)}&`;
      if (this.currentDepartment) url += `department=${encodeURIComponent(this.currentDepartment)}&`;
      const res = await fetch(url);
      const data = await res.json();
      this.renderBrandCheckboxes(data.brands || []);
    } catch (err) {
      console.error('Failed to load brands:', err);
    }
  },

  filterCategoryPillsByDept() {
    const electronicsCategories = new Set(['smartphone', 'laptop', 'tablet', 'headphone', 'earbuds', 'smartwatch', 'camera', 'tv', 'monitor', 'gaming', 'accessories', 'storage']);
    const fashionCategories = new Set(['footwear', 'apparel', 'smart_rings', 'eyewear', 'watches', 'bags']);

    document.querySelectorAll('.cat-pill').forEach(btn => {
      const cat = btn.dataset.category;
      if (!cat) {
        btn.style.display = 'block';
        return;
      }
      if (!this.currentDepartment) {
        btn.style.display = 'block';
      } else if (this.currentDepartment === 'electronics') {
        btn.style.display = electronicsCategories.has(cat) ? 'block' : 'none';
      } else if (this.currentDepartment === 'fashion') {
        btn.style.display = fashionCategories.has(cat) ? 'block' : 'none';
      }
    });

    if (this.currentDepartment === 'electronics' && fashionCategories.has(this.currentCategory)) {
      this.currentCategory = '';
      document.querySelectorAll('.cat-pill').forEach(b => b.classList.toggle('active', !b.dataset.category));
    } else if (this.currentDepartment === 'fashion' && electronicsCategories.has(this.currentCategory)) {
      this.currentCategory = '';
      document.querySelectorAll('.cat-pill').forEach(b => b.classList.toggle('active', !b.dataset.category));
    }
  },

  renderBrandCheckboxes(brands) {
    const container = document.getElementById('brandCheckboxList');
    if (!container) return;

    container.innerHTML = brands.map(brand => `
      <label class="brand-item">
        <input type="checkbox" value="${brand}" ${this.currentBrand === brand ? 'checked' : ''} onchange="CatalogApp.onBrandSelect(this)">
        <span>${brand}</span>
      </label>
    `).join('');
  },

  onBrandSelect(checkbox) {
    if (checkbox.checked) {
      // Uncheck other brands for single brand focus or toggle
      document.querySelectorAll('#brandCheckboxList input').forEach(cb => {
        if (cb !== checkbox) cb.checked = false;
      });
      this.currentBrand = checkbox.value;
    } else {
      this.currentBrand = '';
    }
    this.applyFilters();
  },

  setCategory(category) {
    this.currentCategory = category;
    document.querySelectorAll('.cat-pill').forEach(b => {
      b.classList.toggle('active', (b.dataset.category || '') === category);
    });
    this.fetchBrands(category);
    this.applyFilters();
  },

  applyFilters() {
    const searchVal = (document.getElementById('mainSearchInput')?.value || '').toLowerCase().trim();

    let list = [...this.allProducts];

    // Department filter
    if (this.currentDepartment) {
      list = list.filter(p => (p.department || 'electronics').toLowerCase() === this.currentDepartment.toLowerCase());
    }

    // Category filter
    if (this.currentCategory) {
      list = list.filter(p => p.category.toLowerCase().replace(/s$/, '') === this.currentCategory.toLowerCase().replace(/s$/, ''));
    }

    // Brand filter
    if (this.currentBrand) {
      list = list.filter(p => p.brand.toLowerCase() === this.currentBrand.toLowerCase());
    }

    // Price filter
    list = list.filter(p => p.price <= this.maxPrice);

    // Use case filter
    if (this.activeUseCase) {
      list = list.filter(p => (p.use_cases || []).some(uc => uc.toLowerCase().includes(this.activeUseCase)));
    }

    // Search query filter
    if (searchVal) {
      const terms = searchVal.split(' ').filter(t => t.length > 0);
      list = list.filter(p => {
        const searchable = `${p.title} ${p.brand} ${p.model} ${p.category} ${p.description} ${(p.features || []).join(' ')}`.toLowerCase();
        return terms.every(t => searchable.includes(t));
      });
    }

    this.filteredProducts = list;
    this.sortAndRender();
    this.renderActiveFilterChips();
  },

  sortAndRender() {
    const list = [...this.filteredProducts];

    if (this.sortBy === 'price_asc') {
      list.sort((a, b) => a.price - b.price);
    } else if (this.sortBy === 'price_desc') {
      list.sort((a, b) => b.price - a.price);
    } else if (this.sortBy === 'rating') {
      list.sort((a, b) => b.rating - a.rating);
    }

    this.renderProducts(list);
  },

  renderProducts(products) {
    const grid = document.getElementById('productsGrid');
    const empty = document.getElementById('emptyCatalogState');
    const count = document.getElementById('resultsCount');
    const title = document.getElementById('catalogTitle');

    if (count) {
      const deptLabel = this.currentDepartment === 'fashion' ? 'fashion & lifestyle items' : (this.currentDepartment === 'electronics' ? 'electronics' : 'products');
      count.textContent = `Showing ${products.length} ${deptLabel}`;
    }
    if (title) {
      if (this.currentCategory) {
        title.textContent = `${this.currentCategory.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
      } else if (this.currentDepartment === 'fashion') {
        title.textContent = 'Fashion, Techwear & Lifestyle';
      } else if (this.currentDepartment === 'electronics') {
        title.textContent = 'Electronics & Smart Devices';
      } else {
        title.textContent = 'All Products & Electronics';
      }
    }

    if (!grid) return;

    if (products.length === 0) {
      grid.innerHTML = '';
      if (empty) empty.classList.remove('hidden');
      return;
    }

    if (empty) empty.classList.add('hidden');

    grid.innerHTML = products.map(product => {
      const inCompare = window.ProductDetails?.comparisonIds.has(product.id);
      const specs = product.specs || {};
      const keySpecs = Object.entries(specs).slice(0, 3).map(([_, val]) => `<span class="spec-chip">${val}</span>`).join('');

      return `
        <div class="product-card" id="card-${product.id}">
          <div class="card-image-wrap">
            <img class="card-image" src="${product.image_url}" alt="${product.title}" loading="lazy">
            <span class="card-category-badge">${product.category}</span>
            <label class="card-compare-checkbox">
              <input type="checkbox" data-product-id="${product.id}" ${inCompare ? 'checked' : ''} onchange="ProductDetails.toggleCompare('${product.id}')">
              <span>Compare</span>
            </label>
          </div>

          <div class="card-body">
            <div class="card-brand">${product.brand}</div>
            <h3 class="card-title" title="${product.title}">${product.title}</h3>

            <div class="card-rating-row">
              <span class="stars">★★★★☆</span>
              <span class="rating-num">${product.rating}</span>
            </div>

            <div class="card-specs-chips">
              ${keySpecs}
            </div>

            <div class="card-footer">
              <div class="card-price-wrap">
                <span class="card-price-label">Price</span>
                <span class="card-price">₹${product.price.toLocaleString()}</span>
              </div>
              <div class="card-actions">
                <button class="btn-details" onclick="ProductDetails.openProduct('${product.id}')">Details</button>
                <button class="btn-ask-item" title="Ask AI about this item" onclick="ProductDetails.askAiAbout('${product.id}')">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                  Ask
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  displayProducts(products, contextLabel) {
    const title = document.getElementById('catalogTitle');
    if (title && contextLabel) title.textContent = contextLabel;
    this.filteredProducts = products;
    this.sortAndRender();
  },

  renderActiveFilterChips() {
    const container = document.getElementById('activeFilterChips');
    if (!container) return;

    let chips = '';
    if (this.currentCategory) {
      chips += `<div class="active-filter-tag">${this.currentCategory} <span onclick="CatalogApp.setCategory('')">&times;</span></div>`;
    }
    if (this.currentBrand) {
      chips += `<div class="active-filter-tag">${this.currentBrand} <span onclick="CatalogApp.clearBrand()">&times;</span></div>`;
    }
    if (this.maxPrice < 250000) {
      chips += `<div class="active-filter-tag">&le; ₹${this.maxPrice.toLocaleString()} <span onclick="CatalogApp.resetPrice()">&times;</span></div>`;
    }
    if (this.activeUseCase) {
      chips += `<div class="active-filter-tag">${this.activeUseCase} <span onclick="CatalogApp.clearUseCase()">&times;</span></div>`;
    }

    container.innerHTML = chips;
  },

  clearBrand() {
    this.currentBrand = '';
    document.querySelectorAll('#brandCheckboxList input').forEach(cb => cb.checked = false);
    this.applyFilters();
  },

  resetPrice() {
    this.maxPrice = 250000;
    const priceSlider = document.getElementById('priceRangeInput');
    const priceDisplay = document.getElementById('priceDisplay');
    if (priceSlider) priceSlider.value = '250000';
    if (priceDisplay) priceDisplay.textContent = '₹2,50,000';
    this.applyFilters();
  },

  clearUseCase() {
    this.activeUseCase = '';
    document.querySelectorAll('.tag-chip').forEach(c => c.classList.remove('active'));
    this.applyFilters();
  },

  resetFilters() {
    this.currentDepartment = '';
    this.currentCategory = '';
    this.currentBrand = '';
    this.maxPrice = 250000;
    this.activeUseCase = '';
    this.sortBy = 'popular';

    const searchInput = document.getElementById('mainSearchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    if (searchInput) searchInput.value = '';
    if (clearBtn) clearBtn.style.display = 'none';

    document.querySelectorAll('.dept-tab').forEach(t => {
      t.classList.toggle('active', !t.dataset.department);
    });

    this.filterCategoryPillsByDept();

    document.querySelectorAll('.cat-pill').forEach(b => {
      b.classList.toggle('active', !b.dataset.category);
    });

    document.querySelectorAll('#brandCheckboxList input').forEach(cb => cb.checked = false);
    document.querySelectorAll('.tag-chip').forEach(c => c.classList.remove('active'));

    const priceSlider = document.getElementById('priceRangeInput');
    const priceDisplay = document.getElementById('priceDisplay');
    if (priceSlider) priceSlider.value = '250000';
    if (priceDisplay) priceDisplay.textContent = '₹2,50,000';

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) sortSelect.value = 'popular';

    this.fetchBrands('');
    this.applyFilters();
  },

  getProductById(id) {
    return this.allProducts.find(p => p.id === id);
  }
};

window.CatalogApp = CatalogApp;
document.addEventListener('DOMContentLoaded', () => CatalogApp.init());
