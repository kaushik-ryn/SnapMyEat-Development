let current_resturant_id = document.getElementById("current_resturant_id").textContent;

// Checkout Button
function updateOrderButton() {
  const orderButtonContainer = document.getElementById("orderButtonContainer");

  if (cartItems.length > 0) {
    orderButtonContainer.style.display = "block";
  } else {
    orderButtonContainer.style.display = "none";
  }
}

// ___________________________________________________
// Filter Button
document.addEventListener("DOMContentLoaded", function () {
  const filterBtn = document.getElementById("filter-btn");
  const dropdown = document.getElementById("filter-dropdown");
  const filterForm = document.querySelector("#filter-dropdown form");
  const priceInput = document.getElementById("max-price");
  const priceDisplay = document.getElementById("price-value");

  // Parse existing URL parameters
  const urlParams = new URLSearchParams(window.location.search);

  // Set default price value if not in URL
  if (!urlParams.has("price")) {
    priceInput.value = "0";
    priceDisplay.textContent = "0";
  } else {
    priceDisplay.textContent = urlParams.get("price");
  }

  // Preserve selected filters on form submission
  filterForm.addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent default form submission

    const formData = new FormData(filterForm);
    const newParams = new URLSearchParams(window.location.search); // Preserve existing filters

    formData.forEach((value, key) => {
      if (value !== "all" && value !== "" && value !== null) {
        newParams.set(key, value); // Update or add the filter
      } else {
        newParams.delete(key); // Remove if "all" or empty
      }
    });
    // If price is 0, remove it from the URL to show all items
    if (formData.get("price") === "0") {
      newParams.delete("price");
    }
    // Redirect with updated query parameters (preserving previous selections)
    window.location.href = `${
      window.location.pathname
    }?${newParams.toString()}`;
  });

  // Restore previous selections on page load
  urlParams.forEach((value, key) => {
    const inputElement = filterForm.querySelector(`[name="${key}"]`);
    if (inputElement) {
      if (inputElement.type === "checkbox" || inputElement.type === "radio") {
        inputElement.checked = true;
      } else {
        inputElement.value = value;
      }
    }
  });

  // Update price display in real-time
  priceInput.addEventListener("input", function () {
    priceDisplay.textContent = priceInput.value;
  });

  // Toggle dropdown visibility
  filterBtn.addEventListener("click", function (event) {
    event.stopPropagation();
    dropdown.style.display =
      dropdown.style.display === "block" ? "none" : "block";
  });

  document.addEventListener("click", function (event) {
    if (!dropdown.contains(event.target) && event.target !== filterBtn) {
      dropdown.style.display = "none";
    }
  });

  // Update price range display
  function updatePriceValue(value) {
    document.getElementById("price-value").textContent = value;
  }
  window.updatePriceValue = updatePriceValue; // Ensure function is globally accessible
});

// ___________________________________________
// Order Summary Prev PopUp
let currentItemId = null;
let currentSizeValue = null;

function showOrderSummaryPopup(itemId) {
  const popup = document.getElementById("prev-popup-id");
  const itemsContainer = document.getElementById("prev-popup-items");

  // Clear previous items
  itemsContainer.innerHTML = "";

  if (cartItems.length === 0) {
    itemsContainer.innerHTML = `<p class="dsspecial">Your cart is empty</p>`;
  } else {
    // Add each item to the popup
    cartItems.forEach((item) => {
      if (item.id === itemId) {
        item.sizes.forEach((size) => {
          if (size.quantity > 0) {
            const itemElement = document.createElement("div");
            itemElement.className = "prev-popup-item";
            itemElement.innerHTML = `
                <div>
                  <span class="prev-item-name">${getItemName(item.id)}</span>
                  <span class="prev-item-size">(${size.size})</span>
                </div>
                <div class="prev-item-controls">
                  <span class="prev-item-quantity">${size.quantity}</span>
                  <button class="prev-control-btn" 
                          onclick="adjustItemQuantity(${item.id}, '${size.size}', -1);">-</button>
                </div>
              `;
            itemsContainer.appendChild(itemElement);
          }
        });
      }
    });
  }

  document.getElementById("blur-bg").style.display = "block";
  popup.style.display = "block";
}

function closeOrderSummaryPopup() {
  document.getElementById("blur-bg").style.display = "none";
  document.getElementById("prev-popup-id").style.display = "none";
}

function adjustItemQuantity(itemId, size, change) {
  itemId = parseInt(itemId, 10); // Ensure itemId is a number
  const newQuantity = getCurrentQuantity(itemId, size) + change;

  if (newQuantity >= 0) {
    updateQuantity(itemId, size, newQuantity,false);
    showOrderSummaryPopup(itemId); // Refresh the popup
    updateCartUI(itemId); // Update the main UI
    updateOrderButton();
  }
}

