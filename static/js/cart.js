// Key để lưu trong LocalStorage 
const CART_KEY = "MY_APP_CART";

// --- PHẦN 1: QUẢN LÝ DỮ LIỆU GIỎ HÀNG ---

// Hàm lấy giỏ hàng từ LocalStorage
function getCart() {
    const stored = localStorage.getItem(CART_KEY);
    return stored ? JSON.parse(stored) : [];
}

// Hàm lưu giỏ hàng
function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartBadge(); // Cập nhật số lượng trên menu
}

// Hàm thêm vào giỏ (Đã nâng cấp thông báo)
function addToCart(product) {
    let cart = getCart();
    
    // Kiểm tra sản phẩm đã có chưa
    const existingItem = cart.find(item => item.product.id === product.id);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({ product: product, quantity: 1 });
    }
    
    saveCart(cart);
    
    // Thay alert bằng Toast đẹp hơn
    showToast(`Đã thêm "${product.title}" vào giỏ hàng!`, 'success');
}

// Hàm cập nhật số lượng badge trên menu
function updateCartBadge() {
    const cart = getCart();
    const totalQty = cart.reduce((sum, item) => sum + item.quantity, 0);
    
    const badge = document.getElementById('cart-badge');
    if (badge) {
        badge.innerText = totalQty;
        badge.style.display = totalQty > 0 ? 'inline-block' : 'none';
    }
}

// Hàm format tiền tệ
function formatCurrency(amount) {
    return "$" + parseFloat(amount).toFixed(2);
}

// --- PHẦN 2: LOGIC HIỂN THỊ TRANG CART.HTML ---

function renderCartPage() {
    const cart = getCart();
    const container = document.getElementById('cart-container');
    const emptyMsg = document.getElementById('cart-empty');
    const cartTable = document.getElementById('cart-table');
    const totalPriceEl = document.getElementById('total-price');

    if (!container) return; // Không phải trang cart thì thoát

    if (cart.length === 0) {
        emptyMsg.style.display = 'block';
        cartTable.style.display = 'none';
        return;
    }

    emptyMsg.style.display = 'none';
    cartTable.style.display = 'block';

    // Render danh sách
    const tbody = document.getElementById('cart-body');
    tbody.innerHTML = '';
    
    let total = 0;

    cart.forEach(item => {
        const p = item.product;
        const lineTotal = p.price * item.quantity;
        total += lineTotal;

        const row = `
            <tr>
                <td style="padding: 10px; display: flex; align-items: center; gap: 10px;">
                    <img src="${p.image || '/static/images/khongcoanh.png'}" width="50" height="50" style="object-fit: contain;">
                    <span>${p.title}</span>
                </td>
                <td>${formatCurrency(p.price)}</td>
                <td>
                    <button onclick="changeQty(${p.id}, -1)" class="btn-qty">-</button>
                    <span style="margin: 0 10px;">${item.quantity}</span>
                    <button onclick="changeQty(${p.id}, 1)" class="btn-qty">+</button>
                </td>
                <td style="color: #d32f2f; font-weight: bold;">${formatCurrency(lineTotal)}</td>
                <td>
                    <button onclick="removeItem(${p.id})" class="btn-remove">🗑 Xóa</button>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });

    if (totalPriceEl) totalPriceEl.innerText = formatCurrency(total);
}

// Hàm tăng giảm số lượng
function changeQty(productId, delta) {
    let cart = getCart();
    const item = cart.find(i => i.product.id === productId);
    
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            cart = cart.filter(i => i.product.id !== productId);
        }
    }
    
    saveCart(cart);
    renderCartPage(); 
}

// Hàm xóa sản phẩm
function removeItem(productId) {
    if(!confirm("Bạn có chắc muốn xóa sản phẩm này?")) return;
    let cart = getCart();
    cart = cart.filter(i => i.product.id !== productId);
    saveCart(cart);
    renderCartPage();
    showToast("Đã xóa sản phẩm khỏi giỏ", "error");
}

// --- PHẦN 3: TOAST NOTIFICATION (THÔNG BÁO ĐẸP) ---

function showToast(message, type = 'success') {
    // 1. Tạo container chứa toast nếu chưa có
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 99999;
            display: flex; flex-direction: column; gap: 10px;
        `;
        document.body.appendChild(container);
    }

    // 2. Tạo phần tử thông báo
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#4caf50' : '#f44336'; // Xanh hoặc Đỏ
    const icon = type === 'success' ? '✔' : '✖';

    toast.style.cssText = `
        min-width: 250px; background: #fff; color: #333;
        padding: 12px 20px; border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-left: 5px solid ${bgColor};
        display: flex; align-items: center; gap: 10px;
        opacity: 0; transform: translateX(50px);
        transition: all 0.3s ease-in-out; font-family: sans-serif; font-size: 14px;
    `;
    
    toast.innerHTML = `<span style="color: ${bgColor}; font-weight: bold; font-size: 18px;">${icon}</span> <span>${message}</span>`;

    // 3. Thêm vào màn hình
    container.appendChild(toast);

    // 4. Hiệu ứng hiện ra
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);

    // 5. Tự động ẩn sau 3 giây
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        // Xóa khỏi DOM sau khi ẩn
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Khởi chạy khi load trang
document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();
    renderCartPage();
});