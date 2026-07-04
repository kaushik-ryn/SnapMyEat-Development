let current_resturant_id = document.getElementById("current_resturant_id").textContent;

function renderCart() {
  let cartHTML = "";
  cartItems.forEach((item) => {
    item.sizes.forEach((sizeData) => {
      cartHTML += `
        <div class="pdr-bg-color">
          <div class="product-summary">
            <div class="summary">
              <div class="summary-item"><b>${item.name}</b></div>
              <div style="display: flex; justify-content: space-between; align-items: center; gap:50px;">
              <div style="width:20%;">${sizeData.size}</div>
              <div id="item-${item.id}-${sizeData.size}" class="greenColor">₹<b>${sizeData.price}</b></div>
              </div>
              <br />
            </div>
            <div class="quantity-controls">
              <button class="quantity-btn decrease-btn" onclick="decreaseQuantity('${item.id}', '${sizeData.size}')";>-</button>
              <span class="quantity-display" id="quantity-${item.id}-${sizeData.size}">${sizeData.quantity}</span>
              <button class="quantity-btn increase-btn" onclick="increaseQuantity('${item.id}', '${sizeData.size}')">+</button>
            </div>
          </div>
        </div>`;
    });
  });

  document.getElementById("cartSummary").innerHTML = cartHTML;
}

globalThis.cartData = JSON.parse(localStorage.getItem(`CartInfo_${current_resturant_id}`));
// globalThis.cartItems = [];

if (cartData && cartData.dishItems && cartData.dishItems.length > 0) {
  fetchingPrice();
}

function saveCart() {
  localStorage.setItem(
    `CartInfo_${current_resturant_id}`,
    JSON.stringify({
      dishItems: cartItems,
      expiry: new Date().getTime() + 10 * 60 * 1000,
    })
  );
}

function updatePayAtCounterButton() {
    let container = document.getElementById("payAtCounterContainer");
    
    if (!cartItems || cartItems.length == 0) {
    document.getElementById(
      "cartSummary"
    ).innerHTML = `<p align="center">Your cart is empty.</p>`;
    container.classList.add("disabled-container");
  }else {
    container.classList.remove("disabled-container");
  }
}

function increaseQuantity(itemId, size) {
  let quantityDisplay = document.getElementById(`quantity-${itemId}-${size}`);
  let newQuantity = parseInt(quantityDisplay.textContent) + 1;
  quantityDisplay.textContent = newQuantity;
  updateQuantity(Number(itemId), size, newQuantity);
  requestAnimationFrame(recalculateTotal);
}

function decreaseQuantity(itemId, size) {
  let quantityDisplay = document.getElementById(`quantity-${itemId}-${size}`);
  let newQuantity = parseInt(quantityDisplay.textContent) - 1;
  
  if (newQuantity < 1) {
    quantityDisplay.parentElement.parentElement.parentElement.remove(); // Remove the item from the DOM
    removeItemFromCart(Number(itemId), size);
  } else {
    quantityDisplay.textContent = newQuantity;
    updateQuantity(Number(itemId), size, newQuantity);
  }
  
  requestAnimationFrame(recalculateTotal);
  
  updatePayAtCounterButton();
}

function updateQuantity(itemId, size, newQuantity) {
  let item = cartItems.find((item) => item.id === itemId);
  if (item) {
    let sizeObj = item.sizes.find((s) => s.size === size);
    if (sizeObj) {
      sizeObj.quantity = newQuantity;
      saveCart();
    }
  }
}


function removeItemFromCart(itemId, size) {
    
  let itemIndex = cartItems.findIndex((item) => item.id === itemId);
  
  if (itemIndex !== -1) {
    let item = cartItems[itemIndex];
    console.log(item);
    console.log(item.sizes);
    
    // Remove size entry from the sizes list
    item.sizes = item.sizes.filter((s) => s.size !== size);
    console.log(item);

    // If no sizes remain, remove the entire item
    if (item.sizes.length === 0) {
      cartItems.splice(itemIndex, 1);
    }
    saveCart();
  }
}

function recalculateTotal() {
  let total = 0;

  cartItems.forEach((item) => {
    item.sizes.forEach((sizeObj) => {
      let { size, quantity, price } = sizeObj;

      let quantityElem = document.getElementById(`quantity-${item.id}-${size}`);
      let priceElem = document.getElementById(`item-${item.id}-${size}`);

      if (quantityElem && priceElem) {
        let updatedQuantity = parseInt(quantityElem.textContent);
        let itemPrice = parseFloat(
          priceElem.textContent.replace("₹", "").trim()
        );
        total += updatedQuantity * itemPrice;
      }
    });
  });

  // Update total amount in UI
  let totalElem = document.querySelector(".total-item b");
  if (totalElem) {
    totalElem.textContent = `₹${total.toFixed(2)}`;
  }
}


// _________________________________
function isEmpty() {
    
  if (!cartData || !cartData.dishItems || cartData.dishItems.length == 0) {

    let btnContainer = document.getElementById("payAtCounterContainer");
    btnContainer.classList.add("disabled-container");

    document.getElementById(
      "cartSummary"
    ).innerHTML = `<p align="center">Your cart is empty.</p>`;
  }
}

isEmpty();