function getCurrentQuantity(itemId, size) {
  const item = cartItems.find((i) => i.id === itemId);
  if (item) {
    const sizeObj = item.sizes.find((s) => s.size === size);
    return sizeObj ? sizeObj.quantity : 0;
  }
  return 0;
}

function getItemName(itemId) {
  // This should be replaced with actual item name lookup
  // You might need to store item names in your cartItems or fetch from DOM
  const itemElement = document.querySelector(
    `[data-id="${itemId}"] .home-item-name`
  );
  return itemElement ? itemElement.textContent : `Item ${itemId}`;
}

// ________________________________________
// Update Cart UI

function updateCartUI(itemId) {
  
  itemId = Number(itemId); // Ensure itemId is a number
  
  const cartContainer = document.getElementById(`cart-container-${itemId}`);
  if (!cartContainer) return; // Prevent errors if element is missing
  
  // Use the global cartItems instead of loading from localStorage again
  let item = cartItems.find((i) => i.id === itemId);
  if (!item) {    
    console.log("not item");
    
    // If item is not in the cart, show "Add to Cart" button
    cartContainer.innerHTML = `<button onclick="showPopup(${itemId});" class="add-to-cart">Add to Cart</button>`;
    return;
  }
  
  if (item.oneSize) {
    quantity = item.sizes[0].quantity;
    value = item.sizes[0].size;
    console.log(item.oneSize);
    
    if (quantity>0) {
      cartContainer.innerHTML = `
                <div class="quantity-control">
                  <button onclick="decreaseQuantity(Number(${itemId}),'${value}',true); event.stopPropagation()" class="minus">-</button>
                  <span>${quantity}</span>
                  <button onclick="increaseQuantity(Number(${itemId}),'${value}',true); event.stopPropagation();" class="plus">+</button>
                </div> 
            `;  
    }else{
      cartContainer.innerHTML = `
              <button onclick="increaseQuantity(Number(${itemId}), '${value}',true);" class="add-to-cart">Add to Cart</button>
          `;
    }
  }
  else{
    // Calculate total quantity from the global cartItems
    let totalQuantity = item.sizes.reduce((sum, size) => sum + size.quantity, 0);
    

    if (totalQuantity > 0) {
      cartContainer.innerHTML = `
              <div class="quantity-control">
                <button onclick="showOrderSummaryPopup(${itemId}); event.stopPropagation()" class="minus">-</button>
                <span>${totalQuantity}</span>
                <button onclick="showPopup(${itemId}); event.stopPropagation();" class="plus">+</button>
              </div> 
          `;
    } else {
      cartContainer.innerHTML = `
              <button onclick="showPopup(${itemId});" class="add-to-cart">Add to Cart</button>
          `;
    }
  }
}

// ________________________________________________
// Function to load cart from localStorage
// const cartString = localStorage.getItem(`CartInfo_${current_resturant_id}`);
// if (cartString === null) {
//   globalThis.cartItems = [];
// } else {
//   let cart = JSON.parse(cartString);
//   globalThis.cartItems = cart.dishItems;
// }

const cartString = localStorage.getItem(`CartInfo_${current_resturant_id}`);
const expiryLimit = 2 * 60 * 60 * 1000; // 2 hours in milliseconds
if (cartString === null) {
  globalThis.cartItems = [];
} else {
  try {
    let cart = JSON.parse(cartString);
    const currentTime = new Date().getTime();
    if(!cart.expiry || currentTime >= (cart.expiry+expiryLimit) ){
      localStorage.clear()
      globalThis.cartItems = [];
    }else{
      globalThis.cartItems = cart.dishItems || [];
    }
  } catch (error) {
    console.error("Corrupt cart data, clearing:", error);
    localStorage.clear();
    globalThis.cartItems = [];
  }
}

if (cartItems.length !== 0) {
  updateOrderButton();  
  cartItems.forEach((item) => updateCartUI(item.id));  
}

// Function to save cart to localStorage with 10-minute expiry
function saveCart() {
  const expiryTime = new Date().getTime() + 10 * 60 * 1000;
  cart = {
    dishItems: cartItems,
    expiry: expiryTime,
  };
  localStorage.setItem(`CartInfo_${current_resturant_id}`, JSON.stringify(cart));
}

// Function to update item quantity
function updateQuantity(itemId, size, newQuantity,oneSize) {
  let itemFound = false;
  // Find the item
  for (let item of cartItems) {
    if (item.id === itemId) {
      let sizeObj = item.sizes.find((s) => s.size === size);

      if (sizeObj) {
        if (newQuantity === 0) {
          // Remove the size entry if quantity is 0
          item.sizes = item.sizes.filter((s) => s.size !== size);
        } else {
          // Update quantity
          sizeObj.quantity = newQuantity;
        }
        // If no sizes left, remove the item
        if (item.sizes.length === 0) {
          cartItems = cartItems.filter((i) => i.id !== itemId);
        }

        itemFound = true;
      } else if (newQuantity > 0) {
        // Add new size if it doesn't exist
        item.sizes.push({ size: size, quantity: newQuantity });
        itemFound = true;
      }
      break;
    }
  }

  // If item doesn't exist, add it
  if (!itemFound && newQuantity > 0) {
    cartItems.push({
      id: itemId,
      sizes: [{ size: value, quantity: newQuantity }],
      oneSize: oneSize ? true : false
    });    
  }

  // Update cart and save
  saveCart();

}


function increaseQuantity(itemId, value,oneSize) {
  let item = cartItems.find((i) => i.id === itemId);

  if (item) {
    // Item exists in cart
    if (!item.sizes) {
      // Initialize sizes array if it doesn't exist
      item.sizes = [];
    }

    let sizeObj = item.sizes.find((s) => s.size === value);

    if (sizeObj) {
      // Size exists - increment quantity
      sizeObj.quantity++;
      newQuantity = sizeObj.quantity;
    } else {
      // Size doesn't exist - add new size with quantity 1
      item.sizes.push({ size: value, quantity: 1 });
      newQuantity = 1;
    }
    updateQuantity(itemId, value, newQuantity, oneSize);
  } else {
    // Item doesn't exist in cart - create new item
    newQuantity = 1;
    cartItems.push({
      id: itemId,
      sizes: [{ size: value, quantity: newQuantity }],
      oneSize: oneSize ? true : false
    });
    updateQuantity(itemId, value, newQuantity, oneSize);
  }

  updateCartUI(itemId);
  updateOrderButton();
}

function decreaseQuantity(itemId, value,oneSize) {
  itemId = parseInt(itemId, 10); // Ensure itemId is a number

  let item = cartItems.find((i) => i.id === itemId);
  if (!item) return; // Item not found
  
  let last_value = item.sizes[0].size;
  let sizeIndex = item.sizes.findIndex((s) => s.size === value);
  if (sizeIndex === -1) return; // Size not found

  let sizeObj = item.sizes[sizeIndex];
  sizeObj.quantity--;

  if (sizeObj.quantity > 0) {
    // Update quantity if it's still above 0
    updateQuantity(itemId, value, sizeObj.quantity, oneSize);
  } else {
    // Remove size entry if quantity is 0
    item.sizes.splice(sizeIndex, 1);

    // If no sizes remain, remove the entire item
    if (item.sizes.length === 0) {
      
      cartItems = cartItems.filter((i) => i.id !== itemId);
    }
    
    updateQuantity(itemId, value, 0, oneSize); // Notify backend of removal
  }
  let search = cartItems.find((i) => i.id === itemId);
  if (!search && item.oneSize) {
    console.log(item.oneSize);
    const cartContainer = document.getElementById(`cart-container-${itemId}`);
    cartContainer.innerHTML = `
              <button onclick="increaseQuantity(Number(${itemId}), '${last_value}',true);" class="add-to-cart">Add to Cart</button>
          `;
  }else{
    updateCartUI(itemId);
  }
  updateOrderButton();
}

// Expansion
function expandion_box(element) {
  element.classList.toggle("expand-box");
}

//   _________________________________________
// Modifier
// Add click event to all .ds-content elements
const dsContents = document.querySelectorAll(".ds-content");
dsContents.forEach((dsContent) => {
  dsContent.addEventListener("click", function () {
    const radioInput = this.querySelector('input[type="radio"]');
    if (radioInput) {
      radioInput.checked = true;
    }
  });
});

// Show and close popup functions
function showPopup(itemId) {
  document.getElementById(`overlay-${itemId}`).style.display = "block";
  document.getElementById(`sizePopup-${itemId}`).style.display = "block";
}

function closePopup(itemId, mssge) {
  const selectSize = document.querySelector(`input[name= size_${itemId}]:checked`);
  document.getElementById(`overlay-${itemId}`).style.display = "none";
  document.getElementById(`sizePopup-${itemId}`).style.display = "none";
  if (mssge === "apply" && selectSize) {
    console.log(selectSize.value);
    increaseQuantity(Number(itemId), selectSize.value,false);
  }
}
